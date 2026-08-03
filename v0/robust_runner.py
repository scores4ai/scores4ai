#!/usr/bin/env python3
import json
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright
import github_updater as engine

STATE = Path(__file__).with_name("cloud_state.json")
SOURCES = [
    "https://michiganlotterynumbers.com/cash-pop/numbers",
    "https://cash-pop.com/michigan/winning-numbers",
]


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


def clock(text):
    return re.sub(r"\s+", " ", str(text or "").upper()).strip()


def load_old():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"draws": []}


def parse_timestamp_results(text, source):
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.replace("\r", "").split("\n")]
    lines = [x for x in lines if x]
    date_time_rx = re.compile(
        r"^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),?\s+"
        r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s*(?:-|–|—)\s*"
        r"(\d{1,2}:\d{2}\s*(?:AM|PM))$",
        re.I,
    )
    number_rx = re.compile(r"^(1[0-5]|[1-9])$")
    seen = []
    for i, line in enumerate(lines):
        match = date_time_rx.match(line)
        if not match:
            continue
        date_text = f"{match.group(1)}, {match.group(2).replace(',', '')}"
        time_text = clock(match.group(3))
        number = None
        for j in range(i + 1, min(len(lines), i + 8)):
            if number_rx.match(lines[j]):
                number = int(lines[j])
                break
        dt = parse_dt(date_text, time_text)
        if dt and number is not None:
            seen.append((dt, {"number": number, "date": date_text, "time": time_text, "source": source}))
    return sorted(dict(seen).items())


def map_draw_ids(timestamp_rows):
    old = load_old().get("draws", [])
    by_dt = {}
    by_time_number = {}
    for row in old:
        number = int(row["number"])
        draw = int(row["draw"])
        dt = parse_dt(row.get("date", ""), row.get("time", ""))
        if dt:
            by_dt[(dt, number)] = max(draw, by_dt.get((dt, number), 0))
        tm = clock(row.get("time"))
        if tm:
            by_time_number[(tm, number)] = max(draw, by_time_number.get((tm, number), 0))

    anchors = []
    for index, (dt, row) in enumerate(timestamp_rows):
        draw = by_dt.get((dt, row["number"]))
        if draw is None:
            draw = by_time_number.get((dt.strftime("%-I:%M %p"), row["number"]))
        if draw is not None:
            anchors.append((index, draw))

    if not anchors:
        return []

    anchor_index, anchor_draw = max(anchors, key=lambda item: item[1])
    mapped = []
    for index in range(anchor_index, len(timestamp_rows)):
        dt, row = timestamp_rows[index]
        mapped.append({
            "draw": anchor_draw + index - anchor_index,
            "number": row["number"],
            "date": row["date"],
            "time": row["time"],
            "source": row["source"] + " time-number anchored",
        })
    return mapped


def fetch_candidates():
    candidates = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1",
            extra_http_headers={"Cache-Control": "no-cache, no-store, max-age=0", "Pragma": "no-cache"},
        )
        page = context.new_page()
        for source in SOURCES:
            try:
                page.goto(source + "?fresh=" + str(time.time_ns()), wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(9000)
                visible = page.locator("body").inner_text(timeout=30000)

                direct = engine.parse(visible)
                if direct:
                    candidates.append((max(row["draw"] for row in direct), direct, source + " direct IDs"))

                timestamp_rows = parse_timestamp_results(visible, source)
                mapped = map_draw_ids(timestamp_rows)
                if mapped:
                    candidates.append((max(row["draw"] for row in mapped), mapped, source + " anchored"))
            except Exception as exc:
                print("source failed", source, repr(exc))
        browser.close()
    return candidates


def rows_to_text(rows):
    lines = []
    current_date = None
    for row in sorted(rows, key=lambda value: value["draw"], reverse=True):
        date = row.get("date", "")
        if date and date != current_date:
            lines.append(date)
            current_date = date
        lines.extend([str(row["number"]), f"#{row['draw']}", row.get("time", "")])
    return "\n".join(lines)


def freshest_text():
    old_latest = int(load_old().get("latestDraw", 0) or 0)
    candidates = fetch_candidates()
    if not candidates:
        raise RuntimeError("No current result source could be parsed")
    candidates.sort(key=lambda item: item[0], reverse=True)
    latest, rows, source = candidates[0]
    print("selected", latest, source, "old", old_latest)
    if latest < old_latest:
        raise RuntimeError(f"Candidate regressed from {old_latest} to {latest}")
    return rows_to_text(rows)


engine.fetch_visible_text = freshest_text
engine.main()
