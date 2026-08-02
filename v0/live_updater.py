#!/usr/bin/env python3
"""Run the predictor with a fresh, cache-busted results fetch.

The source site pauses Michigan drawings between 2:44 AM and 5:09 AM.
This wrapper does not assume continuous clock times; draw number is the key.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, urlopen
import json
import os

import cloud_engine as engine


def fresh_url(url: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["_predictor_refresh"] = str(int(datetime.now(timezone.utc).timestamp()))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def fetch_fresh(url: str):
    target = fresh_url(url)
    request = Request(
        target,
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            "Accept": "application/json,text/html,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "ignore"), response.headers.get("content-type", "")


engine.fetch_url = fetch_fresh
engine.main()

# Fail loudly if the cloud state did not receive a valid next-draw target.
state = json.loads(engine.STATE_PATH.read_text())
latest = int(state.get("latestDraw") or 0)
pending = state.get("pending") or {}
if latest <= 0 or int(pending.get("draw") or 0) != latest + 1:
    raise RuntimeError(f"Invalid updated state: latest={latest}, pending={pending.get('draw')}")
print(f"Updated through draw #{latest}; next prediction #{pending['draw']}; feed={state.get('feed')}")
