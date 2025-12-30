# isthisai – X (Twitter) mention → AI media check bot (FastAPI + Redis + Python workers)

This repo is a production-leaning **skeleton** for an X bot that:
1) detects when `@isthisai` is mentioned
2) downloads the referenced image/video
3) runs an AI-likelihood analysis (pluggable detectors)
4) replies with a short result

> ⚠️ Important: Reliable “AI vs real” detection is a hard problem.
> The included detector is a **heuristic baseline** + a clean interface to plug in a real ML detector later.

---

## Architecture

- **API service (FastAPI)**: accepts enqueue requests (from an X polling script or your own webhook handler)
- **Redis**: queue + cache
- **Worker (RQ)**: pulls jobs from Redis and processes media
- **Media pipeline**:
  - image: normalize → compute features → score
  - video: download → sample frames with `ffmpeg` → per-frame score → aggregate + temporal stability

---

## Quick start (Docker Compose)

### 1) Requirements
- Docker / Docker Compose
- (Optional outside Docker) `ffmpeg` installed if you run locally

### 2) Configure env
Create `.env` (or set env vars) with:

```bash
# Redis
REDIS_URL=redis://redis:6379/0

# X (Twitter) API credentials (fill these)
X_BEARER_TOKEN=...
X_CONSUMER_KEY=...
X_CONSUMER_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...

# Bot identity
BOT_USERNAME=isthisai
BOT_HANDLE=@isthisai

# Behavior
MAX_VIDEO_SECONDS=60
MAX_VIDEO_FRAMES=30
FRAME_FPS=1
REPLY_COOLDOWN_SECONDS=60
```

> The included X client is a placeholder that demonstrates request shapes.  
> You’ll need to implement the exact endpoints per your X API plan.

### 3) Run
```bash
docker compose up --build
```

- API: http://localhost:8000
- Redis: localhost:6379

### 4) Enqueue a test job
```bash
curl -X POST http://localhost:8000/enqueue   -H "Content-Type: application/json"   -d '{
    "tweet_id": "123",
    "author_id": "456",
    "media_url": "https://example.com/image.jpg",
    "media_type": "image",
    "reply_to_tweet_id": "123"
  }'
```

---

## Local (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export REDIS_URL=redis://localhost:6379/0

uvicorn app.main:app --reload
python scripts/worker.py
```

---

## Where to add a real detector
- Implement `app/detectors/base.py::Detector` and register it in `app/detectors/__init__.py`
- Replace the heuristic detector with:
  - an ONNX/Torch model you ship with the repo, or
  - a paid API (keep keys server-side), or
  - a mix (ensemble)

---

## Notes on X integration
- Mentions can be pulled by polling (cron / long-running process) using X endpoints.
- For each mention:
  - find the target tweet (original/quoted/replied)
  - extract media URLs
  - enqueue jobs (one job per media)

See `scripts/poll_mentions.py` for a scaffold.

---

## License
MIT
