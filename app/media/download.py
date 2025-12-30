from __future__ import annotations
import os
import requests
from urllib.parse import urlparse
from ..config import settings

def safe_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = os.path.basename(path) or "media"
    # sanitize
    name = "".join(c for c in name if c.isalnum() or c in "._-")
    return name[:120] or "media"

def download_to(url: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    fn = safe_filename_from_url(url)
    out_path = os.path.join(out_dir, fn)

    with requests.get(url, stream=True, timeout=settings.DOWNLOAD_TIMEOUT_SECONDS) as r:
        r.raise_for_status()
        total = 0
        max_bytes = settings.MAX_DOWNLOAD_MB * 1024 * 1024
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"Download too large (> {settings.MAX_DOWNLOAD_MB} MB)")
                f.write(chunk)
    return out_path
