#!/usr/bin/env python3
"""Leakage-safe pseudo-live replay over the immutable Cash Pop archive.

At step t, models receive draws [0:t), freeze predictions for draw t, then and
only then is draw t revealed and scored. The output contains enough hashes and
indices to reproduce and audit every step.
"""
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE = Path('apx/full_archive.json')
OUT = Path('apx/replay_state.json')
WARMUP = 100
MAX_STEPS = 250  # first proof run; later championship can use the full archive
NUMBERS = tuple(range(1, 16))


def now():
    return datetime.now(timezone.utc).isoformat()


def top5(scores):
    return [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:5]]


def frequency(seq, window=None):
    sample = seq[-window:] if window else seq
    c = Counter(sample)
    return top5({n: c[n] + 0.5 for n in NUMBERS})


def gap_model(seq):
    gaps = {}
    rev = list(reversed(seq))
    for n in NUMBERS:
        try:
            gaps[n] = rev.index(n) + 1
        except ValueError:
            gaps[n] = len(seq) + 1
    return top5(gaps)


def markov1(seq):
    if not seq:
        return list(NUMBERS[:5])
    last = seq[-1]
    c = Counter()
    for a, b in zip(seq, seq[1:]):
        if a == last:
            c[b] += 1
    if not c:
        return frequency(seq, 60)
    return top5({n: c[n] + 0.25 for n in NUMBERS})


def cycle(seq, period=8):
    slot = len(seq) % period
    c = Counter(x for i, x in enumerate(seq) if i % period == slot)
    return top5({n: c[n] + 0.25 for n in NUMBERS})


def lag_vote(seq):
    scores = {n: 0.0 for n in NUMBERS}
    for lag, weight in ((2, 3.0), (3, 2.5), (5, 2.0), (8, 1.5), (13, 1.0)):
        if len(seq) >= lag:
            scores[seq[-lag]] += weight
    return top5(scores)


MODELS = {
    'frequency_all': lambda s: frequency(s),
    'frequency_24': lambda s: frequency(s, 24),
    'frequency_60': lambda s: frequency(s, 60),
    'gap_longest': gap_model,
    'markov_1': markov1,
    'cycle_8': lambda s: cycle(s, 8),
    'cycle_20': lambda s: cycle(s, 20),
    'lag_vote': lag_vote,
}


def fingerprint(archive_sha, target_draw, known_count, predictions):
    body = json.dumps({
        'archiveSha': archive_sha,
        'targetDraw': target_draw,
        'knownCount': known_count,
        'predictions': predictions,
    }, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(body.encode()).hexdigest()


def wilson(hits, tested, z=1.959963984540054):
    if tested == 0:
        return [0.0, 1.0]
    p = hits / tested
    d = 1 + z*z/tested
    center = (p + z*z/(2*tested)) / d
    margin = z * math.sqrt((p*(1-p) + z*z/(4*tested))/tested) / d
    return [max(0.0, center-margin), min(1.0, center+margin)]


def main():
    archive = json.loads(ARCHIVE.read_text())
    draws = archive['draws']
    if len(draws) <= WARMUP:
        raise SystemExit('Archive is too small for replay warm-up')
    end = min(len(draws), WARMUP + MAX_STEPS)
    records = []
    stats = {name: {'tested': 0, 'hits': 0} for name in MODELS}

    for index in range(WARMUP, end):
        known_rows = draws[:index]
        known_seq = [int(r['number']) for r in known_rows]
        target = draws[index]

        # Freeze predictions before target is read for scoring.
        predictions = {name: [int(x) for x in fn(known_seq)] for name, fn in MODELS.items()}
        for name, picks in predictions.items():
            if len(picks) != 5 or len(set(picks)) != 5 or any(n not in NUMBERS for n in picks):
                raise SystemExit(f'Invalid prediction from {name} at draw {target["draw"]}: {picks}')
        frozen = fingerprint(archive['sha256'], int(target['draw']), len(known_rows), predictions)

        # Reveal exactly one authentic result only after the freeze.
        actual = int(target['number'])
        results = {}
        for name, picks in predictions.items():
            hit = actual in picks
            stats[name]['tested'] += 1
            stats[name]['hits'] += int(hit)
            results[name] = {'hit5': hit}

        records.append({
            'step': index - WARMUP + 1,
            'targetIndex': index,
            'targetDraw': int(target['draw']),
            'knownThroughDraw': int(known_rows[-1]['draw']),
            'knownCount': len(known_rows),
            'frozenBeforeReveal': True,
            'predictionFingerprint': frozen,
            'predictions': predictions,
            'revealedActual': actual,
            'results': results,
        })

    leaderboard = []
    for name, row in stats.items():
        tested, hits = row['tested'], row['hits']
        accuracy = hits / tested if tested else 0.0
        leaderboard.append({
            'model': name,
            'tested': tested,
            'hits': hits,
            'misses': tested - hits,
            'accuracy': accuracy,
            'excessOverRandom': accuracy - (5/15),
            'confidence95': wilson(hits, tested),
        })
    leaderboard.sort(key=lambda x: (-x['accuracy'], x['model']))

    record_payload = json.dumps(records, sort_keys=True, separators=(',', ':'))
    out = {
        'version': 'Historical Replay Phase 1',
        'createdAt': now(),
        'archiveSha256': archive['sha256'],
        'archiveDrawCount': archive['drawCount'],
        'warmupDraws': WARMUP,
        'replaySteps': len(records),
        'firstTestedDraw': records[0]['targetDraw'],
        'lastTestedDraw': records[-1]['targetDraw'],
        'randomTop5Baseline': 5/15,
        'integrity': {
            'futureDataAccess': False,
            'oneDrawRevealedPerStep': True,
            'predictionsFrozenBeforeReveal': True,
            'recordSha256': hashlib.sha256(record_payload.encode()).hexdigest(),
            'rule': 'At target index t, every model receives only archive rows with index < t. Predictions are fingerprinted before archive row t is scored.',
        },
        'leaderboard': leaderboard,
        'records': records,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({
        'steps': out['replaySteps'],
        'firstTestedDraw': out['firstTestedDraw'],
        'lastTestedDraw': out['lastTestedDraw'],
        'winner': leaderboard[0]['model'],
        'winnerAccuracy': leaderboard[0]['accuracy'],
        'recordSha256': out['integrity']['recordSha256'],
    }))


if __name__ == '__main__':
    main()
