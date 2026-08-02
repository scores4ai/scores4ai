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
}


def now():
    return datetime.now(timezone.utc).isoformat()


def norm(values):
    total = sum(values) or 1.0
    return [x / total for x in values]


def count(seq, start=0):
    scores = [0.5] * 15
    for value in seq[start:]:
        scores[value - 1] += 1
    return norm(scores)


def markov(seq):
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


def ranked(scores):
    return [i + 1 for i, _ in sorted(enumerate(scores), key=lambda item: (-item[1], item[0]))]


def top5(scores):
    return ranked(scores)[:5]


def fresh_model_weights():
    return {key: 1.0 for key in MODEL_NAMES}


def fresh_expert_weights():
    return {str(h): 1.0 for h in HORIZONS}


def self_learner(seq, expert_weights):
    expert_scores = {}
    combined = [0.0] * 15
    expert_top5 = {}
    for horizon in HORIZONS:
        scores = count(seq, max(0, len(seq) - horizon))
        key = str(horizon)
        expert_scores[key] = scores
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
        "markov1": markov(seq),
        "lag7": lag(seq, 7),
        "cycle8": cycle(seq, 8),
        "selfLearner": adaptive,
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
    picks = diversify(combined, recent_predictions or [])
    return picks, model_top5, expert_top5


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
    seq = []
    history = []
    model_weights = fresh_model_weights()
    expert_weights = fresh_expert_weights()
    recent_predictions = []
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


def main():
    base = load_json(BASE_STATE, {})
    draws = list(base.get("draws", []))[-MAX_DRAWS:]
    if not draws:
        raise RuntimeError("The original live state has no draw data")

    old = load_json(STATE, {})
    old_pending = old.get("pending")
    old_latest = int(old.get("latestDraw", 0) or 0)
    live = [row for row in old.get("history", []) if row.get("type") == "automated_future_test"]

    historical, model_weights, expert_weights, warmup, recent_predictions = replay(draws)
    new_rows = [row for row in draws if int(row["draw"]) > old_latest]
    for row in sorted(new_rows, key=lambda item: item["draw"]):
        if old_pending and int(old_pending.get("draw", -1)) == int(row["draw"]):
            picks = old_pending.get("top5", [])
            model_top5 = old_pending.get("modelTop5", {})
            live.append({
                "draw": row["draw"],
                "top5": picks,
                "actual": row["number"],
                "hit5": row["number"] in picks,
                "modelResults": {key: row["number"] in model_top5.get(key, []) for key in MODEL_NAMES},
                "type": "automated_future_test",
                "predictedAt": old_pending.get("createdAt"),
                "scoredAt": now(),
            })

    seq = [row["number"] for row in draws]
    recent_live = [row.get("top5", []) for row in live[-10:]]
    diversity_context = recent_live if recent_live else recent_predictions[-10:]
    picks, model_top5, expert_top5 = predict(seq, model_weights, expert_weights, diversity_context)
    latest = max(int(row["draw"]) for row in draws)
    pending = {
        "draw": latest + 1,
        "top5": picks,
        "modelTop5": model_top5,
        "selfLearnerExpertTop5": expert_top5,
        "createdAt": now(),
        "feedControlled": True,
        "experiment": "one additional self-learning model",
    }

    history = historical + live
    successes = sum(1 for row in history if row.get("hit5"))
    live_successes = sum(1 for row in live if row.get("hit5"))
    self_results = [row.get("modelResults", {}).get("selfLearner") for row in history]
    self_evaluated = sum(result is not None for result in self_results)
    self_successes = sum(result is True for result in self_results)

    state = {
        "draws": draws,
        "history": history,
        "weights": model_weights,
        "selfLearner": {
            "name": MODEL_NAMES["selfLearner"],
            "expertWeights": expert_weights,
            "horizons": list(HORIZONS),
            "evaluated": self_evaluated,
            "successes": self_successes,
            "accuracy": self_successes / self_evaluated if self_evaluated else 0,
        },
        "pending": pending,
        "warmup": warmup,
        "latestDraw": latest,
        "seedCount": len(draws),
        "feed": "isolated experiment reading verified v0 state",
        "source": "v0/cloud_state.json",
        "updatedAt": now(),
        "modelNames": MODEL_NAMES,
        "stats": {
            "evaluated": len(history),
            "successes": successes,
            "misses": len(history) - successes,
            "accuracy": successes / len(history) if history else 0,
            "liveEvaluated": len(live),
            "liveSuccesses": live_successes,
            "liveMisses": len(live) - live_successes,
            "liveAccuracy": live_successes / len(live) if live else 0,
            "randomTop5Baseline": 1 / 3,
        },
    }
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({"latestDraw": latest, "nextDraw": latest + 1, "prediction": picks, "selfLearnerWeight": model_weights["selfLearner"]}))


if __name__ == "__main__":
    main()
