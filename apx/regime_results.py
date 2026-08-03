#!/usr/bin/env python3
import json, math
from collections import Counter, defaultdict
from pathlib import Path
import importlib.util

ARCHIVE=Path('apx/full_archive.json')
OUT=Path('apx/regime_results.json')
WARMUP=200
STEPS=5000

spec=importlib.util.spec_from_file_location('replay','apx/historical_replay.py')
replay=importlib.util.module_from_spec(spec); spec.loader.exec_module(replay)
MODELS=replay.MODELS


def entropy(seq):
    if not seq:return 0.0
    c=Counter(seq); n=len(seq)
    h=-sum((v/n)*math.log(v/n,15) for v in c.values())
    return h

def regime(seq):
    r20=seq[-20:]; r50=seq[-50:]
    ent=entropy(r50)
    repeats=sum(a==b for a,b in zip(r20,r20[1:]))
    odd=sum(x%2 for x in r20)
    high=sum(x>=8 for x in r20)
    gaps=[]
    rev=list(reversed(seq))
    for n in range(1,16):
        try:gaps.append(rev.index(n)+1)
        except ValueError:gaps.append(len(seq)+1)
    gap_avg=sum(gaps)/15
    return {
      'entropy':'low' if ent<0.82 else ('mid' if ent<0.93 else 'high'),
      'repeat':'high' if repeats>=3 else ('mid' if repeats>=1 else 'low'),
      'parity':'odd-heavy' if odd>=13 else ('even-heavy' if odd<=7 else 'balanced'),
      'band':'high-heavy' if high>=13 else ('low-heavy' if high<=7 else 'balanced'),
      'gap':'stretched' if gap_avg>=15 else ('compressed' if gap_avg<=9 else 'normal')
    }

def main():
    a=json.loads(ARCHIVE.read_text()); draws=a['draws']; end=min(len(draws),WARMUP+STEPS)
    cells=defaultdict(lambda:defaultdict(lambda:{'tested':0,'hits':0}))
    overall={m:{'tested':0,'hits':0} for m in MODELS}
    for i in range(WARMUP,end):
        seq=[int(r['number']) for r in draws[:i]]
        actual=int(draws[i]['number'])
        rg=regime(seq)
        preds={m:fn(seq) for m,fn in MODELS.items()}
        for m,p in preds.items():
            hit=actual in p; overall[m]['tested']+=1; overall[m]['hits']+=int(hit)
            for feature,value in rg.items():
                key=f'{feature}:{value}'; cells[key][m]['tested']+=1; cells[key][m]['hits']+=int(hit)
    regimes=[]
    for key,models in sorted(cells.items()):
        rows=[]
        for m,s in models.items():
            acc=s['hits']/s['tested'] if s['tested'] else 0
            rows.append({'model':m,**s,'accuracy':acc,'excessOverRandom':acc-1/3})
        rows.sort(key=lambda x:(-x['accuracy'],x['model']))
        regimes.append({'regime':key,'tested':rows[0]['tested'] if rows else 0,'winner':rows[0] if rows else None,'leaderboard':rows})
    overall_rows=[]
    for m,s in overall.items():
        acc=s['hits']/s['tested']; overall_rows.append({'model':m,**s,'accuracy':acc,'excessOverRandom':acc-1/3})
    overall_rows.sort(key=lambda x:(-x['accuracy'],x['model']))
    out={'version':'Regime Results Phase 1','archiveSha256':a['sha256'],'warmup':WARMUP,'steps':end-WARMUP,'futureDataAccess':False,'featuresComputedBeforeReveal':True,'overall':overall_rows,'regimes':regimes}
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps({'steps':out['steps'],'overallWinner':overall_rows[0],'regimeCount':len(regimes),'topRegimes':[{'regime':r['regime'],'winner':r['winner']} for r in regimes[:5]]}))
if __name__=='__main__':main()
