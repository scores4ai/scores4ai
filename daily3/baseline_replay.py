#!/usr/bin/env python3
import hashlib, json, random
from collections import Counter
from pathlib import Path

ARCHIVE=Path('daily3/archive.json')
OUT=Path('daily3/baseline_results.json')
WARMUP=200


def frequency_prediction(history):
    return [Counter(row['digits'][p] for row in history).most_common(1)[0][0] for p in range(3)]


def deterministic_random(archive_sha, sequence):
    seed=int(hashlib.sha256(f'{archive_sha}:{sequence}'.encode()).hexdigest()[:16],16)
    rng=random.Random(seed)
    return [rng.randrange(10) for _ in range(3)]


def box_match(pred, actual):
    return sorted(pred)==sorted(actual)


def score(stats,pred,actual):
    correct=[pred[i]==actual[i] for i in range(3)]
    stats['tested']+=1
    stats['exactHits']+=int(all(correct))
    stats['boxHits']+=int(box_match(pred,actual))
    stats['atLeastOnePosition']+=int(any(correct))
    for i,hit in enumerate(correct): stats['positionHits'][i]+=int(hit)


def main():
    archive=json.loads(ARCHIVE.read_text())
    draws=archive['draws']
    if len(draws)<=WARMUP: raise SystemExit('archive too small')
    names=('uniform_random','frequency_position','last_draw')
    stats={n:{'tested':0,'exactHits':0,'boxHits':0,'atLeastOnePosition':0,'positionHits':[0,0,0]} for n in names}
    samples=[]
    for i in range(WARMUP,len(draws)):
        history=draws[:i]
        actual=[int(x) for x in draws[i]['digits']]
        predictions={
            'uniform_random':deterministic_random(archive['sha256'],draws[i]['sequence']),
            'frequency_position':frequency_prediction(history),
            'last_draw':[int(x) for x in history[-1]['digits']],
        }
        frozen=hashlib.sha256(json.dumps({'target':draws[i]['sequence'],'predictions':predictions},sort_keys=True).encode()).hexdigest()
        for name,pred in predictions.items(): score(stats[name],pred,actual)
        if len(samples)<25:
            samples.append({'sequence':draws[i]['sequence'],'date':draws[i]['date'],'drawType':draws[i]['drawType'],'knownThrough':history[-1]['sequence'],'predictions':predictions,'actual':actual,'fingerprint':frozen})
    results=[]
    for name,s in stats.items():
        n=s['tested']
        results.append({
            'model':name,'tested':n,'exactHits':s['exactHits'],'exactAccuracy':s['exactHits']/n,
            'boxHits':s['boxHits'],'boxAccuracy':s['boxHits']/n,
            'atLeastOnePositionHits':s['atLeastOnePosition'],'atLeastOnePositionAccuracy':s['atLeastOnePosition']/n,
            'positionHits':s['positionHits'],'positionAccuracy':[x/n for x in s['positionHits']],
        })
    results.sort(key=lambda x:(-x['exactAccuracy'],-sum(x['positionAccuracy']),x['model']))
    payload={
        'version':'Daily 3 Baseline Replay Phase 1','archiveSha256':archive['sha256'],'archiveDrawCount':archive['drawCount'],
        'warmupDraws':WARMUP,'testedDraws':len(draws)-WARMUP,
        'integrity':{'futureDataAccess':False,'predictionsFrozenBeforeReveal':True,'uniformRandomDeterministic':True},
        'randomBaselines':{'exactStraight':0.001,'eachPosition':0.1,'atLeastOneCorrectPosition':0.271},
        'results':results,'sampleRecords':samples,
    }
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'))
    payload['resultSha256']=hashlib.sha256(raw.encode()).hexdigest()
    OUT.write_text(json.dumps(payload,indent=2))
    print(json.dumps({'tested':payload['testedDraws'],'results':results}))

if __name__=='__main__': main()
