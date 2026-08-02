#!/usr/bin/env python3
import html
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright
import github_updater as engine

BASE = "https://cash-pop.com/michigan/winning-numbers"
FALLBACKS = [
    "https://michiganlotterynumbers.com/cash-pop/numbers",
    "https://michiganlotterylive.com/cash-pop/results",
]
STATE = Path(__file__).with_name("cloud_state.json")


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


def parse_dt(date_text, time_text):
    raw = f"{date_text} {time_text}".replace("  ", " ").strip()
    raw = re.sub(r"\s+(ET|EST|EDT)$", "", raw, flags=re.I)
    for fmt in (
        "%A, %B %d, %Y %I:%M %p",
        "%A, %B %d, %Y %I:%M%p",
        "%A %B %d %Y %I:%M %p",
        "%A %B %d %Y %I:%M%p",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    return None


def load_old_draws():
    try:
        return json.loads(STATE.read_text()).get("draws", [])
    except Exception:
        return []


def parse_fallback_text(text, source):
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.replace("\r", "").split("\n")]
    lines = [x for x in lines if x]
    date_time_rx = re.compile(
        r"^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),?\s+"
        r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s*(?:-|–|—)\s*"
        r"(\d{1,2}:\d{2}\s*(?:AM|PM))$",
        re.I,
    )
    number_rx = re.compile(r"^(1[0-5]|[1-9])$")
    seen = {}
    for i, line in enumerate(lines):
        m = date_time_rx.match(line)
        if not m:
            continue
        date_text = f"{m.group(1)}, {m.group(2).replace(',', '')}"
        time_text = re.sub(r"\s+", " ", m.group(3).upper()).replace("AM", " AM").replace("PM", " PM")
        time_text = re.sub(r"\s+", " ", time_text).strip()
        number = None
        for j in range(i + 1, min(len(lines), i + 7)):
            if number_rx.match(lines[j]):
                number = int(lines[j])
                break
        dt = parse_dt(date_text, time_text)
        if dt and number is not None:
            seen[dt] = {"number": number, "date": date_text, "time": time_text, "source": source}

    old = load_old_draws()
    old_by_dt = {}
    for row in old:
        dt = parse_dt(row.get("date", ""), row.get("time", ""))
        if dt:
            old_by_dt[(dt, int(row["number"]))] = int(row["draw"])

    ordered = sorted(seen.items())
    anchors = []
    for idx, (dt, row) in enumerate(ordered):
        draw = old_by_dt.get((dt, row["number"]))
        if draw is not None:
            anchors.append((idx, draw))
    if not anchors:
        print("fallback had rows but no verified timestamp anchor", source, len(ordered))
        return []

    anchor_idx, anchor_draw = max(anchors, key=lambda x: x[1])
    mapped = []
    for idx in range(anchor_idx, len(ordered)):
        dt, row = ordered[idx]
        mapped.append({
            "draw": anchor_draw + (idx - anchor_idx),
            "number": row["number"],
            "date": row["date"],
            "time": row["time"],
            "source": source + " timestamp-matched",
        })
    return mapped


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
                    if "draw" in body.lower() or "winning" in body.lower():
                        bodies.append((response.url, body))
                except Exception:
                    pass

        page.on("response", capture)
        try:
            page.goto(BASE + "?live=" + stamp, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(12000)
            bodies.append(("page-visible", page.locator("body").inner_text(timeout=30000)))
        except Exception as exc:
            print("primary browser failed", repr(exc))

        for fallback in FALLBACKS:
            try:
                page.goto(fallback + "?live=" + str(time.time_ns()), wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(7000)
                visible = page.locator("body").inner_text(timeout=30000)
                rows = parse_fallback_text(visible, fallback)
                if rows:
                    candidates.append((max(r["draw"] for r in rows), rows, fallback + " [fallback]"))
                    print("fallback candidate", max(r["draw"] for r in rows), fallback)
            except Exception as exc:
                print("fallback browser failed", fallback, repr(exc))
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
    urls = [BASE] + FALLBACKS
    for base in urls:
        url = base + ("&" if "?" in base else "?") + "nocache=" + str(time.time_ns())
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/json,*/*",
                "Cache-Control": "no-cache, no-store, max-age=0",
                "Pragma": "no-cache",
            })
            with urlopen(req, timeout=60) as response:
                body = response.read().decode("utf-8", "ignore")
            text = html_to_text(body)
            if base == BASE:
                for candidate_text in (body, text):
                    rows = engine.parse(candidate_text)
                    if rows:
                        candidates.append((max(r["draw"] for r in rows), rows, url))
            else:
                rows = parse_fallback_text(text, base)
                if rows:
                    candidates.append((max(r["draw"] for r in rows), rows, url + " [fallback-direct]"))
        except Exception as exc:
            print("direct failed", url, repr(exc))
    return candidates


def rows_to_engine_text(rows):
    lines = []
    current_date = None
    for row in sorted(rows, key=lambda x: x["draw"], reverse=True):
        date = row.get("date", "")
        if date and date != current_date:
            lines.append(date)
            current_date = date
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
