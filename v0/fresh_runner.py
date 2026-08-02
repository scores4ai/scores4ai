#!/usr/bin/env python3
import html
import json
import re
import time
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright
import github_updater as engine

BASE = "https://cash-pop.com/michigan/winning-numbers"


def html_to_text(document: str) -> str:
    document = re.sub(r"(?is)<script[^>]*>.*?</script>", "\n", document)
    document = re.sub(r"(?is)<style[^>]*>.*?</style>", "\n", document)
    document = re.sub(r"(?i)<br\s*/?>", "\n", document)
    document = re.sub(r"(?i)</(?:div|p|li|section|article|h[1-6]|tr|td|span|a)>", "\n", document)
    document = re.sub(r"(?s)<[^>]+>", " ", document)
    return "\n".join(x.strip() for x in html.unescape(document).replace("\xa0", " ").splitlines() if x.strip())


def normalize_json(value, out):
    if isinstance(value, dict):
        draw = None
        number = None
        for key, val in value.items():
            k = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if k in {"draw", "drawnumber", "drawid", "drawingnumber"}:
                try:
                    n = int(val)
                    if 80000 <= n <= 999999:
                        draw = n
                except Exception:
                    pass
            if k in {"number", "winningnumber", "result", "ball", "value"}:
                try:
                    n = int(val)
                    if 1 <= n <= 15:
                        number = n
                except Exception:
                    pass
        if draw and number:
            out[draw] = {"draw": draw, "number": number, "date": "", "time": "", "source": "live network JSON"}
        for val in value.values():
            normalize_json(val, out)
    elif isinstance(value, list):
        for item in value:
            normalize_json(item, out)


def browser_candidates():
    candidates = []
    bodies = []
    stamp = str(time.time_ns())
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1",
            extra_http_headers={"Cache-Control": "no-cache, no-store, max-age=0", "Pragma": "no-cache"},
        )
        page = context.new_page()
        session = context.new_cdp_session(page)
        session.send("Network.enable")
        session.send("Network.setCacheDisabled", {"cacheDisabled": True})

        def capture(response):
            ctype = (response.headers.get("content-type") or "").lower()
            if any(x in ctype for x in ("json", "javascript", "text", "html")):
                try:
                    body = response.body().decode("utf-8", "ignore")
                    if "886" in body or "draw" in body.lower() or "winning" in body.lower():
                        bodies.append((response.url, body))
                except Exception:
                    pass

        page.on("response", capture)
        page.goto(BASE + "?live=" + stamp, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(10000)
        page.reload(wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(5000)
        bodies.append(("page-visible", page.locator("body").inner_text(timeout=30000)))
        browser.close()

    for url, body in bodies:
        rows = engine.parse(body)
        if rows:
            candidates.append((max(r["draw"] for r in rows), rows, url))
        try:
            payload = json.loads(body)
            found = {}
            normalize_json(payload, found)
            if found:
                rows2 = [found[k] for k in sorted(found)]
                candidates.append((max(found), rows2, url + " [json]"))
        except Exception:
            pass
    return candidates


def direct_candidates():
    candidates = []
    for suffix in ("?nocache=", "/?nocache=", "?v="):
        url = BASE + suffix + str(time.time_ns())
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/json,*/*",
                "Cache-Control": "no-cache, no-store, max-age=0",
                "Pragma": "no-cache",
            })
            with urlopen(req, timeout=60) as response:
                body = response.read().decode("utf-8", "ignore")
            for text in (body, html_to_text(body)):
                rows = engine.parse(text)
                if rows:
                    candidates.append((max(r["draw"] for r in rows), rows, url))
        except Exception as exc:
            print("direct failed", url, repr(exc))
    return candidates


def rows_to_engine_text(rows):
    lines = []
    for row in sorted(rows, key=lambda x: x["draw"], reverse=True):
        lines.extend([str(row["number"]), f"#{row['draw']}", row.get("time", "")])
    return "\n".join(lines)


def freshest_text():
    candidates = direct_candidates() + browser_candidates()
    if not candidates:
        raise RuntimeError("No live result candidate found")
    candidates.sort(key=lambda x: x[0], reverse=True)
    latest, rows, source = candidates[0]
    print("selected", latest, source)
    return rows_to_engine_text(rows)


engine.fetch_visible_text = freshest_text
engine.main()
