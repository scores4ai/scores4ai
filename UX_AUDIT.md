# Scores4AI live UX audit — May 18, 2026

Preview command used: `npm run preview:codex` at `http://127.0.0.1:4173`.

## Annotated findings addressed in this PR

1. **Homepage value was too vague.** The original hero said "Discover the best AI" but did not explain the user workflow quickly. It now leads with selecting the right model before spending tokens and gives direct CTAs for Prompt Lab and token-cost comparison.
2. **Rankings felt fake without enough trust context.** Rankings now explicitly frame themselves as a shortlist workflow, include source-label guidance, and cards show when evidence is pending.
3. **Prompt Lab looked like a demo table instead of an actionable workflow.** It now includes task presets, token estimates, context-fit checks, OpenRouter model IDs, per-run cost, risk-adjusted quality recommendations, and lowest-cost recommendations.
4. **Pricing needed token transparency.** The calculator now separates input/output token prices, displays monthly token volume, shows the selected model ID/context window, and labels fallback pricing assumptions.
5. **Search needed intent synonyms.** Queries such as "low cost", "privacy", and "fast" now map to value/privacy/speed signals in the searchable index.
6. **Data labels were defensive.** The data notice now explains what is usable today and how live/cached/estimated records should be trusted.

## Remaining product gaps

- Connect Supabase-backed live OpenRouter rows into the ranking catalog instead of relying on bundled fallback price rows.
- Add real community/reviewer submission flows rather than static community examples.
- Add a server-side Prompt Lab execution queue with saved comparisons once API credentials are configured.
- Replace demo score claims with benchmark provenance links as the live database fills in.

## Screenshot note

The environment did not include a browser binary, and `npx playwright@1.57.0 screenshot` was blocked by the npm registry policy, so screenshots could not be captured from the terminal session. The preview route checks were still run against the live local preview.
