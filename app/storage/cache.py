from __future__ import annotations
import hashlib
from redis import Redis
from ..queue import get_redis
from ..config import settings

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()

def cache_get(redis: Redis, key: str) -> str | None:
    v = redis.get(key)
    return v.decode("utf-8") if v else None

def cache_set(redis: Redis, key: str, value: str, ttl: int = 24 * 3600) -> None:
    redis.setex(key, ttl, value)
