#!/usr/bin/env python3
import json, math
from pathlib import Path

DATA=Path('research/clean_cashpop_archive.json')
OUT=Path('research/four_distinct_five_pool_v1_results.json')

def load_draws():
    d=json.loads(DATA.read_text())
    rows=d['draws'] if isinstance(d,dict) and 'draws' in d else d
    rows=sorted(rows,key=lambda r:int(r['draw']))
    return rows

def test_segment(rows,start,end):
    trials=hits=0
    expected=0.0
    by_pool={4:{'trials':0,'hits':0},5:{'trials':0,'hits':0}}
    examples=[]
    for i in range(max(start,5),end):
        prev4=[int(rows[j]['number']) for j in range(i-4,i)]
        if len(set(prev4))!=4:
            continue
        pool=[int(rows[j]['number']) for j in range(i-5,i)]
        uniq=set(pool)
        actual=int(rows[i]['number'])
        k=len(uniq)
        if k not in (4,5):
            continue
        hit=actual in uniq
        trials+=1; hits+=int(hit); expected+=k/15
        by_pool[k]['trials']+=1; by_pool[k]['hits']+=int(hit)
        if len(examples)<20:
            examples.append({'targetDraw':int(rows[i]['draw']),'last5':pool,'uniquePool':sorted(uniq),'poolSize':k,'actual':actual,'hit':hit})
    rate=hits/trials if trials else 0
    exp_rate=expected/trials if trials else 0
    # Poisson-binomial normal approximation z using per-case p=k/15
    var=0.0
    for k,info in by_pool.items():
        p=k/15
        var += info['trials']*p*(1-p)
    z=(hits-expected)/math.sqrt(var) if var>0 else 0
    return {'trials':trials,'hits':hits,'hitRate':rate,'expectedHits':expected,'expectedRate':exp_rate,'excessPercentagePoints':(rate-exp_rate)*100,'zApprox':z,'byPoolSize':by_pool,'examples':examples}

def main():
    rows=load_draws(); n=len(rows)
    discovery_end=int(n*.70); validation_end=int(n*.85)
    out={
      'hypothesis':'When last 4 draws are all distinct, the next draw is in the set of the last 5 draw values more often than chance.',
      'rule':'Trigger if draws t-4..t-1 are all different. Candidate set = unique values among t-5..t-1. Score whether draw t is in that set.',
      'datasetRows':n,
      'partitions':{'discovery':[0,discovery_end],'validation':[discovery_end,validation_end],'sealedTest':[validation_end,n]},
      'sealedTestOpened':False,
      'discovery':test_segment(rows,0,discovery_end),
      'validation':test_segment(rows,discovery_end,validation_end)
    }
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
