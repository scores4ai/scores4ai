#!/usr/bin/env python3
import json, math, hashlib, random
from pathlib import Path

STATE=Path('v0/cloud_state.json')
OUT_JSON=Path('research/echo_regime_results.json')
OUT_MD=Path('research/echo_regime_results.md')

BASELINE=5/15
WARMUP=260
MAX_LAG=15
REGIME_WINDOW=30
REGIME_PERCENTILE=0.80
MIN_PRIOR_REGIME_WINDOWS=100
WINDOWS=(50,150,500)
WINDOW_WEIGHTS=(0.50,0.30,0.20)
PRIOR_STRENGTH=12.0
ECHO_WEIGHT=0.65
MOTIF_WEIGHT=0.20
FREQ_WEIGHT=0.15


def rate_for_lag(prefix,lag,window):
    start=max(lag,len(prefix)-window)
    total=max(0,len(prefix)-start)
    matches=sum(1 for i in range(start,len(prefix)) if prefix[i]==prefix[i-lag])
    return (matches+PRIOR_STRENGTH*(1/15))/(total+PRIOR_STRENGTH) if total else 1/15


def motif_strength(prefix,lag):
    total_score=0.0
    for window,weight in ((30,0.7),(100,0.3)):
        start=max(lag,len(prefix)-window)
        total=max(0,len(prefix)-start)
        matches=sum(1 for i in range(start,len(prefix)) if prefix[i]==prefix[i-lag])
        rate=(matches+6*(1/15))/(total+6) if total else 1/15
        total_score += weight*math.log(max(rate,1e-12)/(1/15))
    return total_score


def echo_picks(prefix):
    echo={n:0.0 for n in range(1,16)}
    motif={n:0.0 for n in range(1,16)}
    for lag in range(1,MAX_LAG+1):
        n=prefix[-lag]
        combined=0.0
        for window,w in zip(WINDOWS,WINDOW_WEIGHTS):
            rate=rate_for_lag(prefix,lag,window)
            combined += w*math.log(max(rate,1e-12)/(1/15))
        echo[n]+=combined
        motif[n]+=motif_strength(prefix,lag)
    recent=prefix[-150:]
    counts={n:recent.count(n)/len(recent) for n in range(1,16)}
    scores={n:ECHO_WEIGHT*echo[n]+MOTIF_WEIGHT*motif[n]+FREQ_WEIGHT*math.log(max(counts[n],1e-12)/(1/15)) for n in range(1,16)}
    return sorted(range(1,16),key=lambda n:(scores[n],-n),reverse=True)[:5]


def echo_density(seq,end_index):
    # Density inside the REGIME_WINDOW ending at end_index (exclusive).
    start=max(MAX_LAG,end_index-REGIME_WINDOW)
    matches=0
    comps=0
    for i in range(start,end_index):
        for lag in range(1,MAX_LAG+1):
            if i-lag>=0:
                comps+=1
                if seq[i]==seq[i-lag]: matches+=1
    return matches/comps if comps else 0.0


def percentile(values,q):
    vals=sorted(values)
    if not vals: return float('inf')
    idx=min(len(vals)-1,max(0,math.ceil(q*len(vals))-1))
    return vals[idx]


def regime_decision(prefix):
    end=len(prefix)
    current=echo_density(prefix,end)
    historical=[]
    # Build the threshold only from windows that ended in the known past.
    first_end=MAX_LAG+REGIME_WINDOW
    for e in range(first_end,end-REGIME_WINDOW+1):
        historical.append(echo_density(prefix,e))
    if len(historical)<MIN_PRIOR_REGIME_WINDOWS:
        return False,current,None
    threshold=percentile(historical,REGIME_PERCENTILE)
    return current>=threshold,current,threshold


def decision_at(numbers,t):
    prefix=list(numbers[:t])
    active,density,threshold=regime_decision(prefix)
    picks=echo_picks(prefix) if active else []
    return active,picks,density,threshold


def binomial_tail(k,n,p):
    return sum(math.comb(n,i)*(p**i)*((1-p)**(n-i)) for i in range(k,n+1)) if n else 1.0


def main():
    state=json.loads(STATE.read_text())
    draws=sorted(state['draws'],key=lambda x:int(x['draw']))
    numbers=[int(x['number']) for x in draws]
    records=[]; active_records=[]; contamination=[]; hits=0; chain='GENESIS'

    for t in range(WARMUP,len(numbers)):
        active,picks,density,threshold=decision_at(numbers,t)

        # Strong anti-leak test: mutate the entire unseen suffix and require both
        # the regime gate and frozen picks to remain identical.
        mutated=list(numbers)
        rng=random.Random(0xEC40+t)
        for j in range(t,len(mutated)):
            mutated[j]=rng.randint(1,15)
        a2,p2,d2,th2=decision_at(mutated,t)
        if (a2,p2)!=(active,picks) or abs(d2-density)>1e-15 or ((threshold is None)!=(th2 is None)) or (threshold is not None and abs(th2-threshold)>1e-15):
            contamination.append(int(draws[t]['draw']))

        actual=numbers[t]
        hit=active and actual in picks
        payload=f"{chain}|{draws[t]['draw']}|{int(active)}|{','.join(map(str,picks))}|{density:.12f}|{threshold if threshold is not None else 'NA'}"
        frozen_hash=hashlib.sha256(payload.encode()).hexdigest()[:20]
        chain=frozen_hash
        rec={'targetDraw':int(draws[t]['draw']),'trainingThrough':int(draws[t-1]['draw']),'active':active,'density':density,'threshold':threshold,'picks':picks,'actual':actual,'hit':bool(hit),'frozenHash':frozen_hash}
        records.append(rec)
        if active:
            active_records.append(rec)
            hits+=int(hit)

    n=len(active_records); accuracy=hits/n if n else 0.0; pval=binomial_tail(hits,n,BASELINE)
    # Also measure whether abstention selected easier periods vs all eligible draws.
    coverage=n/len(records) if records else 0.0
    result={
      'model':'Echo-Regime Adaptive v1 LOCKED',
      'integrity':{'futureMutationTests':len(records),'futureMutationFailures':contamination,'passed':not contamination,'rule':'gate, threshold, and picks use only draws strictly before target','predictionHashChainTail':chain},
      'lockedParameters':{'warmup':WARMUP,'maxLag':MAX_LAG,'regimeWindow':REGIME_WINDOW,'regimePercentile':REGIME_PERCENTILE,'minPriorRegimeWindows':MIN_PRIOR_REGIME_WINDOWS,'echoWindows':WINDOWS,'echoWindowWeights':WINDOW_WEIGHTS,'priorStrength':PRIOR_STRENGTH,'echoWeight':ECHO_WEIGHT,'motifWeight':MOTIF_WEIGHT,'frequencyWeight':FREQ_WEIGHT},
      'eligibleTests':len(records),'activatedTests':n,'coverage':coverage,'hits':hits,'misses':n-hits,'activatedAccuracy':accuracy,'randomTop5Baseline':BASELINE,'excessPercentagePoints':(accuracy-BASELINE)*100,'oneSidedExactBinomialPValue':pval,
      'firstEligibleDraw':records[0]['targetDraw'] if records else None,'lastEligibleDraw':records[-1]['targetDraw'] if records else None,'recentActivated':active_records[-20:]
    }
    OUT_JSON.write_text(json.dumps(result,indent=2))
    verdict='PROMISING' if n>=30 and accuracy>BASELINE and pval<0.05 else 'NO RELIABLE EDGE'
    md=f'''# Echo-Regime Adaptive v1 — sealed conditional walk-forward backtest\n\n- Verdict: **{verdict}**\n- Eligible targets: **{len(records)}**\n- Echo-active targets: **{n}** ({coverage:.1%} coverage)\n- Hits while active: **{hits}**\n- Accuracy while active: **{accuracy:.2%}**\n- Random top-5 baseline: **{BASELINE:.2%}**\n- Excess while active: **{(accuracy-BASELINE)*100:+.2f} percentage points**\n- One-sided exact binomial p-value: **{pval:.6f}**\n- Anti-leak future-mutation checks: **{len(records)}**\n- Contamination failures: **{len(contamination)}**\n- Hash-chain tail: `{chain}`\n\n## Locked regime gate\nAt each target, compute 30-draw aggregate lag-repeat density across lags 1–15. Compare it only with earlier regime windows available at that moment. Activate when current density is at or above the past-only 80th percentile. No threshold is learned from future draws.\n'''
    OUT_MD.write_text(md)
    print(md)

if __name__=='__main__': main()
