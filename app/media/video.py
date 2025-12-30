from __future__ import annotations
import os, subprocess, shlex
from ..config import settings

def extract_frames(video_path: str, frames_dir: str) -> str:
    os.makedirs(frames_dir, exist_ok=True)

    # Limit analysis duration
    # Sample frames at FRAME_FPS, cap to MAX_VIDEO_FRAMES via -frames:v
    fps = max(1, settings.FRAME_FPS)
    max_frames = max(1, settings.MAX_VIDEO_FRAMES)
    max_seconds = max(1, settings.MAX_VIDEO_SECONDS)

    out_pattern = os.path.join(frames_dir, "frame_%03d.jpg")
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-t", str(max_seconds),
        "-i", video_path,
        "-vf", f"fps={fps},scale=960:-1",
        "-frames:v", str(max_frames),
        out_pattern,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.strip()[:400]}")
    return frames_dir
