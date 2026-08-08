#!/usr/bin/env python3
import json, math, hashlib, random
from pathlib import Path

STATE = Path('v0/cloud_state.json')
OUT_JSON = Path('research/echo_lag_results.json')
OUT_MD = Path('research/echo_lag_results.md')

BASELINE = 5/15
WARMUP = 200
MAX_LAG = 15
WINDOWS = (50, 150, 500)
WINDOW_WEIGHTS = (0.50, 0.30, 0.20)
PRIOR_STRENGTH = 12.0
FREQ_WEIGHT = 0.15
ECHO_WEIGHT = 0.65
MOTIF_WEIGHT = 0.20


def rate_for_lag(prefix, lag, window):
    start = max(lag, len(prefix) - window)
    total = max(0, len(prefix) - start)
    matches = sum(1 for i in range(start, len(prefix)) if prefix[i] == prefix[i-lag])
    return (matches + PRIOR_STRENGTH*(1/15)) / (total + PRIOR_STRENGTH) if total else 1/15


def motif_strength(prefix, lag):
    vals=[]
    for window, weight in ((30,0.7),(100,0.3)):
        start=max(lag,len(prefix)-window)
        total=max(0,len(prefix)-start)
        matches=sum(1 for i in range(start,len(prefix)) if prefix[i]==prefix[i-lag])
        rate=(matches+6*(1/15))/(total+6) if total else 1/15
        vals.append(weight*math.log(max(rate,1e-9)/(1/15)))
    return sum(vals)


def predict_prefix(prefix):
    if len(prefix) < WARMUP:
        raise ValueError('insufficient history')
    echo={n:0.0 for n in range(1,16)}
    motif={n:0.0 for n in range(1,16)}
    for lag in range(1,MAX_LAG+1):
        if lag > len(prefix): break
        n = prefix[-lag]
        combined=0.0
        for window,w in zip(WINDOWS,WINDOW_WEIGHTS):
            rate=rate_for_lag(prefix,lag,window)
            combined += w*math.log(max(rate,1e-9)/(1/15))
        echo[n] += combined
        motif[n] += motif_strength(prefix,lag)
    recent=prefix[-150:]
    counts={n:recent.count(n)/len(recent) for n in range(1,16)}
    scores={n:ECHO_WEIGHT*echo[n]+MOTIF_WEIGHT*motif[n]+FREQ_WEIGHT*math.log(max(counts[n],1e-9)/(1/15)) for n in range(1,16)}
    ranked=sorted(range(1,16), key=lambda n:(scores[n],-n), reverse=True)
    return ranked[:5], scores


def predict_at(full_numbers, target_index):
    return predict_prefix(list(full_numbers[:target_index]))


def binomial_tail(k,n,p):
    return sum(math.comb(n,i)*(p**i)*((1-p)**(n-i)) for i in range(k,n+1))


def main():
    state=json.loads(STATE.read_text())
    draws=sorted(state['draws'], key=lambda x:int(x['draw']))
    numbers=[int(x['number']) for x in draws]
    if len(numbers) <= WARMUP:
        raise SystemExit('Not enough draws for sealed test')

    records=[]
    hits=0
    contamination_failures=[]
    chain='GENESIS'

    for t in range(WARMUP,len(numbers)):
        picks,scores=predict_at(numbers,t)
        mutated=list(numbers)
        rng=random.Random(0xEC40 + t)
        for j in range(t,len(mutated)):
            mutated[j]=rng.randint(1,15)
        picks_mut,_=predict_at(mutated,t)
        if picks_mut != picks:
            contamination_failures.append(int(draws[t]['draw']))

        actual=numbers[t]
        hit=actual in picks
        hits += int(hit)
        payload=f"{chain}|{draws[t]['draw']}|{draws[t-1]['draw']}|{','.join(map(str,picks))}"
        frozen_hash=hashlib.sha256(payload.encode()).hexdigest()[:20]
        chain=frozen_hash
        records.append({
            'targetDraw':int(draws[t]['draw']),
            'trainingThrough':int(draws[t-1]['draw']),
            'picks':picks,
            'actual':actual,
            'hit':hit,
            'frozenHash':frozen_hash,
        })

    n=len(records)
    accuracy=hits/n
    pval=binomial_tail(hits,n,BASELINE)
    result={
        'model':'Echo-Lag Adaptive v1 LOCKED',
        'integrity':{
            'futureMutationTests':n,
            'futureMutationFailures':contamination_failures,
            'passed':len(contamination_failures)==0,
            'rule':'prediction at target t receives draws strictly before t only',
            'predictionHashChainTail':chain,
        },
        'lockedParameters':{
            'warmup':WARMUP,'maxLag':MAX_LAG,'windows':WINDOWS,'windowWeights':WINDOW_WEIGHTS,
            'priorStrength':PRIOR_STRENGTH,'echoWeight':ECHO_WEIGHT,'motifWeight':MOTIF_WEIGHT,'frequencyWeight':FREQ_WEIGHT,
        },
        'tests':n,'hits':hits,'misses':n-hits,'accuracy':accuracy,'randomBaseline':BASELINE,
        'excessPercentagePoints':(accuracy-BASELINE)*100,
        'oneSidedBinomialPValue':pval,
        'firstTestDraw':records[0]['targetDraw'],'lastTestDraw':records[-1]['targetDraw'],
        'recent20':records[-20:],
    }
    OUT_JSON.write_text(json.dumps(result,indent=2))
    verdict='PROMISING' if pval<0.05 and accuracy>BASELINE else 'NO RELIABLE EDGE'
    md=f'''# Echo-Lag Adaptive v1 — sealed walk-forward backtest\n\n- Verdict: **{verdict}**\n- Tests: **{n}**\n- Hits: **{hits}**\n- Accuracy: **{accuracy:.2%}**\n- Random top-5 baseline: **{BASELINE:.2%}**\n- Excess: **{(accuracy-BASELINE)*100:+.2f} percentage points**\n- One-sided exact binomial p-value: **{pval:.6f}**\n- Test range: **#{records[0]['targetDraw']} → #{records[-1]['targetDraw']}**\n- Future-mutation anti-leak checks: **{n}**\n- Contamination failures: **{len(contamination_failures)}**\n- Hash-chain tail: `{chain}`\n\n## Integrity rule\nFor every target draw, the model receives only the chronological prefix ending at the immediately previous draw. Then the unseen suffix is scrambled and the prediction is recomputed. Any changed prediction makes the run fail integrity.\n\n## Locked model\nLags 1–15; recurrence lift estimated over 50/150/500-draw windows with Bayesian shrinkage toward 1/15; short-term lag motif reinforcement; weak recent-frequency tie stabilizer. Parameters are fixed in source before results are generated.\n'''
    OUT_MD.write_text(md)
    print(md)

if __name__=='__main__':
    main()
