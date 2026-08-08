#!/usr/bin/env python3
import json, math, hashlib
from collections import Counter
from pathlib import Path
STATE=Path('v0/cloud_state.json'); OUT=Path('research/arc_chain_v1_results.json')
WARMUP=220; MAX_LAG=15; BASELINE=.2; ARC_CTX=5

def repeat_gap(seq,i):
    for d in range(1,MAX_LAG+1):
        j=i-d
        if j<0: break
        if seq[j]==seq[i]: return d
    return 0

def gaps(seq): return [repeat_gap(seq,i) for i in range(len(seq))]
def arc_events(seq):
    g=gaps(seq)
    return [(i,g[i]) for i in range(len(g)) if g[i]>0]

def fallback(pre,used):
    c=Counter(pre[-120:]); return [n for n,_ in sorted(c.items(),key=lambda z:(z[1],-z[0]),reverse=True) if n not in used]

def predict(pre):
    ev=arc_events(pre)
    if len(ev)<ARC_CTX+3:
        return fallback(pre,set())[:3]
    cur=[g for _,g in ev[-ARC_CTX:]]
    lag_votes=Counter()
    # Historical analogs use only arc-gap sequences available before the target.
    # Weighted suffix similarity preserves exact gaps; recent arc positions matter more.
    for j in range(ARC_CTX, len(ev)-1):
        hist=[g for _,g in ev[j-ARC_CTX:j]]
        sim=0.0
        for k,(a,b) in enumerate(zip(hist,cur)):
            w=k+1
            if a==b: sim += 2.0*w
            elif abs(a-b)==1: sim += 0.5*w
        if sim<=0: continue
        nxt_gap=ev[j][1]
        lag_votes[nxt_gap]+=sim
    # Also learn immediate next-draw repeat gaps from similar recent arc histories.
    gs=gaps(pre)
    for t in range(40,len(pre)):
        hev=[(i,gs[i]) for i in range(t) if gs[i]>0]
        if len(hev)<ARC_CTX: continue
        hist=[g for _,g in hev[-ARC_CTX:]]
        sim=sum((k+1)*(2.0 if a==b else 0.5 if abs(a-b)==1 else 0.0) for k,(a,b) in enumerate(zip(hist,cur)))
        if sim<=0: continue
        ng=gs[t]
        if ng>0: lag_votes[ng]+=0.5*sim
    num_votes=Counter()
    for lag,score in lag_votes.items():
        if 1<=lag<=len(pre): num_votes[pre[-lag]]+=score
    picks=[n for n,_ in num_votes.most_common()]
    for n in fallback(pre,set(picks)):
        picks.append(n)
        if len(picks)>=3: break
    return picks[:3]

def binom_tail(k,n,p): return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
def main():
    st=json.loads(STATE.read_text()); draws=sorted(st['draws'],key=lambda x:int(x['draw'])); nums=[int(x['number']) for x in draws]
    rec=[]; fails=[]; chain='GENESIS'
    for t in range(WARMUP,len(nums)):
        pre=nums[:t]; p=predict(pre)
        mut=nums[:t]+[((x+6-1)%15)+1 for x in nums[t:]]
        mp=predict(mut[:t])
        if p!=mp: fails.append(int(draws[t]['draw']))
        actual=nums[t]; hit=actual in p
        rec.append({'draw':int(draws[t]['draw']),'trainingThrough':int(draws[t-1]['draw']),'picks':p,'actual':actual,'hit':hit})
        chain=hashlib.sha256(f'{chain}|{draws[t]["draw"]}|{p}'.encode()).hexdigest()[:20]
    n=len(rec); h=sum(r['hit'] for r in rec); acc=h/n
    out={'experiment':'Arc-Chain Repeat Geometry v1 LOCKED','locked':{'warmup':WARMUP,'picks':3,'baseline':BASELINE,'maxLag':MAX_LAG,'arcContextLength':ARC_CTX},'integrity':{'futureMutationFailures':fails,'passed':not fails,'hashTail':chain},'tests':n,'hits':h,'accuracy':acc,'excessPercentagePoints':(acc-BASELINE)*100,'oneSidedBinomialPValue':binom_tail(h,n,BASELINE),'recent20':rec[-20:]}
    OUT.write_text(json.dumps(out,indent=2)); print(json.dumps({k:out[k] for k in ['tests','hits','accuracy','excessPercentagePoints','oneSidedBinomialPValue']},indent=2))
if __name__=='__main__': main()
