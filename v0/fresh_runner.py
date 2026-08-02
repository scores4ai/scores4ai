#!/usr/bin/env python3
import time
from urllib.request import Request, urlopen
import github_updater as engine

BASE = "https://cash-pop.com/michigan/winning-numbers"

def direct_fetch():
    candidates = []
    stamp = str(time.time_ns())
    urls = [
        BASE + "?nocache=" + stamp,
        BASE + "/?nocache=" + stamp,
        BASE + "?v=" + stamp + "&source=github",
    ]
    for url in urls:
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1",
                "Accept": "text/html,application/xhtml+xml",
                "Cache-Control": "no-cache, no-store, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            })
            with urlopen(req, timeout=45) as r:
                text = r.read().decode("utf-8", "ignore")
            rows = engine.parse(text)
            if rows:
                candidates.append((max(x["draw"] for x in rows), text, "direct"))
        except Exception as exc:
            print("Direct fetch failed:", url, exc)

    try:
        text = engine.fetch_visible_text()
        rows = engine.parse(text)
        if rows:
            candidates.append((max(x["draw"] for x in rows), text, "browser"))
    except Exception as exc:
        print("Browser fetch failed:", exc)

    if not candidates:
        raise RuntimeError("All live-result fetch methods failed")

    candidates.sort(key=lambda x: x[0], reverse=True)
    print("Selected source:", candidates[0][2], "latest draw:", candidates[0][0])
    return candidates[0][1]

engine.fetch_visible_text = direct_fetch
engine.main()
