from __future__ import annotations
import os, tempfile, json
from .detectors import get_default_detector
from .media.download import download_to
from .media.image import normalize_image
from .media.video import extract_frames
from .storage.cache import sha256_file, cache_get, cache_set
from .queue import get_redis
from .x.client import XClient

def format_reply(score: float, confidence: float, reasons: list[str]) -> str:
    # Map to buckets
    if score >= 0.75:
        bucket = "Yüksek olasılık"
    elif score >= 0.45:
        bucket = "Orta olasılık"
    else:
        bucket = "Düşük olasılık"

    pct = int(round(score * 100))
    conf = int(round(confidence * 100))

    # Keep reply short to reduce spam / long threads
    rs = "; ".join(reasons[:2])
    return (
        f"{bucket}: AI ile üretilmiş/düzenlenmiş olma ihtimali ≈ %{pct} (güven %{conf}).\n"
        f"Sinyaller: {rs}.\n"
        "Not: Bu otomatik bir tahmindir; kesin doğrulama için kaynak dosya / içerik kimlik bilgileri gerekir."
    )

def process_media_job(payload: dict) -> dict:
    """RQ job entrypoint."""
    redis = get_redis()
    detector = get_default_detector()
    x = XClient()

    media_url = payload["media_url"]
    media_type = payload["media_type"]
    reply_to = payload["reply_to_tweet_id"]

    with tempfile.TemporaryDirectory(prefix="isthisai_") as tmp:
        raw_dir = os.path.join(tmp, "raw")
        proc_dir = os.path.join(tmp, "processed")
        frames_dir = os.path.join(tmp, "frames")

        # download
        raw_path = download_to(str(media_url), raw_dir)
        digest = sha256_file(raw_path)

        cache_key = f"isthisai:result:{digest}"
        cached = cache_get(redis, cache_key)
        if cached:
            result = json.loads(cached)
            # still reply (but you may choose to skip replies if already done per tweet)
            x.reply(reply_to, result["reply_text"])
            return result

        if media_type == "image":
            norm_path = normalize_image(raw_path, proc_dir, max_side=1024)
            res = detector.detect_image(norm_path)
        elif media_type == "video":
            extract_frames(raw_path, frames_dir)
            res = detector.detect_video(frames_dir)
        else:
            raise ValueError(f"Unknown media_type: {media_type}")

        reply_text = format_reply(res.score, res.confidence, res.reasons)

        # reply
        x.reply(reply_to, reply_text)

        result = {
            "score": res.score,
            "confidence": res.confidence,
            "reasons": res.reasons,
            "detector": getattr(detector, "name", "unknown"),
            "media_sha256": digest,
            "reply_text": reply_text,
        }
        cache_set(redis, cache_key, json.dumps(result), ttl=7 * 24 * 3600)
        return result
