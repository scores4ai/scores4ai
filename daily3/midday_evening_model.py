#!/usr/bin/env python3
import hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

ARCHIVE=Path('daily3/archive.json')
BASELINES=Path('daily3/baseline_results.json')
OUT=Path('daily3/midday_evening_results.json')
WARMUP_DAYS=100


def top_digit(counter, fallback):
    return counter.most_common(1)[0][0] if counter else fallback


def main():
    archive=json.loads(ARCHIVE.read_text())
    baselines=json.loads(BASELINES.read_text())
    rows=archive['draws']
    by_date=defaultdict(dict)
    for row in rows:
        by_date[row['date']][row['drawType']]=row
    days=[d for d in sorted(by_date) if 'midday' in by_date[d] and 'evening' in by_date[d]]
    if len(days)<=WARMUP_DAYS:
        raise SystemExit('not enough paired days')

    # For each position, learn P(evening digit | same-day midday digit).
    transition=[[defaultdict(Counter) for _ in range(1)][0] for _ in range(3)]
    global_evening=[Counter() for _ in range(3)]

    for date in days[:WARMUP_DAYS]:
        m=by_date[date]['midday']['digits']; e=by_date[date]['evening']['digits']
        for p in range(3):
            transition[p][int(m[p])][int(e[p])]+=1
            global_evening[p][int(e[p])]+=1

    stats={'tested':0,'exactHits':0,'atLeastOnePositionHits':0,'positionHits':[0,0,0]}
    samples=[]
    for date in days[WARMUP_DAYS:]:
        m=[int(x) for x in by_date[date]['midday']['digits']]
        actual=[int(x) for x in by_date[date]['evening']['digits']]
        prediction=[]
        for p in range(3):
            fallback=top_digit(global_evening[p],0)
            prediction.append(top_digit(transition[p][m[p]],fallback))

        frozen=hashlib.sha256(json.dumps({'date':date,'midday':m,'prediction':prediction},sort_keys=True).encode()).hexdigest()
        hits=[prediction[p]==actual[p] for p in range(3)]
        stats['tested']+=1
        stats['exactHits']+=int(all(hits))
        stats['atLeastOnePositionHits']+=int(any(hits))
        for p,h in enumerate(hits): stats['positionHits'][p]+=int(h)

        if len(samples)<25:
            samples.append({'date':date,'midday':m,'prediction':prediction,'actualEvening':actual,'fingerprint':frozen})

        # Update only after the evening result is revealed.
        for p in range(3):
            transition[p][m[p]][actual[p]]+=1
            global_evening[p][actual[p]]+=1

    n=stats['tested']
    result={
        'model':'midday_to_evening_position_transition',
        'testedEveningDraws':n,
        'exactHits':stats['exactHits'],
        'exactAccuracy':stats['exactHits']/n,
        'atLeastOnePositionHits':stats['atLeastOnePositionHits'],
        'atLeastOnePositionAccuracy':stats['atLeastOnePositionHits']/n,
        'positionHits':stats['positionHits'],
        'positionAccuracy':[x/n for x in stats['positionHits']],
    }
    out={
        'version':'Daily 3 Midday-to-Evening Test Phase 1',
        'archiveSha256':archive['sha256'],
        'pairedDays':len(days),
        'warmupDays':WARMUP_DAYS,
        'integrity':{
            'futureDataAccess':False,
            'predictionFrozenAfterMiddayBeforeEveningReveal':True,
            'updatesOnlyAfterEveningReveal':True,
        },
        'result':result,
        'referenceBaselines':baselines['results'],
        'samples':samples,
    }
    raw=json.dumps(out,sort_keys=True,separators=(',',':'))
    out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps(result))

if __name__=='__main__':
    main()
