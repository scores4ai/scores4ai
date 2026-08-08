# Echo-Regime Adaptive v1 — sealed conditional walk-forward backtest

- Verdict: **NO RELIABLE EDGE**
- Eligible targets: **340**
- Echo-active targets: **127** (37.4% coverage)
- Hits while active: **40**
- Accuracy while active: **31.50%**
- Random top-5 baseline: **33.33%**
- Excess while active: **-1.84 percentage points**
- One-sided exact binomial p-value: **0.700395**
- Anti-leak future-mutation checks: **340**
- Contamination failures: **0**
- Hash-chain tail: `9f3ed30343335aaddb83`

## Locked regime gate
At each target, compute 30-draw aggregate lag-repeat density across lags 1–15. Compare it only with earlier regime windows available at that moment. Activate when current density is at or above the past-only 80th percentile. No threshold is learned from future draws.
