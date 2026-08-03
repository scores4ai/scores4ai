#!/usr/bin/env python3
import json, math, hashlib
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('apx/state.json')
SOURCE = Path('v0/cloud_state.json')
NUMBERS = range(1, 16)
BASELINE = 5 / 15
GENERATION_TESTS = 25
MAX_ACTIVE = 12


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def norm(scores):
    total = sum(scores.values()) or 1.0
    return {n: scores.get(n, 0.0) / total for n in NUMBERS}


def picks(scores):
    return [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:5]]


def wilson(hits, tested, z=1.959963984540054):
    if tested <= 0:
        return [0.0, 1.0]
    p = hits / tested
    d = 1 + z * z / tested
    c = (p + z * z / (2 * tested)) / d
    m = z * math.sqrt((p * (1 - p) + z * z / (4 * tested)) / tested) / d
    return [max(0.0, c - m), min(1.0, c + m)]


def binomial_tail(hits, tested, p=BASELINE):
    if tested <= 0:
        return 1.0
    logs = [
        math.lgamma(tested + 1) - math.lgamma(k + 1) - math.lgamma(tested - k + 1)
        + k * math.log(p) + (tested - k) * math.log1p(-p)
        for k in range(hits, tested + 1)
    ]
    mx = max(logs)
    return min(1.0, math.exp(mx) * sum(math.exp(x - mx) for x in logs))


def gap_scores(seq, threshold, boost):
    scores = {n: 1.0 for n in NUMBERS}
    rev = list(reversed(seq))
    for n in NUMBERS:
        try:
            gap = rev.index(n) + 1
        except ValueError:
            gap = len(seq) + 1
        if gap >= threshold:
            scores[n] += boost * (gap / max(1, threshold))
    return norm(scores)


def parity_scores(seq, lookback, boost):
    scores = {n: 1.0 for n in NUMBERS}
    tail = seq[-lookback:]
    if len(tail) == lookback and all(x % 2 == tail[0] % 2 for x in tail):
        target = 1 - tail[0] % 2
        for n in NUMBERS:
            if n % 2 == target:
                scores[n] += boost
    return norm(scores)


def band_scores(seq, lookback, strength):
    scores = {n: 1.0 for n in NUMBERS}
    tail = seq[-lookback:]
    if tail:
        avg = sum(tail) / len(tail)
        for n in NUMBERS:
            scores[n] += strength * abs(n - avg) / 8
    return norm(scores)


def repeat_scores(seq, window, boost):
    scores = {n: 1.0 for n in NUMBERS}
    recent = set(seq[-window:])
    for n in NUMBERS:
        if n not in recent:
            scores[n] += boost
    return norm(scores)


def score_gene(seq, gene):
    family = gene['family']
    if family == 'parity':
        return parity_scores(seq, int(gene['lookback']), float(gene['boost']))
    if family == 'gap':
        return gap_scores(seq, int(gene['threshold']), float(gene['boost']))
    if family == 'band':
        return band_scores(seq, int(gene['lookback']), float(gene['strength']))
    if family == 'repeat':
        return repeat_scores(seq, int(gene['window']), float(gene['boost']))
    return norm({n: 1.0 for n in NUMBERS})


def gene_id(gene):
    raw = json.dumps(gene, sort_keys=True, separators=(',', ':'))
    return hashlib.sha1(raw.encode()).hexdigest()[:10]


def child(parent, changes, generation, index):
    gene = dict(parent['gene'])
    gene.update(changes)
    return {
        'id': f"g{generation}-{gene_id(gene)}-{index}",
        'name': mutation_name(gene),
        'generation': generation,
        'parentId': parent.get('id'),
        'parentName': parent.get('name'),
        'gene': gene,
        'bornAt': utcnow(),
        'status': 'testing'
    }


def mutation_name(gene):
    family = gene['family']
    if family == 'parity':
        return f"parity_l{gene['lookback']}_b{gene['boost']}"
    if family == 'gap':
        return f"gap_t{gene['threshold']}_b{gene['boost']}"
    if family == 'band':
        return f"band_l{gene['lookback']}_s{gene['strength']}"
    return f"repeat_w{gene['window']}_b{gene['boost']}"


def seed_population():
    parents = [
        {'id': 'seed-parity-3', 'name': 'parity_flip_3', 'gene': {'family': 'parity', 'lookback': 3, 'boost': 2.5}},
        {'id': 'seed-parity-4', 'name': 'parity_flip_4', 'gene': {'family': 'parity', 'lookback': 4, 'boost': 2.5}},
        {'id': 'seed-gap-18', 'name': 'gap_threshold_18', 'gene': {'family': 'gap', 'threshold': 18, 'boost': 2.0}},
        {'id': 'seed-gap-25', 'name': 'gap_threshold_25', 'gene': {'family': 'gap', 'threshold': 25, 'boost': 2.0}},
        {'id': 'seed-band-5', 'name': 'band_reversion_5', 'gene': {'family': 'band', 'lookback': 5, 'strength': 1.0}},
        {'id': 'seed-repeat-4', 'name': 'repeat_suppression_4', 'gene': {'family': 'repeat', 'window': 4, 'boost': 2.0}},
    ]
    children = []
    i = 0
    for parent in parents:
        gene = parent['gene']
        family = gene['family']
        variants = []
        if family == 'parity':
            variants = [
                {'lookback': max(2, gene['lookback'] - 1), 'boost': 2.0},
                {'lookback': min(6, gene['lookback'] + 1), 'boost': 3.0},
            ]
        elif family == 'gap':
            variants = [
                {'threshold': max(10, gene['threshold'] - 4), 'boost': 1.5},
                {'threshold': min(32, gene['threshold'] + 4), 'boost': 2.5},
            ]
        elif family == 'band':
            variants = [
                {'lookback': 3, 'strength': 0.75},
                {'lookback': 8, 'strength': 1.5},
            ]
        elif family == 'repeat':
            variants = [
                {'window': 2, 'boost': 1.5},
                {'window': 7, 'boost': 2.5},
            ]
        for changes in variants:
            i += 1
            children.append(child(parent, changes, 1, i))
    unique = {}
    for item in children:
        unique[gene_id(item['gene'])] = item
    return list(unique.values())[:MAX_ACTIVE]


def fitness(hits, tested, gene, lineage_penalty=0.0):
    # Bayesian shrinkage prevents tiny lucky samples from dominating.
    posterior = (hits + BASELINE * 30) / (tested + 30)
    complexity = 0.002 * max(0, len(gene) - 2)
    return posterior - complexity - lineage_penalty


def score_pending(previous, draws):
    evolution = previous.get('evolution') or {}
    history = list(evolution.get('history') or [])
    seen = {(x.get('candidateId'), int(x.get('draw', -1))) for x in history}
    draw_map = {int(x['draw']): x for x in draws}
    for pred in evolution.get('pending', []):
        target = int(pred.get('draw', -1))
        cid = pred.get('candidateId')
        if target in draw_map and (cid, target) not in seen:
            actual = int(draw_map[target]['number'])
            top5 = [int(x) for x in pred.get('top5', [])]
            history.append({
                'candidateId': cid,
                'candidateName': pred.get('candidateName'),
                'generation': pred.get('generation'),
                'draw': target,
                'top5': top5,
                'actual': actual,
                'hit5': actual in top5,
                'predictedAt': pred.get('predictedAt'),
                'scoredAt': utcnow(),
                'type': 'evolution_live_forward'
            })
            seen.add((cid, target))
    return history[-10000:]


def maybe_reproduce(population, history, generation):
    if not population:
        return seed_population(), 1, False
    stats = []
    for item in population:
        rows = [x for x in history if x.get('candidateId') == item['id']]
        tested = len(rows)
        hits = sum(1 for x in rows if x.get('hit5'))
        stats.append((fitness(hits, tested, item['gene']), tested, hits, item))
    if min(x[1] for x in stats) < GENERATION_TESTS:
        return population, generation, False

    stats.sort(key=lambda x: (-x[0], -x[1]))
    parents = [x[3] for x in stats[:4]]
    next_generation = generation + 1
    children = []
    idx = 0
    for parent in parents:
        g = parent['gene']
        family = g['family']
        mutations = []
        if family == 'parity':
            mutations = [
                {'lookback': max(2, int(g['lookback']) - 1), 'boost': round(max(1.0, float(g['boost']) - 0.5), 2)},
                {'lookback': min(7, int(g['lookback']) + 1), 'boost': round(min(4.0, float(g['boost']) + 0.5), 2)},
                {'boost': round(min(4.0, float(g['boost']) + 0.25), 2)},
            ]
        elif family == 'gap':
            mutations = [
                {'threshold': max(8, int(g['threshold']) - 3), 'boost': round(max(1.0, float(g['boost']) - 0.25), 2)},
                {'threshold': min(36, int(g['threshold']) + 3), 'boost': round(min(4.0, float(g['boost']) + 0.25), 2)},
                {'boost': round(min(4.0, float(g['boost']) + 0.5), 2)},
            ]
        elif family == 'band':
            mutations = [
                {'lookback': max(3, int(g['lookback']) - 1), 'strength': round(max(0.5, float(g['strength']) - 0.25), 2)},
                {'lookback': min(10, int(g['lookback']) + 1), 'strength': round(min(2.5, float(g['strength']) + 0.25), 2)},
                {'strength': round(min(2.5, float(g['strength']) + 0.5), 2)},
            ]
        else:
            mutations = [
                {'window': max(1, int(g['window']) - 1), 'boost': round(max(1.0, float(g['boost']) - 0.25), 2)},
                {'window': min(10, int(g['window']) + 1), 'boost': round(min(4.0, float(g['boost']) + 0.25), 2)},
                {'boost': round(min(4.0, float(g['boost']) + 0.5), 2)},
            ]
        for changes in mutations:
            idx += 1
            children.append(child(parent, changes, next_generation, idx))

    unique = {}
    for item in children:
        unique[gene_id(item['gene'])] = item
    return list(unique.values())[:MAX_ACTIVE], next_generation, True


def summarize(population, history, seq):
    rows = []
    for item in population:
        tests = [x for x in history if x.get('candidateId') == item['id']]
        tested = len(tests)
        hits = sum(1 for x in tests if x.get('hit5'))
        accuracy = hits / tested if tested else 0.0
        lo, hi = wilson(hits, tested)
        pv = binomial_tail(hits, tested)
        current = picks(score_gene(seq, item['gene']))
        rows.append({
            **item,
            'tested': tested,
            'hits': hits,
            'misses': tested - hits,
            'accuracy': accuracy,
            'excess': accuracy - BASELINE,
            'fitness': fitness(hits, tested, item['gene']),
            'pValue': pv,
            'confidence95': {'low': lo, 'high': hi},
            'currentTop5': current,
            'testsUntilReproduction': max(0, GENERATION_TESTS - tested)
        })
    rows.sort(key=lambda x: (-x['fitness'], -x['tested'], x['name']))
    return rows


def main():
    state = json.loads(STATE.read_text())
    source = json.loads(SOURCE.read_text())
    draws = source.get('draws', [])
    seq = [int(x['number']) for x in draws]
    latest = max(int(x['draw']) for x in draws)

    history = score_pending(state, draws)
    old = state.get('evolution') or {}
    population = list(old.get('population') or [])
    generation = int(old.get('generation') or 0)
    population, generation, reproduced = maybe_reproduce(population, history, generation)

    now = utcnow()
    pending = []
    for item in population:
        top5 = picks(score_gene(seq, item['gene']))
        pending.append({
            'candidateId': item['id'],
            'candidateName': item['name'],
            'generation': item['generation'],
            'draw': latest + 1,
            'top5': top5,
            'predictedAt': now,
            'immutable': True
        })

    candidates = summarize(population, history, seq)
    state['evolution'] = {
        'version': 1,
        'isolatedFromTournament': True,
        'affectsLivePrediction': False,
        'generation': generation,
        'populationSize': len(population),
        'generationTestsRequired': GENERATION_TESTS,
        'lastReproducedAt': now if reproduced else old.get('lastReproducedAt'),
        'reproducedThisRun': reproduced,
        'population': population,
        'candidates': candidates,
        'pending': pending,
        'history': history,
        'selectionRule': 'After every candidate receives 25 immutable live tests, the four highest shrinkage-adjusted fitness scores reproduce. Parameter mutations remain isolated from the live ensemble.',
        'safetyRule': 'No evolutionary candidate can vote in APX or graduate automatically.'
    }
    state['version'] = 'APX Phase 1.5'
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({
        'latest': latest,
        'generation': generation,
        'population': len(population),
        'reproduced': reproduced,
        'isolated': True,
        'nextDraw': latest + 1
    }))


if __name__ == '__main__':
    main()
