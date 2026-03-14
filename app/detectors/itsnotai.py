"""ItsNotAI v2 - Hugging Face tabanlı AI görsel tespiti.

Model: boluobobo/ItsNotAI-ai-detector-v2
- Dual-head: Real vs AI + kaynak tespiti (Midjourney, FLUX, Stable Diffusion vb.)
- ~95% doğruluk, FLUX/Midjourney desteği
"""
from __future__ import annotations
import json
import os
from typing import Any

from PIL import Image

from .base import DetectionResult

# Lazy imports - model sadece ilk detect_image çağrısında yüklenir
_model: Any = None
_processor: Any = None
_binary_head: Any = None
_source_names: list[str] | None = None
_source_is_real: dict[str, bool] | None = None
_hidden_size: int = 0


def _load_model() -> None:
    global _model, _processor, _binary_head, _source_names, _source_is_real, _hidden_size
    if _model is not None:
        return

    import torch
    import torch.nn as nn
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    from huggingface_hub import hf_hub_download

    model_id = "boluobobo/ItsNotAI-ai-detector-v2"
    _model = AutoModelForImageClassification.from_pretrained(model_id)
    _processor = AutoImageProcessor.from_pretrained(model_id)
    _model.eval()

    meta_path = hf_hub_download(repo_id=model_id, filename="source_meta.json")
    with open(meta_path) as f:
        meta = json.load(f)
    _source_names = meta["source_names"]
    _source_is_real = meta.get("source_is_real", {})
    _hidden_size = meta.get("hidden_size", _model.config.hidden_size)

    binary_head_path = hf_hub_download(repo_id=model_id, filename="binary_head.pt")
    _binary_head = nn.Sequential(nn.Dropout(0.1), nn.Linear(_hidden_size, 2))
    _binary_head.load_state_dict(torch.load(binary_head_path, map_location="cpu"))
    _binary_head.eval()


def _get_backbone_features(pixel_values: Any) -> Any:
    import torch

    if hasattr(_model, "beit"):
        outputs = _model.beit(pixel_values)
    elif hasattr(_model, "vit"):
        outputs = _model.vit(pixel_values)
    else:
        raise RuntimeError("Model backbone (beit/vit) bulunamadı")
    return outputs.last_hidden_state[:, 0]


def _detect_single(image_path: str) -> dict:
    import torch

    _load_model()
    img = Image.open(image_path).convert("RGB")
    inputs = _processor(img, return_tensors="pt")

    with torch.no_grad():
        outputs = _model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]
        features = _get_backbone_features(inputs["pixel_values"])
        binary_logits = _binary_head(features)
        binary_probs = torch.softmax(binary_logits, dim=-1)[0]

    human_prob = binary_probs[0].item()
    ai_prob = binary_probs[1].item()
    pred_idx = probs.argmax().item()
    predicted_source = _source_names[pred_idx]

    return {
        "ai_probability": ai_prob,
        "human_probability": human_prob,
        "predicted_source": predicted_source,
        "is_real": human_prob > ai_prob,
    }


class ItsNotAIDetector:
    """ItsNotAI v2 modeli ile AI görsel tespiti."""

    name: str = "itsnotai-v2"

    def detect_image(self, image_path: str) -> DetectionResult:
        res = _detect_single(image_path)
        score = res["ai_probability"]
        is_real = res["is_real"]
        source = res["predicted_source"]

        reasons: list[str] = []
        if is_real:
            reasons.append(f"model: gerçek fotoğraf tahmini ({source})")
        else:
            reasons.append(f"model: AI üretimi tahmini (kaynak: {source})")

        confidence = 0.5 + 0.35 * abs(score - 0.5)
        return DetectionResult(score=score, confidence=confidence, reasons=reasons)

    def detect_video(self, frames_dir: str) -> DetectionResult:
        import os

        frame_files = sorted(
            [
                os.path.join(frames_dir, f)
                for f in os.listdir(frames_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )
        if not frame_files:
            return DetectionResult(score=0.5, confidence=0.2, reasons=["frame örneklenemedi"])

        scores: list[float] = []
        for fp in frame_files[:30]:
            r = self.detect_image(fp)
            scores.append(r.score)

        import numpy as np

        avg = float(np.mean(scores))
        var = float(np.var(scores))
        score = min(1.0, avg + min(0.1, var * 1.5))
        reasons = ["frame bazlı ItsNotAI analizi ortalaması"]
        if var > 0.02:
            reasons.append("frame'ler arası tutarsızlık işareti")
        confidence = 0.4 + 0.3 * score
        return DetectionResult(score=score, confidence=confidence, reasons=reasons[:3])
