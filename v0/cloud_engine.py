#!/usr/bin/env python3
import json, math, os, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://cash-pop.com/michigan/winning-numbers"
STATE_PATH = Path(__file__).with_name("cloud_state.json")
NUMBERS = list(range(1, 16))

def fetch_html():
    req = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 CashPopResearchBot/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def strip_html(html):
    html = re.sub(r"<script[\s\S]*?</script>", "\n", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", "\n", html, flags=re.I)
    html = re.sub(r"<(?:br|/p|/div|/li|/h[1-6]|/tr)[^>]*>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", html)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&ndash;", "–").replace("&mdash;", "—"))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def parse_draws(html):
    text = strip_html(html)
    dates = list(re.finditer(r"(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}", text))
    out = {}
    for i, dm in enumerate(dates):
        date_label = dm.group(0)
        start = dm.end()
        end = dates[i+1].start() if i+1 < len(dates) else len(text)
        block = text[start:end]
        rx = re.compile(r"(?:^|\n)\s*(1[0-5]|[1-9])\s*\n+\s*#(\d{4,})\s*\n+\s*(\d{1,2}:\d{2}\s*(?:AM|PM))\b", re.I)
        for m in rx.finditer(block):
            number = int(m.group(1))
            draw = int(m.group(2))
            time_label = re.sub(r"\s+", " ", m.group(3)).upper()
            out[draw] = {"draw": draw, "number": number, "date": date_label, "time": time_label, "source": SOURCE_URL}
    return [out[k] for k in sorted(out)]

def norm(a):
    s = sum(a) or 1
    return [x/s for x in a]

def count_model(seq, start=0):
    a = [0.5]*15
    for x in seq[start:]: a[x-1] += 1
    return norm(a)

def transition_model(seq):
    a = [0.4]*15
    if not seq: return norm(a)
    last = seq[-1]
    for i in range(1, len(seq)):
        if seq[i-1] == last: a[seq[i]-1] += 1
    return norm(a)

def lag_model(seq, lag):
    a = [0.5]*15
    if len(seq) >= lag: a[seq[-lag]-1] += 4
    return norm(a)

def cycle_model(seq, cycle):
    a = [0.5]*15
    slot = len(seq) % cycle
    for i, x in enumerate(seq):
        if i % cycle == slot: a[x-1] += 1
    return norm(a)

def similarity_model(seq, length=4):
    a = [0.5]*15
    if len(seq) <= length: return norm(a)
    target = seq[-length:]
    matches = []
    for end in range(length, len(seq)):
        d = sum(1 for j in range(length) if seq[end-length+j] != target[j])
        matches.append((d, seq[end]))
    matches.sort()
    for i, (d, nxt) in enumerate(matches[:12]):
        a[nxt-1] += 1/(1+d+i*0.1)
    return norm(a)

def models(seq):
    return [
        ("overall", "Overall frequency", count_model(seq, 0)),
        ("recent", "Recent frequency", count_model(seq, max(0, len(seq)-24))),
        ("transition", "Transition / Markov", transition_model(seq)),
        ("lag7", "Lag 7", lag_model(seq, 7)),
        ("cycle8", "Cycle 8", cycle_model(seq, 8)),
        ("similarity", "Sequence similarity", similarity_model(seq)),
    ]

def top5(scores):
    return [i+1 for i, _ in sorted(enumerate(scores), key=lambda z: (-z[1], z[0]))[:5]]

def fresh_weights():
    return {k: 1.0 for k in ["overall","recent","transition","lag7","cycle8","similarity"]}

def predict(seq, weights):
    ms = []
    combined = [0.0]*15
    for mid, name, scores in models(seq):
        picks = top5(scores)
        w = max(0.1, float(weights.get(mid, 1.0)))
        for i, s in enumerate(scores): combined[i] += s*w
        ms.append({"id":mid,"name":name,"top5":picks,"weight":w})
    picks = top5(combined)
    return picks, ms

def update_weights(weights, model_rows, actual):
    for m in model_rows:
        cur = float(weights.get(m["id"], 1.0))
        weights[m["id"]] = max(0.1, min(10.0, cur*(1.10 if actual in m["top5"] else 0.95)))
    avg = sum(weights.values())/len(weights)
    for k in list(weights): weights[k] /= avg

def run_replay(draws):
    seq, weights, history = [], fresh_weights(), []
    warmup = min(40, max(20, int(len(draws)*0.08)))
    for row in draws:
        if len(seq) >= warmup:
            picks, ms = predict(seq, weights)
            hit = row["number"] in picks
            history.append({
                "draw": row["draw"], "top5": picks, "actual": row["number"], "hit5": hit,
                "modelResults": {m["id"]: row["number"] in m["top5"] for m in ms},
                "type": "historical_walk_forward"
            })
            update_weights(weights, ms, row["number"])
        seq.append(row["number"])
    return history, weights, warmup

def load_state():
    if STATE_PATH.exists():
        try: return json.loads(STATE_PATH.read_text())
        except Exception: pass
    return {"draws":[], "history":[], "weights":fresh_weights(), "pending":None, "warmup":40}

def main():
    state = load_state()
    fetched = parse_draws(fetch_html())
    if not fetched:
        raise RuntimeError("No draws parsed from source page")

    existing = {int(x["draw"]): x for x in state.get("draws", [])}
    first_run = len(existing) == 0

    if first_run:
        draws = fetched
        history, weights, warmup = run_replay(draws)
        seq = [x["number"] for x in draws]
        picks, ms = predict(seq, weights)
        pending = {"draw": max(x["draw"] for x in draws)+1, "top5":picks,
                   "modelTop5":{m["id"]:m["top5"] for m in ms},
                   "createdAt":datetime.now(timezone.utc).isoformat()}
        state.update({"draws":draws,"history":history,"weights":weights,"pending":pending,"warmup":warmup})
    else:
        new_rows = [r for r in fetched if r["draw"] not in existing]
        new_rows.sort(key=lambda x:x["draw"])
        draws = sorted(existing.values(), key=lambda x:x["draw"])
        seq = [x["number"] for x in draws]
        weights = state.get("weights") or fresh_weights()
        history = state.get("history") or []
        pending = state.get("pending")

        for row in new_rows:
            if pending and int(pending.get("draw",-1)) == row["draw"]:
                picks = pending["top5"]
                _, ms = predict(seq, weights)
                history.append({
                    "draw":row["draw"],"top5":picks,"actual":row["number"],
                    "hit5":row["number"] in picks,
                    "modelResults":{m["id"]:row["number"] in pending.get("modelTop5",{}).get(m["id"],[]) for m in ms},
                    "type":"automated_future_test",
                    "predictedAt":pending.get("createdAt"),
                    "scoredAt":datetime.now(timezone.utc).isoformat()
                })
                update_weights(weights, ms, row["number"])
            else:
                picks, ms = predict(seq, weights)
                history.append({
                    "draw":row["draw"],"top5":picks,"actual":row["number"],
                    "hit5":row["number"] in picks,
                    "modelResults":{m["id"]:row["number"] in m["top5"] for m in ms},
                    "type":"automatic_catchup"
                })
                update_weights(weights, ms, row["number"])
            draws.append(row); seq.append(row["number"])
            picks, ms = predict(seq, weights)
            pending = {"draw":row["draw"]+1,"top5":picks,
                       "modelTop5":{m["id"]:m["top5"] for m in ms},
                       "createdAt":datetime.now(timezone.utc).isoformat()}

        state.update({"draws":draws,"history":history,"weights":weights,"pending":pending})

    hist = state.get("history", [])
    successes = sum(1 for x in hist if x.get("hit5"))
    state["stats"] = {
        "evaluated":len(hist), "successes":successes, "misses":len(hist)-successes,
        "accuracy": successes/len(hist) if hist else 0,
        "randomTop5Baseline": 5/15
    }
    state["source"] = SOURCE_URL
    state["updatedAt"] = datetime.now(timezone.utc).isoformat()
    state["latestDraw"] = max((x["draw"] for x in state["draws"]), default=None)
    STATE_PATH.write_text(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()
