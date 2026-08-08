#!/usr/bin/env python3
import json, math
from pathlib import Path

DATA=Path('research/clean_cashpop_archive.json')
OUT=Path('research/four_distinct_five_recent_v1_results.json')


def load_rows():
    d=json.loads(DATA.read_text())
    return d['draws'] if isinstance(d,dict) and 'draws' in d else d


def poisson_binomial_tail(ps,k):
    # DP exact tail for non-identical Bernoulli probabilities.
    dp=[1.0]
    for p in ps:
        nd=[0.0]*(len(dp)+1)
        for i,v in enumerate(dp):
            nd[i]+=v*(1-p)
            nd[i+1]+=v*p
        dp=nd
    return sum(dp[k:])


def run_partition(rows,start,end,name):
    tests=[]
    for t in range(max(start,5),end):
        last4=[int(rows[i]['number']) for i in range(t-4,t)]
        if len(set(last4))<4:
            continue
        last5=[int(rows[i]['number']) for i in range(t-5,t)]
        candidates=sorted(set(last5))
        actual=int(rows[t]['number'])
        p=len(candidates)/15.0
        tests.append({
            'targetIndex':t,
            'draw':rows[t].get('draw'),
            'last5':last5,
            'uniqueCandidates':candidates,
            'candidateCount':len(candidates),
            'actual':actual,
            'hit':actual in candidates,
            'randomP':p
        })
    n=len(tests); h=sum(x['hit'] for x in tests)
    expected=sum(x['randomP'] for x in tests)
    acc=h/n if n else 0
    baseline=expected/n if n else 0
    pval=poisson_binomial_tail([x['randomP'] for x in tests],h) if n else None
    return {
        'partition':name,'tests':n,'hits':h,'accuracy':acc,
        'averageRandomBaseline':baseline,'expectedHitsUnderRandom':expected,
        'excessPercentagePoints':(acc-baseline)*100,
        'oneSidedExactPoissonBinomialPValue':pval,
        'candidateCount4':sum(x['candidateCount']==4 for x in tests),
        'candidateCount5':sum(x['candidateCount']==5 for x in tests),
        'sample':tests[:10]
    }


def main():
    rows=load_rows(); n=len(rows)
    a=int(n*.70); b=int(n*.85)
    discovery=run_partition(rows,0,a,'discovery')
    validation=run_partition(rows,a,b,'validation')
    # Sealed 15% deliberately untouched.
    out={
      'experiment':'Four distinct -> previous five contain next v1',
      'rule':'Trigger only when the immediately previous four draws are all distinct. Candidate pool is the set of the immediately previous five draw values. Score whether the next draw is in that set.',
      'dataRows':n,
      'split':{'discoveryEnd':a,'validationEnd':b,'sealedStart':b,'sealedRows':n-b},
      'sealedStatus':'UNTOUCHED',
      'discovery':discovery,
      'validation':validation
    }
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
