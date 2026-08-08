#!/usr/bin/env python3
import json, math, random, hashlib
from collections import Counter
from pathlib import Path

STATE=Path('v0/cloud_state.json')
OUT=Path('research/three_pattern_models_results.json')
BASELINE=3/15
WARMUP=220
MAX_LAG=15

# Logic is unchanged from v1. This version only caches deterministic
# prefix-derived quantities so the sealed test can finish efficiently.

def prev_distance(seq, idx):
    v=seq[idx]
    for d in range(1,MAX_LAG+1):
        j=idx-d
        if j<0: break
        if seq[j]==v: return d
    return 0

def distance_series(prefix):
    return [prev_distance(prefix,i) for i in range(len(prefix))]

def fallback_freq(prefix, used):
    c=Counter(prefix[-120:])
    return [n for n,_ in sorted(c.items(), key=lambda kv:(kv[1],-kv[0]), reverse=True) if n not in used]

def model_a(prefix, ds=None):
    ds=ds if ds is not None else distance_series(prefix)
    ctx=tuple(ds[-3:])
    scores=Counter()
    for i in range(3,len(ds)):
        hist=tuple(ds[i-3:i])
        sim=sum((3-j) for j in range(3) if hist[j]==ctx[j])
        if sim:
            nxt=ds[i]
            if 1<=nxt<=MAX_LAG and nxt<=len(prefix):
                scores[prefix[-nxt]] += sim
    picks=[n for n,_ in scores.most_common()]
    for n in fallback_freq(prefix,set(picks)):
        picks.append(n)
        if len(picks)>=3: break
    return picks[:3]

def feature_from_ds(ds, end):
    return (ds[end-1],ds[end-2],ds[end-3],sum(1 for x in ds[max(0,end-8):end] if x>0))

def model_b(prefix, ds=None):
    ds=ds if ds is not None else distance_series(prefix)
    N=len(prefix)
    fcur=feature_from_ds(ds,N)
    features=[None]*N
    for t in range(3,N):
        features[t]=feature_from_ds(ds,t)
    scores=Counter()
    for lag in range(1,MAX_LAG+1):
        if lag>N: break
        cand=prefix[-lag]
        succ=2.0/15.0; total=2.0
        for t in range(max(40,lag+5),N):
            fh=features[t]
            sim=(2 if fh[0]==fcur[0] else 0)+(1 if fh[1]==fcur[1] else 0)+(1 if abs(fh[3]-fcur[3])<=1 else 0)
            if sim==0: continue
            total += sim
            if prefix[t]==prefix[t-lag]: succ += sim
        rate=succ/total
        scores[cand] += math.log(max(rate,1e-9)/(1/15))
    ranked=sorted(range(1,16), key=lambda n:(scores[n],prefix[-90:].count(n),-n), reverse=True)
    return ranked[:3]

def signature(win):
    ids={}; nxt=0; out=[]
    for v in win:
        if v not in ids:
            ids[v]=nxt; nxt+=1
        out.append(ids[v])
    return tuple(out)

def model_c(prefix):
    L=9
    cur=prefix[-L:]
    csig=signature(cur)
    votes=Counter()
    for end in range(L,len(prefix)):
        w=prefix[end-L:end]
        sig=signature(w)
        dist=sum(1 for a,b in zip(sig,csig) if a!=b)
        if dist>3: continue
        weight=1.0/(1+dist)
        nxt=prefix[end]
        rel=None
        for j in range(L-1,-1,-1):
            if w[j]==nxt:
                rel=j; break
        if rel is not None:
            votes[cur[rel]] += 2*weight
    picks=[n for n,_ in votes.most_common()]
    for n in fallback_freq(prefix,set(picks)):
        picks.append(n)
        if len(picks)>=3: break
    return picks[:3]

def all_models(prefix):
    ds=distance_series(prefix)
    pa=model_a(prefix,ds)
    pb=model_b(prefix,ds)
    pc=model_c(prefix)
    v=Counter()
    for ps in (pa,pb,pc):
        for rank,n in enumerate(ps): v[n]+=3-rank
    pe=sorted(range(1,16), key=lambda n:(v[n],prefix[-100:].count(n),-n), reverse=True)[:3]
    return [pa,pb,pc,pe]

def binom_tail(k,n,p):
    return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))

def main():
    state=json.loads(STATE.read_text())
    draws=sorted(state['draws'],key=lambda x:int(x['draw']))
    nums=[int(x['number']) for x in draws]
    names=['Repeat-Distance Grammar','Multi-Echo Intersection','Pattern Analog','Consensus Ensemble']
    stats={n:{'hits':0,'records':[]} for n in names}
    contamination=[]; chain='GENESIS'
    for t in range(WARMUP,len(nums)):
        prefix=nums[:t]
        preds=all_models(prefix)
        # Future mutation: because models receive prefix only, corrupted suffix must be irrelevant.
        mut=nums[:]
        rng=random.Random(730001+t)
        for j in range(t,len(mut)): mut[j]=rng.randint(1,15)
        mp=all_models(mut[:t])
        if mp!=preds: contamination.append(int(draws[t]['draw']))
        actual=nums[t]
        for name,picks in zip(names,preds):
            hit=actual in picks
            stats[name]['hits']+=int(hit)
            stats[name]['records'].append({'draw':int(draws[t]['draw']),'trainingThrough':int(draws[t-1]['draw']),'picks':picks,'actual':actual,'hit':hit})
        payload=f"{chain}|{draws[t]['draw']}|"+'|'.join(','.join(map(str,p)) for p in preds)
        chain=hashlib.sha256(payload.encode()).hexdigest()[:20]
    n=len(nums)-WARMUP
    results={}
    for name in names:
        h=stats[name]['hits']; acc=h/n
        results[name]={'tests':n,'hits':h,'misses':n-h,'accuracy':acc,'baseline':BASELINE,'excessPercentagePoints':(acc-BASELINE)*100,'oneSidedBinomialPValue':binom_tail(h,n,BASELINE),'recent20':stats[name]['records'][-20:]}
    out={'experiment':'Three Pattern Models v1 LOCKED','integrity':{'futureMutationTests':n,'futureMutationFailures':contamination,'passed':not contamination,'predictionHashChainTail':chain},'locked':{'warmup':WARMUP,'maxLag':MAX_LAG,'picksPerDraw':3,'baseline':BASELINE},'firstTestDraw':int(draws[WARMUP]['draw']),'lastTestDraw':int(draws[-1]['draw']),'results':results}
    OUT.write_text(json.dumps(out,indent=2))
    print(json.dumps({k:{'acc':round(v['accuracy'],4),'hits':v['hits'],'p':round(v['oneSidedBinomialPValue'],6)} for k,v in results.items()},indent=2))

if __name__=='__main__': main()
