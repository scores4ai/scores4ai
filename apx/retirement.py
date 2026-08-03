#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('apx/state.json')
BASELINE = 5 / 15
MIN_TESTS = 400
MIN_ACTIVE = 20
MAX_RETIRE_FRACTION = 0.25
LIFETIME_MARGIN = 0.015
ROLLING_MARGIN = 0.05


def now():
    return datetime.now(timezone.utc).isoformat()


def should_retire(model):
    tested = int(model.get('tested', 0))
    accuracy = float(model.get('accuracy', 0))
    rolling = float(model.get('rolling50', 0))
    return (
        tested >= MIN_TESTS
        and accuracy < BASELINE - LIFETIME_MARGIN
        and rolling < BASELINE - ROLLING_MARGIN
    )


def borda_prediction(active):
    scores = {n: 0.0 for n in range(1, 16)}
    support = {n: 0 for n in range(1, 16)}
    for model in active:
        weight = max(0.05, float(model.get('weight', 1.0)))
        for rank, number in enumerate(model.get('top5', [])[:5]):
            number = int(number)
            scores[number] += weight * (5 - rank)
            support[number] += 1
    top5 = sorted(scores, key=lambda n: (-scores[n], -support[n], n))[:5]
    return top5, scores, support


def main():
    state = json.loads(STATE.read_text())
    board = list(state.get('leaderboard', []))
    previous = state.get('modelRetirement', {})
    previous_retired = set(previous.get('retiredNames', []))

    eligible = [m for m in board if should_retire(m)]
    eligible.sort(key=lambda m: (m.get('rolling50', 0), m.get('accuracy', 0), m.get('weight', 0)))

    max_retire = min(
        max(0, len(board) - MIN_ACTIVE),
        max(1, int(len(board) * MAX_RETIRE_FRACTION)),
    )
    retired_names = {m['name'] for m in eligible[:max_retire]}

    # A previously retired model may return only after both metrics recover to baseline.
    for model in board:
        name = model['name']
        if name in previous_retired:
            recovered = (
                float(model.get('accuracy', 0)) >= BASELINE
                and float(model.get('rolling50', 0)) >= BASELINE
            )
            if not recovered and len(retired_names) < max_retire:
                retired_names.add(name)

    # Enforce the active floor even if old retirement records are excessive.
    if len(board) - len(retired_names) < MIN_ACTIVE:
        ranked_retired = sorted(
            [m for m in board if m['name'] in retired_names],
            key=lambda m: (m.get('rolling50', 0), m.get('accuracy', 0), m.get('weight', 0)),
            reverse=True,
        )
        while len(board) - len(retired_names) < MIN_ACTIVE and ranked_retired:
            retired_names.remove(ranked_retired.pop(0)['name'])

    active = []
    retired = []
    for model in board:
        model['status'] = 'retired' if model['name'] in retired_names else 'active'
        model['votingWeight'] = 0.0 if model['status'] == 'retired' else float(model.get('weight', 1.0))
        (retired if model['status'] == 'retired' else active).append(model)

    top5, scores, support = borda_prediction(active)
    next_draw = int(state.get('nextDraw', int(state.get('latestDraw', 0)) + 1))
    frozen_at = now()
    fingerprint = f"apx-{next_draw}-" + '-'.join(map(str, top5))

    state['top5'] = top5
    state['modelCount'] = len(active)
    state['totalModelCount'] = len(board)
    state['leaderboard'] = active + retired
    state['pendingPrediction'] = {
        **state.get('pendingPrediction', {}),
        'draw': next_draw,
        'top5': top5,
        'predictedAt': frozen_at,
        'fingerprint': fingerprint,
        'modelCount': len(active),
        'totalModelCount': len(board),
        'immutable': True,
        'retirementFiltered': True,
    }
    state['modelRetirement'] = {
        'enabled': True,
        'evaluatedAt': frozen_at,
        'activeCount': len(active),
        'retiredCount': len(retired),
        'retiredNames': sorted(retired_names),
        'newlyRetired': sorted(retired_names - previous_retired),
        'reactivated': sorted(previous_retired - retired_names),
        'minimumTests': MIN_TESTS,
        'minimumActiveModels': MIN_ACTIVE,
        'maximumRetiredPerCycle': max_retire,
        'lifetimeThreshold': BASELINE - LIFETIME_MARGIN,
        'rolling50Threshold': BASELINE - ROLLING_MARGIN,
        'reactivationRule': 'Lifetime and rolling-50 accuracy must both recover to the random baseline.',
        'rule': 'A model stops voting only after at least 400 tests, lifetime accuracy below 31.8%, and rolling-50 accuracy below 28.3%. History is retained.',
    }
    state['ensembleDiagnostics'] = {
        'method': 'retirement-filtered weighted Borda vote',
        'numberScores': {str(n): scores[n] for n in scores},
        'modelSupport': {str(n): support[n] for n in support},
    }
    state['version'] = 'APX Phase 1.6'
    state['updatedAt'] = frozen_at
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({
        'active': len(active),
        'retired': len(retired),
        'newlyRetired': sorted(retired_names - previous_retired),
        'top5': top5,
        'nextDraw': next_draw,
    }))


if __name__ == '__main__':
    main()
