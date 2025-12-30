from __future__ import annotations
from dataclasses import dataclass
from PIL import Image
import numpy as np
from .base import DetectionResult

@dataclass
class HeuristicDetector:
    name: str = "heuristic-v0"

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

        return {
            "hf_energy": hf_energy,
            "sat_mean": sat_mean,
            "sat_p95": sat_p95,
            "edge_density": edge_density,
        }

    def detect_image(self, image_path: str) -> DetectionResult:
        img = Image.open(image_path)
        feats = self._image_features(img)

        # Heuristic scoring:
        # Very low hf_energy + relatively high saturation can be a weak AI hint
        # (NOT a reliable detector; this is just a baseline).
        hf = feats["hf_energy"]
        satm = feats["sat_mean"]
        ed = feats["edge_density"]

        score = 0.0
        reasons: list[str] = []

        if hf < 0.03:
            score += 0.35
            reasons.append("düşük yüksek-frekans detayı (aşırı pürüzsüz görünüm)")
        if satm > 0.35:
            score += 0.25
            reasons.append("yüksek doygunluk paterni")
        if ed < 0.08:
            score += 0.20
            reasons.append("düşük kenar yoğunluğu (detay azlığı)")

        score = max(0.0, min(1.0, score))
        # confidence low by design
        confidence = 0.35 + 0.25 * score
        return DetectionResult(score=score, confidence=confidence, reasons=reasons[:3] or ["belirgin bir sinyal yakalanmadı"])

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
