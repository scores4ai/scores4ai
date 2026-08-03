#!/usr/bin/env python3
"""Build a separate, immutable Michigan Cash Pop archive.

This never edits the live APX source. It downloads year pages, parses authentic
historical results, merges them with any previously accepted archive records,
and rejects conflicting values for an existing draw ID.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ARCHIVE = Path("apx/full_archive.json")
LIVE = Path("v0/cloud_state.json")
YEARS = (2024, 2025, 2026)
SOURCES = [
    "https://www.lottery.net/michigan/cash-pop/numbers/{year}",
    "https://michiganlotterynumbers.com/cash-pop/numbers/{year}",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def fetch(url):
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 APX Historical Research Archive",
        "Cache-Control": "no-cache",
    })
    with urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", "ignore")


def clean_html(html):
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&amp;", "&")
    return "\n".join(re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip())


def parse_lottery_net(text, year, source):
    # Page order is newest to oldest. Typical sequence:
    # Wednesday - 11:56pm / December 31, 2025 / 58296 / 15
    lines = text.splitlines()
    date_rx = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*-\s*(\d{1,2}:\d{2}\s*(?:am|pm))$", re.I)
    calendar_rx = re.compile(r"^([A-Za-z]+\s+\d{1,2},\s*\d{4})$")
    integer_rx = re.compile(r"^\d+$")
    rows = []
    for i, line in enumerate(lines):
        dm = date_rx.match(line)
        if not dm:
            continue
        date_text = time_text = None
        draw = number = None
        for j in range(i + 1, min(len(lines), i + 12)):
            value = lines[j]
            if date_text is None and calendar_rx.match(value):
                date_text = value
                time_text = dm.group(2).upper().replace("AM", " AM").replace("PM", " PM")
                time_text = re.sub(r"\s+", " ", time_text)
                continue
            if date_text and integer_rx.match(value):
                n = int(value)
                if draw is None and n > 1000:
                    draw = n
                    continue
                if draw is not None and 1 <= n <= 15:
                    number = n
                    break
        if draw and number and date_text and date_text.endswith(str(year)):
            rows.append({
                "draw": draw,
                "number": number,
                "date": date_text,
                "time": time_text,
                "source": source,
            })
    return rows


def parse_mln(text, year, source):
    # This source may omit draw IDs, so it is used only for cross-check counts,
    # not as the canonical archive identity source.
    date_time_rx = re.compile(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
        r"([A-Za-z]+\s+\d{1,2},\s*\d{4})\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))$", re.I
    )
    lines = text.splitlines()
    rows = []
    for i, line in enumerate(lines):
        m = date_time_rx.match(line)
        if not m or not m.group(2).endswith(str(year)):
            continue
        for j in range(i + 1, min(len(lines), i + 5)):
            if lines[j].isdigit() and 1 <= int(lines[j]) <= 15:
                rows.append({"date": m.group(2), "time": m.group(3).upper(), "number": int(lines[j]), "source": source})
                break
    return rows


def load_previous():
    try:
        data = json.loads(ARCHIVE.read_text())
        return {int(x["draw"]): x for x in data.get("draws", [])}
    except Exception:
        return {}


def load_live():
    try:
        data = json.loads(LIVE.read_text())
        return {int(x["draw"]): x for x in data.get("draws", [])}
    except Exception:
        return {}


def fingerprint(draws):
    payload = "\n".join(f'{x["draw"]},{x["number"]},{x.get("date","")},{x.get("time","")}' for x in draws)
    return hashlib.sha256(payload.encode()).hexdigest()


def main():
    accepted = load_previous()
    conflicts = []
    source_report = []

    for year in YEARS:
        for template in SOURCES:
            url = template.format(year=year)
            try:
                text = clean_html(fetch(url))
                if "lottery.net" in url:
                    rows = parse_lottery_net(text, year, url)
                    for row in rows:
                        draw = int(row["draw"])
                        old = accepted.get(draw)
                        if old and int(old["number"]) != int(row["number"]):
                            conflicts.append({"draw": draw, "existing": old["number"], "incoming": row["number"], "source": url})
                        else:
                            accepted[draw] = row
                    source_report.append({"year": year, "source": url, "canonicalRows": len(rows), "status": "ok" if rows else "empty"})
                else:
                    checks = parse_mln(text, year, url)
                    source_report.append({"year": year, "source": url, "crossCheckRows": len(checks), "status": "ok" if checks else "empty"})
            except Exception as exc:
                source_report.append({"year": year, "source": url, "status": "error", "error": repr(exc)})

    # Current live draws extend the archive and preserve exact draw IDs.
    for draw, row in load_live().items():
        old = accepted.get(draw)
        if old and int(old["number"]) != int(row["number"]):
            conflicts.append({"draw": draw, "existing": old["number"], "incoming": row["number"], "source": "live APX feed"})
        else:
            accepted[draw] = {**row, "source": row.get("source") or "live APX feed"}

    if conflicts:
        raise SystemExit("Archive conflict detected: " + json.dumps(conflicts[:10]))

    draws = [accepted[k] for k in sorted(accepted)]
    if not draws:
        raise SystemExit("No canonical historical rows were accepted")

    ids = [int(x["draw"]) for x in draws]
    missing_ids = []
    for a, b in zip(ids, ids[1:]):
        if b > a + 1:
            missing_ids.extend(range(a + 1, min(b, a + 101)))

    out = {
        "version": 1,
        "immutableAppendOnly": True,
        "updatedAt": now(),
        "drawCount": len(draws),
        "firstDraw": ids[0],
        "latestDraw": ids[-1],
        "sha256": fingerprint(draws),
        "validation": {
            "duplicateDrawIds": len(ids) - len(set(ids)),
            "conflicts": 0,
            "numbersOutside1To15": sum(not 1 <= int(x["number"]) <= 15 for x in draws),
            "missingDrawIdCount": sum(max(0, b - a - 1) for a, b in zip(ids, ids[1:])),
            "sampleMissingDrawIds": missing_ids[:100],
            "chronological": ids == sorted(ids),
        },
        "sources": source_report,
        "draws": draws,
    }
    ARCHIVE.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("drawCount", "firstDraw", "latestDraw", "sha256")}))


if __name__ == "__main__":
    main()
