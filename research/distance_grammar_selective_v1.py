#!/usr/bin/env python3
import json, math, hashlib
from collections import Counter, defaultdict
from pathlib import Path

STATE=Path('v0/cloud_state.json')
OUT=Path('research/distance_grammar_selective_v1_results.json')
WARMUP=260
MAX_LAG=15
BASELINE=3/15
MIN_CONTEXT_CASES=8
# LOCKED BEFORE RESULTS: activate only when the exact 3-distance context's
# past-only Laplace-smoothed hit rate is >= 30% with >=8 historical cases.
THRESHOLD=0.30

def prev_distance(seq,idx):
    v=seq[idx]
    for d in range(1,MAX_LAG+1):
        j=idx-d
        if j<0: break
        if seq[j]==v:return d
    return 0

def distances(seq): return [prev_distance(seq,i) for i in range(len(seq))]

def fallback(prefix,used):
    c=Counter(prefix[-120:])
    return [n for n,_ in sorted(c.items(),key=lambda kv:(kv[1],-kv[0]),reverse=True) if n not in used]

def predict(prefix,ds=None):
    ds=ds or distances(prefix); ctx=tuple(ds[-3:]); scores=Counter()
    for i in range(3,len(ds)):
        hist=tuple(ds[i-3:i]); sim=sum((3-j) for j in range(3) if hist[j]==ctx[j])
        if sim:
            nxt=ds[i]
            if 1<=nxt<=MAX_LAG:scores[prefix[-nxt]]+=sim
    picks=[n for n,_ in scores.most_common()]
    for n in fallback(prefix,set(picks)):
        picks.append(n)
        if len(picks)>=3:break
    return picks[:3]

def gate(prefix):
    ds=distances(prefix); ctx=tuple(ds[-3:]); cases=hits=0
    # For each prior occurrence of current exact context, generate the model
    # using only data available BEFORE that historical target, then score it.
    for target in range(40,len(prefix)):
        if tuple(ds[target-3:target])!=ctx: continue
        hist=prefix[:target]
        ps=predict(hist)
        cases+=1; hits+=int(prefix[target] in ps)
    # Laplace/Beta(1,4) shrinkage centered at 20% baseline.
    rate=(hits+1)/(cases+5)
    return cases>=MIN_CONTEXT_CASES and rate>=THRESHOLD,cases,hits,rate,ctx

def binom_tail(k,n,p):
    return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))

def main():
    state=json.loads(STATE.read_text()); draws=sorted(state['draws'],key=lambda x:int(x['draw']))
    nums=[int(x['number']) for x in draws]; records=[]; contamination=[]; chain='GENESIS'
    for t in range(WARMUP,len(nums)):
        prefix=nums[:t]; active,cases,ph,rate,ctx=gate(prefix); picks=predict(prefix)
        # anti-leak mutation: suffix is never supplied; assert identical gate/picks
        mutated=nums[:t]+[15 if x!=15 else 1 for x in nums[t:]]
        ma,mc,mh,mr,mctx=gate(mutated[:t]); mp=predict(mutated[:t])
        if (active,cases,ph,round(rate,12),ctx,picks)!=(ma,mc,mh,round(mr,12),mctx,mp): contamination.append(int(draws[t]['draw']))
        if active:
            actual=nums[t]; hit=actual in picks
            records.append({'draw':int(draws[t]['draw']),'trainingThrough':int(draws[t-1]['draw']),'context':ctx,'pastCases':cases,'pastHits':ph,'pastSmoothedRate':rate,'picks':picks,'actual':actual,'hit':hit})
            chain=hashlib.sha256(f'{chain}|{draws[t]["draw"]}|{ctx}|{picks}'.encode()).hexdigest()[:20]
    n=len(records); h=sum(r['hit'] for r in records); acc=h/n if n else 0
    out={'experiment':'Selective Repeat-Distance Grammar v1 LOCKED','locked':{'warmup':WARMUP,'picksPerDraw':3,'baseline':BASELINE,'contextLength':3,'minPastExactContextCases':MIN_CONTEXT_CASES,'activationSmoothedPastHitRate':THRESHOLD},'integrity':{'futureMutationFailures':contamination,'passed':not contamination,'hashTail':chain},'eligibleTargets':max(0,len(nums)-WARMUP),'activations':n,'coverage':n/max(1,len(nums)-WARMUP),'hits':h,'accuracy':acc,'excessPercentagePoints':(acc-BASELINE)*100,'oneSidedBinomialPValue':binom_tail(h,n,BASELINE) if n else None,'records':records}
    OUT.write_text(json.dumps(out,indent=2)); print(json.dumps({k:out[k] for k in ['activations','coverage','hits','accuracy','excessPercentagePoints','oneSidedBinomialPValue']},indent=2))
if __name__=='__main__':main()
