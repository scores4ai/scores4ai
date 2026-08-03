#!/usr/bin/env python3
import hashlib, json, math, random
from collections import Counter
from pathlib import Path

ARCHIVE = Path('daily3/archive.json')
OUT = Path('daily3/rolling_block_results.json')
WARMUP = 1000
BLOCK = 1000
MODELS = ('uniform_random','frequency_position','last_draw','position_transition_1')


def frequency_prediction(history):
    return [Counter(row['digits'][p] for row in history).most_common(1)[0][0] for p in range(3)]


def transition_prediction(history):
    pred=[]
    for p in range(3):
        last=history[-1]['digits'][p]
        c=Counter()
        for a,b in zip(history,history[1:]):
            if a['digits'][p]==last:
                c[b['digits'][p]]+=1
        if c:
            pred.append(c.most_common(1)[0][0])
        else:
            pred.append(Counter(r['digits'][p] for r in history).most_common(1)[0][0])
    return pred


def deterministic_random(sha, sequence):
    seed=int(hashlib.sha256(f'{sha}:rolling:{sequence}'.encode()).hexdigest()[:16],16)
    rng=random.Random(seed)
    return [rng.randrange(10) for _ in range(3)]


def binom_upper_tail(k,n,p):
    # Exact upper-tail probability for small expected counts.
    return min(1.0, sum(math.comb(n,i)*(p**i)*((1-p)**(n-i)) for i in range(k,n+1)))


def main():
    archive=json.loads(ARCHIVE.read_text())
    draws=archive['draws']
    blocks=[]
    overall={m:{'tested':0,'exact':0,'positions':[0,0,0]} for m in MODELS}
    start=WARMUP
    block_id=1
    while start < len(draws):
        end=min(len(draws),start+BLOCK)
        stats={m:{'tested':0,'exact':0,'positions':[0,0,0]} for m in MODELS}
        for i in range(start,end):
            history=draws[:i]
            actual=draws[i]['digits']
            preds={
                'uniform_random':deterministic_random(archive['sha256'],draws[i]['sequence']),
                'frequency_position':frequency_prediction(history),
                'last_draw':history[-1]['digits'],
                'position_transition_1':transition_prediction(history),
            }
            for name,pred in preds.items():
                hits=[pred[p]==actual[p] for p in range(3)]
                stats[name]['tested']+=1
                stats[name]['exact']+=int(all(hits))
                for p,h in enumerate(hits): stats[name]['positions'][p]+=int(h)
                overall[name]['tested']+=1
                overall[name]['exact']+=int(all(hits))
                for p,h in enumerate(hits): overall[name]['positions'][p]+=int(h)
        board=[]
        for name,s in stats.items():
            n=s['tested']
            board.append({
                'model':name,'tested':n,'exactHits':s['exact'],'exactAccuracy':s['exact']/n,
                'exactPUpper':binom_upper_tail(s['exact'],n,0.001),
                'positionAccuracy':[x/n for x in s['positions']],
            })
        board.sort(key=lambda r:(-r['exactHits'],-sum(r['positionAccuracy']),r['model']))
        blocks.append({
            'block':block_id,'startSequence':draws[start]['sequence'],'endSequence':draws[end-1]['sequence'],
            'startDate':draws[start]['date'],'endDate':draws[end-1]['date'],'leaderboard':board,
        })
        start=end; block_id+=1
    summary=[]
    wins=Counter()
    for b in blocks: wins[b['leaderboard'][0]['model']]+=1
    for name,s in overall.items():
        n=s['tested']
        summary.append({
            'model':name,'tested':n,'exactHits':s['exact'],'exactAccuracy':s['exact']/n,
            'exactPUpper':binom_upper_tail(s['exact'],n,0.001),
            'positionAccuracy':[x/n for x in s['positions']],
            'blocksWon':wins[name],
        })
    summary.sort(key=lambda r:(-r['blocksWon'],-r['exactHits'],r['model']))
    out={
        'version':'Daily 3 Rolling Block Stability Phase 1','archiveSha256':archive['sha256'],
        'warmupDraws':WARMUP,'blockSize':BLOCK,'blockCount':len(blocks),
        'integrity':{'futureDataAccess':False,'predictionsMadeSequentially':True,'parametersFixed':True},
        'overall':summary,'blocks':blocks,
    }
    raw=json.dumps(out,sort_keys=True,separators=(',',':'))
    out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps({'blocks':len(blocks),'overall':summary}))

if __name__=='__main__': main()
