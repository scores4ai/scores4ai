#!/usr/bin/env python3
import json, re
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://cash-pop.com/michigan/winning-numbers"
STATE = Path(__file__).with_name("cloud_state.json")
MAX_DRAWS = 600
MODEL_NAMES = {
    "overall": "Overall frequency",
    "recent24": "Recent 24",
    "recent60": "Recent 60",
    "markov1": "Markov 1",
    "lag7": "Lag 7",
    "cycle8": "Cycle 8",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def fetch_visible_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127 Safari/537.36"
        )
        page.goto(URL + "?github=" + str(int(datetime.now().timestamp())), wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)
        text = page.locator("body").inner_text(timeout=30000)
        browser.close()
        return text

def parse(text):
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.replace("\r", "").split("\n")]
    lines = [x for x in lines if x]
    date_rx = re.compile(r"^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}$", re.I)
    draw_rx = re.compile(r"^#(\d{4,})$")
    time_rx = re.compile(r"^\d{1,2}:\d{2}\s*(AM|PM)$", re.I)
    number_rx = re.compile(r"^(1[0-5]|[1-9])$")
    current_date = ""
    out = {}
    for i, line in enumerate(lines):
        if date_rx.match(line):
            current_date = line
            continue
        m = draw_rx.match(line)
        if not m:
            continue
        draw = int(m.group(1))
        number = None
        time = ""
        for j in range(max(0, i - 3), i):
            if number_rx.match(lines[j]):
                number = int(lines[j])
        for j in range(i + 1, min(len(lines), i + 4)):
            if time_rx.match(lines[j]):
                time = lines[j].upper()
                break
        if number is not None:
            out[draw] = {"draw": draw, "number": number, "date": current_date, "time": time, "source": "cash-pop.com rendered"}
    return [out[k] for k in sorted(out)]

def norm(values):
    total = sum(values) or 1.0
    return [x / total for x in values]

def count(seq, start=0):
    a = [0.5] * 15
    for x in seq[start:]:
        a[x - 1] += 1
    return norm(a)

def markov(seq):
    a = [0.4] * 15
    if seq:
        last = seq[-1]
        for i in range(1, len(seq)):
            if seq[i - 1] == last:
                a[seq[i] - 1] += 1
    return norm(a)

def lag(seq, n):
    a = [0.5] * 15
    if len(seq) >= n:
        a[seq[-n] - 1] += 4
    return norm(a)

def cycle(seq, n):
    a = [0.5] * 15
    slot = len(seq) % n
    for i, x in enumerate(seq):
        if i % n == slot:
            a[x - 1] += 1
    return norm(a)

def models(seq):
    return {
        "overall": count(seq),
        "recent24": count(seq, max(0, len(seq) - 24)),
        "recent60": count(seq, max(0, len(seq) - 60)),
        "markov1": markov(seq),
        "lag7": lag(seq, 7),
        "cycle8": cycle(seq, 8),
    }

def top5(scores):
    return [i + 1 for i, _ in sorted(enumerate(scores), key=lambda z: (-z[1], z[0]))[:5]]

def fresh_weights():
    return {k: 1.0 for k in MODEL_NAMES}

def predict(seq, weights):
    rows = models(seq)
    combined = [0.0] * 15
    model_top5 = {}
    for key, scores in rows.items():
        model_top5[key] = top5(scores)
        w = max(0.05, float(weights.get(key, 1.0)))
        for i, score in enumerate(scores):
            combined[i] += score * w
    return top5(combined), model_top5

def update_weights(weights, model_top5, actual):
    for key in MODEL_NAMES:
        cur = float(weights.get(key, 1.0))
        weights[key] = max(0.05, min(20.0, cur * (1.075 if actual in model_top5.get(key, []) else 0.965)))
    avg = sum(weights.values()) / len(weights)
    for key in weights:
        weights[key] /= avg

def replay(draws):
    seq, history, weights = [], [], fresh_weights()
    warmup = min(60, max(30, int(len(draws) * 0.10)))
    for row in draws:
        if len(seq) >= warmup:
            picks, mt = predict(seq, weights)
            history.append({
                "draw": row["draw"], "top5": picks, "actual": row["number"],
                "hit5": row["number"] in picks,
                "modelResults": {k: row["number"] in v for k, v in mt.items()},
                "type": "historical_walk_forward"
            })
            update_weights(weights, mt, row["number"])
        seq.append(row["number"])
    return history, weights, warmup

def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"draws": [], "history": [], "pending": None, "weights": fresh_weights()}

def main():
    old = load_state()
    fetched = parse(fetch_visible_text())
    if not fetched:
        raise RuntimeError("Rendered page loaded but no draw rows were parsed")

    merged = {int(x["draw"]): x for x in old.get("draws", [])}
    for row in fetched:
        merged[row["draw"]] = row
    draws = [merged[k] for k in sorted(merged)][-MAX_DRAWS:]

    old_ids = {int(x["draw"]) for x in old.get("draws", [])}
    new_rows = [x for x in draws if x["draw"] not in old_ids]
    old_pending = old.get("pending")
    live = [x for x in old.get("history", []) if x.get("type") == "automated_future_test"]

    historical, weights, warmup = replay(draws)
    for row in sorted(new_rows, key=lambda x: x["draw"]):
        if old_pending and int(old_pending.get("draw", -1)) == row["draw"]:
            mt = old_pending.get("modelTop5", {})
            picks = old_pending.get("top5", [])
            live.append({
                "draw": row["draw"], "top5": picks, "actual": row["number"],
                "hit5": row["number"] in picks,
                "modelResults": {k: row["number"] in mt.get(k, []) for k in MODEL_NAMES},
                "type": "automated_future_test",
                "predictedAt": old_pending.get("createdAt"), "scoredAt": now()
            })

    seq = [x["number"] for x in draws]
    picks, model_top5 = predict(seq, weights)
    latest = max(x["draw"] for x in draws)
    pending = {"draw": latest + 1, "top5": picks, "modelTop5": model_top5, "createdAt": now(), "feedControlled": True}
    history = historical + live
    successes = sum(1 for x in history if x.get("hit5"))
    live_successes = sum(1 for x in live if x.get("hit5"))

    state = {
        "draws": draws, "history": history, "weights": weights, "pending": pending,
        "warmup": warmup, "latestDraw": latest, "seedCount": len(draws),
        "feed": "cash-pop.com rendered GitHub feed", "source": URL,
        "updatedAt": now(), "modelNames": MODEL_NAMES,
        "stats": {
            "evaluated": len(history), "successes": successes, "misses": len(history) - successes,
            "accuracy": successes / len(history) if history else 0,
            "liveEvaluated": len(live), "liveSuccesses": live_successes,
            "liveMisses": len(live) - live_successes,
            "liveAccuracy": live_successes / len(live) if live else 0,
            "randomTop5Baseline": 1 / 3
        }
    }
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({"latestDraw": latest, "nextDraw": latest + 1, "fetched": len(fetched), "stored": len(draws)}))

if __name__ == "__main__":
    main()
