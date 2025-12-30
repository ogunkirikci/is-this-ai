from __future__ import annotations
from PIL import Image
import os

def normalize_image(in_path: str, out_dir: str, max_side: int = 1024) -> str:
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(in_path).convert("RGB")

    w, h = img.size
    scale = min(1.0, max_side / float(max(w, h)))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))

    out_path = os.path.join(out_dir, "normalized.jpg")
    img.save(out_path, format="JPEG", quality=92, optimize=True)
    return out_path
