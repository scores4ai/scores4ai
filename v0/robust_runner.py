#!/usr/bin/env python3
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright
import github_updater as engine

STATE = Path(__file__).with_name("cloud_state.json")
OFFICIAL = "https://www.michiganlottery.com/"
FALLBACKS = [
    "https://michiganlotterynumbers.com/cash-pop/numbers",
    "https://cash-pop.com/michigan/winning-numbers",
]
DIAGNOSTICS = {"official": {"status": "not_checked"}, "fallbacks": []}


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


def normalize_official_json(value, out, context=""):
    if isinstance(value, dict):
        local_context = (context + " " + " ".join(str(v) for v in value.values() if isinstance(v, str))).lower()
        draw = number = None
        for key, val in value.items():
            k = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if k in {"draw", "drawnumber", "drawid", "drawingnumber", "drawno"}:
                try:
                    n = int(str(val).replace("#", ""))
                    if 80000 <= n <= 999999:
                        draw = n
                except Exception:
                    pass
            if k in {"number", "winningnumber", "result", "ball", "value", "winningvalue"}:
                try:
                    n = int(val)
                    if 1 <= n <= 15:
                        number = n
                except Exception:
                    pass
        if draw and number and ("cash pop" in local_context or "cashpop" in local_context):
            out[draw] = {"draw": draw, "number": number, "date": "", "time": "", "source": "official Michigan Lottery network JSON"}
        for val in value.values():
            normalize_official_json(val, out, local_context)
    elif isinstance(value, list):
        for item in value:
            normalize_official_json(item, out, context)


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
    by_dt, by_time_number = {}, {}
    for row in old:
        number, draw = int(row["number"]), int(row["draw"])
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
    return [{
        "draw": anchor_draw + index - anchor_index,
        "number": timestamp_rows[index][1]["number"],
        "date": timestamp_rows[index][1]["date"],
        "time": timestamp_rows[index][1]["time"],
        "source": timestamp_rows[index][1]["source"] + " time-number anchored",
    } for index in range(anchor_index, len(timestamp_rows))]


def fetch_candidates():
    candidates = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18 Mobile Safari/604.1",
            extra_http_headers={"Cache-Control": "no-cache, no-store, max-age=0", "Pragma": "no-cache"},
        )
        page = context.new_page()
        official_payloads = []

        def capture(response):
            url = response.url.lower()
            ctype = (response.headers.get("content-type") or "").lower()
            if "michiganlottery.com" not in url or not any(x in ctype for x in ("json", "javascript", "text")):
                return
            try:
                body = response.body().decode("utf-8", "ignore")
                if "cash pop" in body.lower() or "cashpop" in body.lower():
                    official_payloads.append((response.url, body))
            except Exception:
                pass

        page.on("response", capture)
        try:
            page.goto(OFFICIAL + "?fresh=" + str(time.time_ns()), wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(15000)
            official_found = {}
            for url, body in official_payloads:
                try:
                    normalize_official_json(json.loads(body), official_found, url)
                except Exception:
                    continue
            if official_found:
                rows = [official_found[k] for k in sorted(official_found)]
                latest = max(official_found)
                candidates.append((latest, rows, "official Michigan Lottery"))
                DIAGNOSTICS["official"] = {"status": "online", "latestDraw": latest, "payloads": len(official_payloads)}
            else:
                DIAGNOSTICS["official"] = {"status": "online_no_cash_pop_payload", "payloads": len(official_payloads)}
        except Exception as exc:
            DIAGNOSTICS["official"] = {"status": "error", "error": repr(exc)}

        for source in FALLBACKS:
            info = {"source": source}
            try:
                page.goto(source + "?fresh=" + str(time.time_ns()), wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(8000)
                visible = page.locator("body").inner_text(timeout=30000)
                best = None
                direct = engine.parse(visible)
                if direct:
                    best = (max(row["draw"] for row in direct), direct, source + " direct IDs")
                mapped = map_draw_ids(parse_timestamp_results(visible, source))
                if mapped and (best is None or max(row["draw"] for row in mapped) > best[0]):
                    best = (max(row["draw"] for row in mapped), mapped, source + " anchored")
                if best:
                    candidates.append(best)
                    info.update({"status": "online", "latestDraw": best[0]})
                else:
                    info["status"] = "unparsed"
            except Exception as exc:
                info.update({"status": "error", "error": repr(exc)})
            DIAGNOSTICS["fallbacks"].append(info)
        browser.close()
    return candidates


def rows_to_text(rows):
    lines, current_date = [], None
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
    official = [c for c in candidates if c[2] == "official Michigan Lottery"]
    selected = max(official, key=lambda x: x[0]) if official else max(candidates, key=lambda x: x[0])
    latest, rows, source = selected
    DIAGNOSTICS.update({"selectedSource": source, "selectedLatestDraw": latest, "oldLatestDraw": old_latest, "polledAt": datetime.now(timezone.utc).isoformat()})
    print("selected", latest, source, "old", old_latest)
    if latest < old_latest:
        raise RuntimeError(f"Candidate regressed from {old_latest} to {latest}")
    return rows_to_text(rows)


engine.fetch_visible_text = freshest_text
engine.main()
state = load_old()
state["feedDiagnostics"] = DIAGNOSTICS
state["feed"] = DIAGNOSTICS.get("selectedSource", state.get("feed"))
STATE.write_text(json.dumps(state, indent=2))
