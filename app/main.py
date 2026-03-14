from __future__ import annotations
import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from rq.job import Job
from .queue import get_queue, get_redis
from .models import EnqueueRequest, JobStatusResponse
from .tasks import process_media_job, format_reply
from .detectors import get_default_detector
from .media.image import normalize_image

app = FastAPI(title="isthisai-bot API", version="0.1.0")

# Accept image formats
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse)
def test_page():
    """Görsel test sayfası (Twitter entegrasyonu yok)."""
    path = STATIC_DIR / "test.html"
    return path.read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze")
def analyze_image(file: UploadFile = File(...)):
    """Test için: görsel yükle, AI analizi yap, sonucu döndür (Twitter yok)."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenen formatlar: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        content = file.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dosya okunamadı: {e}")

    with tempfile.TemporaryDirectory(prefix="isthisai_analyze_") as tmp:
        raw_path = os.path.join(tmp, f"upload{ext}")
        proc_dir = os.path.join(tmp, "processed")
        with open(raw_path, "wb") as f:
            f.write(content)

        try:
            norm_path = normalize_image(raw_path, proc_dir, max_side=1024)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Görsel işlenemedi: {e}")

        detector = get_default_detector()
        res = detector.detect_image(norm_path)

    comment = format_reply(res.score, res.confidence, res.reasons)

    return {
        "score": res.score,
        "confidence": res.confidence,
        "reasons": res.reasons,
        "comment": comment,
    }

@app.post("/enqueue", response_model=JobStatusResponse)
def enqueue(req: EnqueueRequest):
    q = get_queue()
    job = q.enqueue(
        process_media_job,
        req.model_dump(),
        job_timeout=300,
        result_ttl=3600,
        failure_ttl=3600,
    )
    return JobStatusResponse(job_id=job.id, status=job.get_status())

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str):
    redis = get_redis()
    try:
        job = Job.fetch(job_id, connection=redis)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job.id, status=job.get_status())
