from fastapi import FastAPI, HTTPException
from rq.job import Job
from .queue import get_queue, get_redis
from .models import EnqueueRequest, JobStatusResponse
from .tasks import process_media_job

app = FastAPI(title="isthisai-bot API", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True}

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
