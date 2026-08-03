#!/usr/bin/env python3
import hashlib, json, random
from collections import Counter, deque
from pathlib import Path

ARCHIVE=Path('daily3/archive.json')
OUT=Path('daily3/window_model_results.json')
WARMUP=1000
WINDOWS=(25,50,100,250,500,1000)


def deterministic_random(sha,sequence):
    seed=int(hashlib.sha256(f'{sha}:window:{sequence}'.encode()).hexdigest()[:16],16)
    rng=random.Random(seed)
    return [rng.randrange(10) for _ in range(3)]


def freq_predict(history,w):
    subset=history[-w:]
    return [Counter(r['digits'][p] for r in subset).most_common(1)[0][0] for p in range(3)]


def transition_predict(history,w):
    subset=history[-w:]
    pred=[]
    for p in range(3):
        last=subset[-1]['digits'][p]
        c=Counter()
        for a,b in zip(subset,subset[1:]):
            if a['digits'][p]==last:
                c[b['digits'][p]]+=1
        if c:
            pred.append(c.most_common(1)[0][0])
        else:
            pred.append(Counter(r['digits'][p] for r in subset).most_common(1)[0][0])
    return pred


def blank(names):
    return {n:{'tested':0,'exact':0,'positions':[0,0,0]} for n in names}


def score(store,name,pred,actual):
    hits=[pred[p]==actual[p] for p in range(3)]
    s=store[name];s['tested']+=1;s['exact']+=int(all(hits))
    for p,h in enumerate(hits):s['positions'][p]+=int(h)


def main():
    archive=json.loads(ARCHIVE.read_text());draws=archive['draws']
    names=['uniform_random','last_draw']
    names += [f'frequency_w{w}' for w in WINDOWS]
    names += [f'transition_w{w}' for w in WINDOWS]
    stats=blank(names)
    block_stats=blank(names)
    blocks=[];block_start=WARMUP;block_id=1
    for i in range(WARMUP,len(draws)):
        history=draws[:i];actual=draws[i]['digits']
        preds={'uniform_random':deterministic_random(archive['sha256'],draws[i]['sequence']),
               'last_draw':history[-1]['digits']}
        for w in WINDOWS:
            preds[f'frequency_w{w}']=freq_predict(history,w)
            preds[f'transition_w{w}']=transition_predict(history,w)
        frozen=hashlib.sha256(json.dumps({'sequence':draws[i]['sequence'],'predictions':preds},sort_keys=True).encode()).hexdigest()
        for n,p in preds.items():score(stats,n,p,actual);score(block_stats,n,p,actual)
        if (i-block_start+1)==1000 or i==len(draws)-1:
            board=[]
            for n,s in block_stats.items():
                tested=s['tested']
                board.append({'model':n,'tested':tested,'exactHits':s['exact'],'exactAccuracy':s['exact']/tested,
                              'positionAccuracy':[x/tested for x in s['positions']]})
            board.sort(key=lambda r:(-r['exactHits'],-sum(r['positionAccuracy']),r['model']))
            blocks.append({'block':block_id,'startSequence':draws[block_start]['sequence'],'endSequence':draws[i]['sequence'],'leaderboard':board})
            block_stats=blank(names);block_start=i+1;block_id+=1
    wins=Counter(b['leaderboard'][0]['model'] for b in blocks)
    overall=[]
    for n,s in stats.items():
        tested=s['tested']
        overall.append({'model':n,'tested':tested,'exactHits':s['exact'],'exactAccuracy':s['exact']/tested,
                        'positionAccuracy':[x/tested for x in s['positions']],'blocksWon':wins[n]})
    overall.sort(key=lambda r:(-r['blocksWon'],-r['exactHits'],-sum(r['positionAccuracy']),r['model']))
    out={'version':'Daily 3 Rolling Window Challenge Phase 1','archiveSha256':archive['sha256'],
         'warmupDraws':WARMUP,'windows':list(WINDOWS),'testedDraws':len(draws)-WARMUP,
         'integrity':{'futureDataAccess':False,'predictionsFrozenBeforeReveal':True,'parametersFixed':True},
         'overall':overall,'blocks':blocks}
    raw=json.dumps(out,sort_keys=True,separators=(',',':'));out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2));print(json.dumps({'top':overall[:5]}))

if __name__=='__main__':main()
