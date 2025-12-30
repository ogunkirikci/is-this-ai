from __future__ import annotations
from dataclasses import dataclass
from PIL import Image
import numpy as np
from .base import DetectionResult

@dataclass
class HeuristicDetector:
    name: str = "heuristic-v0"

    def _check_watermark(self, img: Image.Image) -> tuple[bool, str]:
        """Check for common AI watermark patterns."""
        # Convert to grayscale for watermark detection
        gray = img.convert("L")
        arr = np.asarray(gray, dtype=np.uint8)
        h, w = arr.shape
        
        # Check corners and edges for watermark patterns
        # AI watermarks often appear in corners or along edges
        corner_size = min(100, w // 10, h // 10)
        
        # Check bottom-right corner (common for Gemini, Midjourney)
        br_corner = arr[-corner_size:, -corner_size:]
        br_mean = float(np.mean(br_corner))
        br_std = float(np.std(br_corner))
        
        # Watermarks often have low variance (uniform text/logo)
        # and appear as darker or lighter regions
        if br_std < 15 and (br_mean < 50 or br_mean > 200):
            return True, "watermark tespiti (köşe bölgesi)"
        
        # Check for horizontal watermark band at bottom
        bottom_band = arr[-corner_size//2:, :]
        bottom_std = float(np.std(bottom_band))
        if bottom_std < 20:
            return True, "watermark tespiti (alt bant)"
        
        return False, ""
    
    def _texture_uniformity(self, gray: np.ndarray) -> float:
        """Measure texture uniformity - AI images often have more uniform textures."""
        # Divide image into blocks and measure variance
        h, w = gray.shape
        block_size = 32
        blocks_h = h // block_size
        blocks_w = w // block_size
        
        if blocks_h < 2 or blocks_w < 2:
            return 0.5
        
        variances = []
        for i in range(blocks_h):
            for j in range(blocks_w):
                block = gray[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size]
                variances.append(float(np.var(block)))
        
        # Low variance across blocks indicates uniform texture (AI-like)
        if not variances:
            return 0.5
        
        mean_var = float(np.mean(variances))
        std_var = float(np.std(variances))
        
        # Normalize to 0-1 range (lower = more uniform = more AI-like)
        uniformity = 1.0 - min(1.0, mean_var / 0.01)
        return uniformity

    def _image_features(self, img: Image.Image) -> dict:
        # normalize
        img = img.convert("RGB")
        arr = np.asarray(img).astype(np.float32) / 255.0

        # simple signals:
        # - over-smoothness (low high-frequency energy)
        # - extreme saturation patterns
        # - edge density
        gray = np.dot(arr[..., :3], [0.299, 0.587, 0.114])

        # high-frequency energy via Laplacian-ish kernel
        k = np.array([[0, 1, 0],
                      [1,-4, 1],
                      [0, 1, 0]], dtype=np.float32)
        # naive conv (no scipy): pad + sliding
        pad = np.pad(gray, 1, mode="edge")
        lap = (
            k[0,0]*pad[:-2,:-2] + k[0,1]*pad[:-2,1:-1] + k[0,2]*pad[:-2,2:] +
            k[1,0]*pad[1:-1,:-2] + k[1,1]*pad[1:-1,1:-1] + k[1,2]*pad[1:-1,2:] +
            k[2,0]*pad[2:,:-2] + k[2,1]*pad[2:,1:-1] + k[2,2]*pad[2:,2:]
        )
        hf_energy = float(np.mean(np.abs(lap)))

        # saturation estimate in HSV-ish way
        mx = arr.max(axis=2)
        mn = arr.min(axis=2)
        sat = np.where(mx == 0, 0, (mx - mn) / (mx + 1e-6))
        sat_mean = float(np.mean(sat))
        sat_p95 = float(np.quantile(sat, 0.95))

        # edge density (threshold on lap magnitude)
        edges = np.abs(lap) > np.quantile(np.abs(lap), 0.90)
        edge_density = float(np.mean(edges))
        
        # Texture uniformity
        gray_uint8 = (gray * 255).astype(np.uint8)
        texture_uniformity = self._texture_uniformity(gray_uint8)
        
        # Watermark check
        has_watermark, watermark_reason = self._check_watermark(img)

        return {
            "hf_energy": hf_energy,
            "sat_mean": sat_mean,
            "sat_p95": sat_p95,
            "edge_density": edge_density,
            "texture_uniformity": texture_uniformity,
            "has_watermark": has_watermark,
            "watermark_reason": watermark_reason,
        }

    def detect_image(self, image_path: str) -> DetectionResult:
        img = Image.open(image_path)
        feats = self._image_features(img)

        # Improved heuristic scoring with better thresholds
        hf = feats["hf_energy"]
        satm = feats["sat_mean"]
        ed = feats["edge_density"]
        texture_uni = feats["texture_uniformity"]
        has_wm = feats["has_watermark"]
        wm_reason = feats["watermark_reason"]

        score = 0.0
        reasons: list[str] = []

        # Watermark is a strong signal
        if has_wm:
            score += 0.50
            reasons.append(wm_reason)

        # Very low hf_energy (more strict threshold)
        # AI images tend to be smoother, but so are low-light photos
        # So we need combination with other signals
        if hf < 0.02:
            score += 0.30
            reasons.append("çok düşük yüksek-frekans detayı (aşırı pürüzsüz)")
        elif hf < 0.025:
            # Medium smoothness - only count if combined with other signals
            if texture_uni > 0.4 or has_wm:
                score += 0.15
                reasons.append("düşük yüksek-frekans detayı")

        # High texture uniformity (AI images often have uniform textures)
        if texture_uni > 0.5:
            score += 0.25
            reasons.append("yüksek doku tekdüzeliği")
        elif texture_uni > 0.4:
            score += 0.15
            reasons.append("orta doku tekdüzeliği")

        # Edge density - very low edges suggest AI
        if ed < 0.06:
            score += 0.20
            reasons.append("çok düşük kenar yoğunluğu")
        elif ed < 0.08:
            if hf < 0.025:  # Only if combined with smoothness
                score += 0.10
                reasons.append("düşük kenar yoğunluğu")

        # Saturation - be more careful here
        # High saturation alone doesn't mean AI, but combined with other signals it can
        if satm > 0.40 and (hf < 0.025 or texture_uni > 0.4):
            score += 0.15
            reasons.append("yüksek doygunluk + diğer sinyaller")

        score = max(0.0, min(1.0, score))
        
        # Confidence calculation - higher if multiple signals agree
        signal_count = len(reasons)
        if signal_count >= 3:
            confidence = 0.50 + 0.25 * score
        elif signal_count == 2:
            confidence = 0.40 + 0.20 * score
        elif signal_count == 1:
            confidence = 0.30 + 0.15 * score
        else:
            confidence = 0.25
        
        confidence = min(0.85, confidence)
        
        return DetectionResult(
            score=score, 
            confidence=confidence, 
            reasons=reasons[:4] or ["belirgin bir sinyal yakalanmadı"]
        )

    def detect_video(self, frames_dir: str) -> DetectionResult:
        # Aggregate image scores over sampled frames
        import os
        frame_files = sorted(
            [os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))]
        )
        if not frame_files:
            return DetectionResult(score=0.5, confidence=0.2, reasons=["frame örneklenemedi"])

        scores = []
        for fp in frame_files[:30]:
            res = self.detect_image(fp)
            scores.append(res.score)

        avg = float(np.mean(scores))
        var = float(np.var(scores))

        # Temporal inconsistency proxy: high variance across frames could indicate artifacts
        score = avg + min(0.15, var * 2.0)
        score = max(0.0, min(1.0, score))

        reasons = ["frame bazlı analiz ortalaması"] if avg >= 0.5 else ["frame bazlı analiz düşük"]
        if var > 0.02:
            reasons.append("frame’ler arası tutarsızlık işareti (zayıf sinyal)")

        confidence = 0.25 + 0.25 * score
        return DetectionResult(score=score, confidence=confidence, reasons=reasons[:3])
