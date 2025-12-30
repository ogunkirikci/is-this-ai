"""Scaffold: poll X mentions and enqueue jobs.

You must implement the exact X endpoints depending on your API plan.
Typical steps:
1) call mentions endpoint or search recent tweets: query = '@isthisai -is:retweet'
2) for each mention tweet:
   - resolve referenced tweet (quoted / replied / contains media itself)
   - extract media urls (image/video variants)
   - POST to your API /enqueue for each media

This file is intentionally incomplete to avoid baking in wrong endpoint assumptions.
"""

import os
import time
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))

def main():
    print("poll_mentions scaffold running. Implement X API calls in this script.")
    while True:
        # TODO: call X API, collect media items
        # Example enqueue call:
        # requests.post(f"{API_URL}/enqueue", json={...}, timeout=10).raise_for_status()
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
