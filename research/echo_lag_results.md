# Echo-Lag Adaptive v1 — sealed walk-forward backtest

- Verdict: **NO RELIABLE EDGE**
- Tests: **400**
- Hits: **128**
- Accuracy: **32.00%**
- Random top-5 baseline: **33.33%**
- Excess: **-1.33 percentage points**
- One-sided exact binomial p-value: **0.730720**
- Test range: **#89222 → #89621**
- Future-mutation anti-leak checks: **400**
- Contamination failures: **0**
- Hash-chain tail: `d0ba53c6db5b37a1ffb2`

## Integrity rule
For every target draw, the model receives only the chronological prefix ending at the immediately previous draw. Then the unseen suffix is scrambled and the prediction is recomputed. Any changed prediction makes the run fail integrity.

## Locked model
Lags 1–15; recurrence lift estimated over 50/150/500-draw windows with Bayesian shrinkage toward 1/15; short-term lag motif reinforcement; weak recent-frequency tie stabilizer. Parameters are fixed in source before results are generated.
