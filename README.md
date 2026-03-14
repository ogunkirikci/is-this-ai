# isthisai-bot

A bot that analyzes images or videos shared on X (Twitter) when mentioned with `@isthisai` and assesses the likelihood of AI-generated content.

## What It Does

The bot follows these steps:
1. Triggered when `@isthisai` is mentioned on X
2. Downloads the relevant image/video
3. Analyzes whether it is AI-generated (uses ItsNotAI v2 model)
4. Replies with the result as a tweet

**Note:** AI detection is a hard problem. The current detector uses ItsNotAI v2 (Hugging Face). No detector is 100% accurate; false positives and negatives can occur.

## Architecture

- **FastAPI**: REST API for enqueueing jobs and status queries
- **Redis**: Job queue and cache (same media is not re-analyzed)
- **RQ Worker**: Workers that process jobs from the queue and analyze media
- **Media Pipeline**:
  - Image: normalize → extract features → score
  - Video: download → extract frames via ffmpeg → analyze each frame → aggregate results

## Installation

### With Docker (Recommended)

1. Create a `.env` file:

```bash
# Redis
REDIS_URL=redis://redis:6379/0

# X API credentials (fill in your own)
X_BEARER_TOKEN=...
X_CONSUMER_KEY=...
X_CONSUMER_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...

# Bot settings
BOT_USERNAME=isthisai
BOT_HANDLE=@isthisai

# Behavior
MAX_VIDEO_SECONDS=60
MAX_VIDEO_FRAMES=30
FRAME_FPS=1
REPLY_COOLDOWN_SECONDS=60
```

2. Run:

```bash
docker compose up --build
```

- API: http://localhost:8000
- Redis: localhost:6379

3. Add a test job:

```bash
curl -X POST http://localhost:8000/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "tweet_id": "123",
    "author_id": "456",
    "media_url": "https://example.com/image.jpg",
    "media_type": "image",
    "reply_to_tweet_id": "123"
  }'
```

### Without Docker (with uv)

```bash
# Install dependencies (uv auto-creates .venv)
uv sync

# Start API
uv run uvicorn app.main:app --reload

# In another terminal, start worker
uv run python scripts/worker.py
```

**Using uv:** When you run `uv sync`, uv creates `.venv` and installs packages there. With `uv run`, this venv is used automatically; no need to activate manually.

**Note:** `ffmpeg` must be installed for video analysis.

## Detector

Default detector: **ItsNotAI v2** (Hugging Face)
- Model: `boluobobo/ItsNotAI-ai-detector-v2`
- ~95% accuracy, supports FLUX, Midjourney, Stable Diffusion
- Model is downloaded on first run (~1.2GB)

Optional: Set `HF_TOKEN` (Hugging Face) environment variable for faster downloads.

To switch back to the heuristic detector, use `HeuristicDetector()` in `get_default_detector()` in `app/detectors/__init__.py`.

## Adding a New Detector

1. Implement the `Detector` interface in `app/detectors/base.py`
2. Register it in `app/detectors/__init__.py`

## X Integration

See `scripts/poll_mentions.py` for X API integration. It is currently a placeholder; you need to add real API calls.

General flow:
1. Fetch mentions from X API (polling or webhook)
2. For each mention:
   - Find the target tweet (original/quoted/replied)
   - Extract media URLs
   - POST to `/enqueue` for each media

## Testing

### Web UI (no Twitter)

To upload an image and get AI analysis:

```bash
uv sync && uv run uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser. Drag or select an image, then click **Analyze**. Redis and worker are not required.

### CLI script

```bash
# Add example1.jpg and example2.jpg to test_images/ folder
uv run python scripts/test_images.py
```

## License

MIT
