#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_STATE = Path(__file__).parents[1] / "v0" / "cloud_state.json"
STATE = Path(__file__).with_name("cloud_state.json")
MAX_DRAWS = 600
HORIZONS = (12, 24, 48, 96)
MODEL_NAMES = {
    "overall": "Overall frequency",
    "recent24": "Recent 24",
    "recent60": "Recent 60",
    "markov1": "Markov 1",
    "lag7": "Lag 7",
    "cycle8": "Cycle 8",
    "selfLearner": "Self-learning horizon model",
    "decayFrequency": "Exponentially decayed frequency",
    "markov2": "Second-order Markov",
    "gapHazard": "Gap and return hazard",
    "sequenceTwin": "Historical sequence twin",
    "runState": "Run-state transition model",
    "cycleBank": "Multi-period cycle bank",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def norm(values):
    total = sum(values) or 1.0
    return [x / total for x in values]


def ranked(scores):
    return [i + 1 for i, _ in sorted(enumerate(scores), key=lambda item: (-item[1], item[0]))]


def top5(scores):
    return ranked(scores)[:5]


def count(seq, start=0):
    scores = [0.5] * 15
    for value in seq[start:]:
        scores[value - 1] += 1
    return norm(scores)


def markov1(seq):
    scores = [0.4] * 15
    if seq:
        last = seq[-1]
        for i in range(1, len(seq)):
            if seq[i - 1] == last:
                scores[seq[i] - 1] += 1
    return norm(scores)


def lag(seq, n):
    scores = [0.5] * 15
    if len(seq) >= n:
        scores[seq[-n] - 1] += 4
    return norm(scores)


def cycle(seq, n):
    scores = [0.5] * 15
    slot = len(seq) % n
    for i, value in enumerate(seq):
        if i % n == slot:
            scores[value - 1] += 1
    return norm(scores)


def decay_frequency(seq, decay=0.965):
    scores = [0.35] * 15
    weight = 1.0
    for value in reversed(seq):
        scores[value - 1] += weight
        weight *= decay
    return norm(scores)


def markov2(seq):
    scores = [0.35] * 15
    if len(seq) >= 2:
        a, b = seq[-2], seq[-1]
        matches = 0
        for i in range(2, len(seq)):
            if seq[i - 2] == a and seq[i - 1] == b:
                scores[seq[i] - 1] += 1.5
                matches += 1
        if not matches:
            return markov1(seq)
    return norm(scores)


def gap_hazard(seq):
    scores = [0.35] * 15
    positions = {n: [] for n in range(1, 16)}
    for i, value in enumerate(seq):
        positions[value].append(i)
    end = len(seq) - 1
    for number in range(1, 16):
        seen = positions[number]
        current_gap = len(seq) if not seen else end - seen[-1]
        gaps = [seen[i] - seen[i - 1] for i in range(1, len(seen))]
        mean_gap = sum(gaps) / len(gaps) if gaps else 15.0
        scores[number - 1] += min(4.0, current_gap / max(mean_gap, 1.0))
        if current_gap <= 2:
            scores[number - 1] += 0.35
    return norm(scores)


def sequence_twin(seq):
    scores = [0.35] * 15
    found = 0
    for length, weight in ((6, 3.0), (5, 2.4), (4, 1.8), (3, 1.2)):
        if len(seq) <= length:
            continue
        suffix = seq[-length:]
        for i in range(length, len(seq)):
            if seq[i - length:i] == suffix:
                scores[seq[i] - 1] += weight
                found += 1
        if found >= 3:
            break
    return norm(scores) if found else decay_frequency(seq, 0.94)


def run_state(seq):
    scores = [0.35] * 15
    if not seq:
        return norm(scores)
    last = seq[-1]
    state_repeat = len(seq) >= 2 and seq[-2] == last
    parity = last % 2
    band = 0 if last <= 5 else 1 if last <= 10 else 2
    for i in range(2, len(seq)):
        prev = seq[i - 1]
        prev_repeat = seq[i - 2] == prev
        prev_band = 0 if prev <= 5 else 1 if prev <= 10 else 2
        if prev_repeat == state_repeat and prev % 2 == parity and prev_band == band:
            scores[seq[i] - 1] += 1.0
    return norm(scores)


def cycle_bank(seq):
    periods = (3, 4, 5, 6, 7, 9, 11, 13, 17, 23)
    combined = [0.0] * 15
    for period in periods:
        scores = cycle(seq, period)
        recent_hits = 0
        tests = 0
        start = max(period + 1, len(seq) - 90)
        for end in range(start, len(seq)):
            recent_hits += seq[end] in top5(cycle(seq[:end], period))
            tests += 1
        weight = (recent_hits + 2.0) / (tests + 6.0)
        for i, score in enumerate(scores):
            combined[i] += score * weight
    return norm(combined)


def fresh_model_weights():
    return {key: 1.0 for key in MODEL_NAMES}


def fresh_expert_weights():
    return {str(h): 1.0 for h in HORIZONS}


def self_learner(seq, expert_weights):
    combined = [0.0] * 15
    expert_top5 = {}
    for horizon in HORIZONS:
        key = str(horizon)
        scores = count(seq, max(0, len(seq) - horizon))
        expert_top5[key] = top5(scores)
        weight = max(0.05, float(expert_weights.get(key, 1.0)))
        for i, score in enumerate(scores):
            combined[i] += score * weight
    return norm(combined), expert_top5


def models(seq, expert_weights):
    adaptive, expert_top5 = self_learner(seq, expert_weights)
    return {
        "overall": count(seq),
        "recent24": count(seq, max(0, len(seq) - 24)),
        "recent60": count(seq, max(0, len(seq) - 60)),
        "markov1": markov1(seq),
        "lag7": lag(seq, 7),
        "cycle8": cycle(seq, 8),
        "selfLearner": adaptive,
        "decayFrequency": decay_frequency(seq),
        "markov2": markov2(seq),
        "gapHazard": gap_hazard(seq),
        "sequenceTwin": sequence_twin(seq),
        "runState": run_state(seq),
        "cycleBank": cycle_bank(seq),
    }, expert_top5


def diversify(combined, recent_predictions):
    exposure = [0] * 15
    for picks in recent_predictions[-10:]:
        for number in picks:
            if 1 <= int(number) <= 15:
                exposure[int(number) - 1] += 1
    adjusted = list(combined)
    for i, seen in enumerate(exposure):
        adjusted[i] *= 1.0 - min(0.15, seen * 0.015)
    order = ranked(adjusted)
    candidate = order[:5]
    previous = list(recent_predictions[-1]) if recent_predictions else []
    if previous and set(candidate) == set(previous):
        fifth = adjusted[candidate[-1] - 1]
        sixth_number = order[5]
        sixth = adjusted[sixth_number - 1]
        if fifth <= 0 or (fifth - sixth) / fifth < 0.08:
            candidate[-1] = sixth_number
    return candidate


def predict(seq, model_weights, expert_weights, recent_predictions=None):
    rows, expert_top5 = models(seq, expert_weights)
    combined = [0.0] * 15
    model_top5 = {}
    for key, scores in rows.items():
        model_top5[key] = top5(scores)
        weight = max(0.05, float(model_weights.get(key, 1.0)))
        for i, score in enumerate(scores):
            combined[i] += score * weight
    return diversify(combined, recent_predictions or []), model_top5, expert_top5


def update_model_weights(weights, model_top5, actual):
    for key in MODEL_NAMES:
        current = float(weights.get(key, 1.0))
        multiplier = 1.075 if actual in model_top5.get(key, []) else 0.965
        weights[key] = max(0.05, min(20.0, current * multiplier))
    average = sum(weights.values()) / len(weights)
    for key in weights:
        weights[key] /= average


def update_expert_weights(weights, expert_top5, actual):
    for key in weights:
        current = float(weights.get(key, 1.0))
        multiplier = 1.06 if actual in expert_top5.get(key, []) else 0.97
        weights[key] = max(0.05, min(20.0, current * multiplier))
    average = sum(weights.values()) / len(weights)
    for key in weights:
        weights[key] /= average


def replay(draws):
    seq, history, recent_predictions = [], [], []
    model_weights, expert_weights = fresh_model_weights(), fresh_expert_weights()
    warmup = min(60, max(30, int(len(draws) * 0.10)))
    for row in draws:
        if len(seq) >= warmup:
            picks, model_top5, expert_top5 = predict(seq, model_weights, expert_weights, recent_predictions)
            history.append({
                "draw": row["draw"],
                "top5": picks,
                "actual": row["number"],
                "hit5": row["number"] in picks,
                "modelResults": {key: row["number"] in values for key, values in model_top5.items()},
                "selfLearnerExperts": {key: row["number"] in values for key, values in expert_top5.items()},
                "type": "historical_walk_forward",
            })
            recent_predictions.append(picks)
            update_model_weights(model_weights, model_top5, row["number"])
            update_expert_weights(expert_weights, expert_top5, row["number"])
        seq.append(row["number"])
    return history, model_weights, expert_weights, warmup, recent_predictions


def load_json(path, fallback):
    try:
        return json.loads(path.read_text())
    except Exception:
        return fallback


def model_scorecard(history):
    card = {}
    for key, name in MODEL_NAMES.items():
        values = [row.get("modelResults", {}).get(key) for row in history]
        evaluated = sum(value is not None for value in values)
        successes = sum(value is True for value in values)
        card[key] = {
            "name": name,
            "evaluated": evaluated,
            "successes": successes,
            "misses": evaluated - successes,
            "accuracy": successes / evaluated if evaluated else 0,
        }
    return card


def unique_live_rows(rows):
    by_draw = {}
    for row in rows:
        if row.get("type") == "automated_future_test" and row.get("draw") is not None:
            by_draw[int(row["draw"])] = row
    return [by_draw[key] for key in sorted(by_draw)]


def main():
    base = load_json(BASE_STATE, {})
    draws = list(base.get("draws", []))[-MAX_DRAWS:]
    if not draws:
        raise RuntimeError("The original live state has no draw data")

    old = load_json(STATE, {})
    old_pending = old.get("pending")
    old_latest = int(old.get("latestDraw", 0) or 0)

    legacy_live = [row for row in old.get("history", []) if row.get("type") == "automated_future_test"]
    live = unique_live_rows(list(old.get("liveHistory", [])) + legacy_live)
    live_draw_ids = {int(row["draw"]) for row in live}

    historical, model_weights, expert_weights, warmup, recent_predictions = replay(draws)

    new_rows = [row for row in draws if int(row["draw"]) > old_latest]
    for row in sorted(new_rows, key=lambda item: item["draw"]):
        draw_id = int(row["draw"])
        if draw_id in live_draw_ids:
            continue
        if old_pending and int(old_pending.get("draw", -1)) == draw_id:
            picks = old_pending.get("top5", [])
            model_top5 = old_pending.get("modelTop5", {})
            live.append({
                "draw": draw_id,
                "top5": picks,
                "actual": row["number"],
                "hit5": row["number"] in picks,
                "modelResults": {key: row["number"] in model_top5.get(key, []) for key in MODEL_NAMES},
                "type": "automated_future_test",
                "predictedAt": old_pending.get("createdAt"),
                "scoredAt": now(),
            })
            live_draw_ids.add(draw_id)

    live = unique_live_rows(live)
    seq = [row["number"] for row in draws]
    recent_live = [row.get("top5", []) for row in live[-10:]]
    context = recent_live if recent_live else recent_predictions[-10:]
    picks, model_top5, expert_top5 = predict(seq, model_weights, expert_weights, context)
    latest = max(int(row["draw"]) for row in draws)

    pending = {
        "draw": latest + 1,
        "top5": picks,
        "modelTop5": model_top5,
        "selfLearnerExpertTop5": expert_top5,
        "createdAt": now(),
        "feedControlled": True,
        "experiment": "six additional independent walk-forward models",
    }

    historical_successes = sum(1 for row in historical if row.get("hit5"))
    live_successes = sum(1 for row in live if row.get("hit5"))

    state = {
        "draws": draws,
        "history": historical,
        "historicalHistory": historical,
        "liveHistory": live,
        "weights": model_weights,
        "modelScorecard": model_scorecard(historical),
        "selfLearner": {
            "name": MODEL_NAMES["selfLearner"],
            "expertWeights": expert_weights,
            "horizons": list(HORIZONS),
        },
        "pending": pending,
        "warmup": warmup,
        "latestDraw": latest,
        "seedCount": len(draws),
        "feed": "isolated experiment reading verified v0 state",
        "source": "v0/cloud_state.json",
        "updatedAt": now(),
        "modelNames": MODEL_NAMES,
        "integrity": {
            "duplicateScoringRemoved": True,
            "historicalAndLiveSeparated": True,
            "uniqueLiveDraws": len(live),
        },
        "stats": {
            "evaluated": len(historical),
            "successes": historical_successes,
            "misses": len(historical) - historical_successes,
            "accuracy": historical_successes / len(historical) if historical else 0,
            "liveEvaluated": len(live),
            "liveSuccesses": live_successes,
            "liveMisses": len(live) - live_successes,
            "liveAccuracy": live_successes / len(live) if live else 0,
            "randomTop5Baseline": 1 / 3,
        },
    }
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({
        "latestDraw": latest,
        "nextDraw": latest + 1,
        "prediction": picks,
        "historicalEvaluated": len(historical),
        "liveEvaluated": len(live),
        "duplicateScoringRemoved": True,
    }))


if __name__ == "__main__":
    main()
