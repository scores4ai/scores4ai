#!/usr/bin/env python3
import hashlib,json,random
from collections import Counter
from pathlib import Path

ARCHIVE=Path('daily3/archive.json')
REAL=Path('daily3/baseline_results.json')
OUT=Path('daily3/monte_carlo_results.json')
WARMUP=200
SIMULATIONS=500


def pick(rng,weights):
    x=rng.random();s=0.0
    for digit,w in enumerate(weights):
        s+=w
        if x<=s:return digit
    return 9


def normalize(c):
    total=sum(c.values())
    return [c[d]/total for d in range(10)]


def evaluate(draws,seed):
    rng=random.Random(seed)
    counts=[Counter(row[p] for row in draws[:WARMUP]) for p in range(3)]
    models={n:{'exact':0,'positions':[0,0,0],'one':0} for n in ('uniform_random','frequency_position','last_draw')}
    prev=draws[WARMUP-1]
    for i in range(WARMUP,len(draws)):
        actual=draws[i]
        preds={
            'uniform_random':[rng.randrange(10) for _ in range(3)],
            'frequency_position':[counts[p].most_common(1)[0][0] for p in range(3)],
            'last_draw':prev,
        }
        for name,pred in preds.items():
            hits=[pred[p]==actual[p] for p in range(3)]
            models[name]['exact']+=int(all(hits));models[name]['one']+=int(any(hits))
            for p,h in enumerate(hits):models[name]['positions'][p]+=int(h)
        for p,d in enumerate(actual):counts[p][d]+=1
        prev=actual
    return models


def percentile(sorted_values,q):
    if not sorted_values:return 0
    idx=min(len(sorted_values)-1,max(0,round((len(sorted_values)-1)*q)))
    return sorted_values[idx]


def main():
    archive=json.loads(ARCHIVE.read_text());real=json.loads(REAL.read_text())
    rows=archive['draws'];n=len(rows);tested=n-WARMUP
    dist={}
    for draw_type in ('midday','evening'):
        dist[draw_type]=[]
        subset=[r for r in rows if r['drawType']==draw_type]
        for p in range(3):dist[draw_type].append(normalize(Counter(int(r['digits'][p]) for r in subset)))
    real_by={r['model']:r for r in real['results']}
    sim_metrics={name:{'exact':[],'one':[],'p0':[],'p1':[],'p2':[]} for name in real_by}
    best_exact=[]
    for sim in range(SIMULATIONS):
        seed=int(hashlib.sha256(f"{archive['sha256']}:{sim}".encode()).hexdigest()[:16],16)
        rng=random.Random(seed)
        synthetic=[[pick(rng,dist[row['drawType']][p]) for p in range(3)] for row in rows]
        result=evaluate(synthetic,seed^0xA5A5A5A5)
        best_exact.append(max(v['exact'] for v in result.values()))
        for name,v in result.items():
            sim_metrics[name]['exact'].append(v['exact']);sim_metrics[name]['one'].append(v['one'])
            for p in range(3):sim_metrics[name][f'p{p}'].append(v['positions'][p])
    report=[]
    for name,r in real_by.items():
        row={'model':name,'real':{'exactHits':r['exactHits'],'atLeastOnePositionHits':r['atLeastOnePositionHits'],'positionHits':r['positionHits']},'simulation':{}}
        for key,real_value in [('exact',r['exactHits']),('one',r['atLeastOnePositionHits']),('p0',r['positionHits'][0]),('p1',r['positionHits'][1]),('p2',r['positionHits'][2])]:
            vals=sorted(sim_metrics[name][key]);ge=sum(v>=real_value for v in vals)
            row['simulation'][key]={'median':percentile(vals,.5),'p95':percentile(vals,.95),'p99':percentile(vals,.99),'empiricalP':(ge+1)/(SIMULATIONS+1)}
        report.append(row)
    real_best=max(r['exactHits'] for r in real['results']);best_exact.sort()
    out={'version':'Daily 3 Monte Carlo Reality Check Phase 1','archiveSha256':archive['sha256'],'simulations':SIMULATIONS,'drawsPerSimulation':n,'testedPerSimulation':tested,'syntheticRule':'Independent digits sampled from real midday/evening position-specific marginal frequencies; same replay and model-selection process applied.','integrity':{'realResultsReadOnly':True,'simulationSeedsDeterministic':True,'futureDataAccess':False},'multipleModelRealityCheck':{'realBestExactHits':real_best,'simulatedBestMedian':percentile(best_exact,.5),'simulatedBestP95':percentile(best_exact,.95),'simulatedBestP99':percentile(best_exact,.99),'empiricalP':(sum(v>=real_best for v in best_exact)+1)/(SIMULATIONS+1)},'models':report}
    raw=json.dumps(out,sort_keys=True,separators=(',',':'));out['resultSha256']=hashlib.sha256(raw.encode()).hexdigest();OUT.write_text(json.dumps(out,indent=2));print(json.dumps(out))

if __name__=='__main__':main()
