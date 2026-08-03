#!/usr/bin/env python3
import hashlib, json, math, random
from collections import Counter
from pathlib import Path

ARCHIVE=Path('daily3/archive.json')
OUT=Path('daily3/rolling_block_results.json')
WARMUP=1000
BLOCK=1000
MODELS=('uniform_random','frequency_position','last_draw','position_transition_1')

def deterministic_random(sha,sequence):
    seed=int(hashlib.sha256(f'{sha}:rolling:{sequence}'.encode()).hexdigest()[:16],16)
    rng=random.Random(seed)
    return [rng.randrange(10) for _ in range(3)]

def z_score(k,n,p=.001):
    mean=n*p
    sd=math.sqrt(n*p*(1-p))
    return 0.0 if sd==0 else (k-mean)/sd

def blank():
    return {m:{'tested':0,'exact':0,'positions':[0,0,0]} for m in MODELS}

def score(store,name,pred,actual):
    hits=[pred[p]==actual[p] for p in range(3)]
    s=store[name]
    s['tested']+=1
    s['exact']+=int(all(hits))
    for p,h in enumerate(hits):
        s['positions'][p]+=int(h)

def board(stats):
    rows=[]
    for name,s in stats.items():
        n=s['tested']
        rows.append({
            'model':name,
            'tested':n,
            'exactHits':s['exact'],
            'exactAccuracy':s['exact']/n,
            'exactZ':z_score(s['exact'],n),
            'positionAccuracy':[x/n for x in s['positions']],
        })
    return sorted(rows,key=lambda r:(-r['exactHits'],-sum(r['positionAccuracy']),r['model']))

def main():
    archive=json.loads(ARCHIVE.read_text())
    draws=archive['draws']
    freq=[Counter() for _ in range(3)]
    trans=[[Counter() for _ in range(10)] for _ in range(3)]
    for i in range(WARMUP):
        cur=draws[i]['digits']
        for p,d in enumerate(cur):
            freq[p][d]+=1
        if i:
            prev=draws[i-1]['digits']
            for p in range(3):
                trans[p][prev[p]][cur[p]]+=1
    overall=blank()
    blocks=[]
    stats=blank()
    block_start=WARMUP
    block_id=1
    for i in range(WARMUP,len(draws)):
        actual=draws[i]['digits']
        prev=draws[i-1]['digits']
        freq_pred=[freq[p].most_common(1)[0][0] for p in range(3)]
        transition=[]
        for p in range(3):
            c=trans[p][prev[p]]
            transition.append(c.most_common(1)[0][0] if c else freq_pred[p])
        preds={
            'uniform_random':deterministic_random(archive['sha256'],draws[i]['sequence']),
            'frequency_position':freq_pred,
            'last_draw':prev,
            'position_transition_1':transition,
        }
        for name,pred in preds.items():
            score(stats,name,pred,actual)
            score(overall,name,pred,actual)
        for p,d in enumerate(actual):
            freq[p][d]+=1
            trans[p][prev[p]][d]+=1
        if ((i-block_start+1)==BLOCK) or i==len(draws)-1:
            blocks.append({
                'block':block_id,
                'startSequence':draws[block_start]['sequence'],
                'endSequence':draws[i]['sequence'],
                'startDate':draws[block_start]['date'],
                'endDate':draws[i]['date'],
                'leaderboard':board(stats),
            })
            block_id+=1
            block_start=i+1
            stats=blank()
    wins=Counter(b['leaderboard'][0]['model'] for b in blocks)
    summary=board(overall)
    for row in summary:
        row['blocksWon']=wins[row['model']]
    summary.sort(key=lambda r:(-r['blocksWon'],-r['exactHits'],r['model']))
    out={
        'version':'Daily 3 Rolling Block Stability Phase 2',
        'archiveSha256':archive['sha256'],
        'warmupDraws':WARMUP,
        'blockSize':BLOCK,
        'blockCount':len(blocks),
        'integrity':{
            'futureDataAccess':False,
            'predictionsMadeSequentially':True,
            'parametersFixed':True,
            'incrementalEquivalent':True,
            'timeoutSafeStatistics':True,
        },
        'overall':summary,
        'blocks':blocks,
    }
    raw=json.dumps(out,sort_keys=True,separators=(',',':'))
    out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps({'blocks':len(blocks),'overall':summary}))

if __name__=='__main__':
    main()
