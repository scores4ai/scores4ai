#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
import cloud_engine as engine

base = Path(__file__).parent
state_path = base / "cloud_state.json"
seed_path = base / "seed_draws.json"

try:
    state = json.loads(state_path.read_text())
except Exception:
    state = {}

if state.get("draws"):
    raise SystemExit(0)

pairs = json.loads(seed_path.read_text())
draws = [
    {"draw": int(d), "number": int(n), "date": date, "time": time, "source": "user-seed"}
    for d, n, date, time in pairs
]
draws.sort(key=lambda x: x["draw"])
history, weights, warmup = engine.run_replay(draws)
seq = [x["number"] for x in draws]
picks, models = engine.predict(seq, weights)
now = datetime.now(timezone.utc).isoformat()
successes = sum(1 for row in history if row.get("hit5"))
state = {
    "draws": draws,
    "history": history,
    "weights": weights,
    "pending": {
        "draw": draws[-1]["draw"] + 1,
        "top5": picks,
        "modelTop5": {m["id"]: m["top5"] for m in models},
        "createdAt": now
    },
    "warmup": warmup,
    "stats": {
        "evaluated": len(history),
        "successes": successes,
        "misses": len(history) - successes,
        "accuracy": successes / len(history) if history else 0,
        "randomTop5Baseline": 5 / 15
    },
    "updatedAt": now,
    "latestDraw": draws[-1]["draw"],
    "source": "User seed plus automated cash-pop.com updates"
}
state_path.write_text(json.dumps(state, indent=2))
print(f"Seeded {len(draws)} draws; next #{state['pending']['draw']} picks {picks}")
