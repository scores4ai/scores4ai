# Scores4AI

Scores4AI is a transparent AI ranking and comparison platform for LLMs, AI tools, AI agents, and AI APIs. The product direction is Rotten Tomatoes + Consumer Reports + IMDb/Product Hunt/Hugging Face for AI, with live model metadata, visible formulas, source labeling, Prompt Lab benchmarking, and personalized rankings.

## Codex already handled this

- Added a production Netlify configuration at the repository root with the app base directory, Node 22, static asset caching, security headers, an SPA fallback backed by a generated `dist/client/index.html`, explicit function bundling, and a scheduled OpenRouter sync placeholder.
- Added a complete Supabase setup under `supabase/` with a one-shot `full_setup.sql` and migration file for profiles, models, tools, agents, reviews, comparisons, prompt lab results, submitted tools, model sources, bookmarks, comments, and saved comparisons.
- Added RLS, policies, auth profile trigger, updated-at triggers, indexes, and automatic RLS enablement for future public tables.
- Added reusable scoring/pricing modules for the client and moved OpenRouter fetch/normalization plus Supabase service-role cache sync into server-only source paths.
- Improved the UI for Prompt Lab, pricing calculator, transparent scoring sliders, personalized rankings, model profile sources, and setup transparency labels.
- Added setup documentation for Supabase, Netlify, and OpenRouter.
- Added an in-app setup checker backed by `/.netlify/functions/setup-status` so missing public/server config is listed explicitly instead of inferred.
- Added `/.netlify/functions/openrouter-models` so the UI can use live OpenRouter rows, then cached Supabase rows, and only fall back to demo records when both are unavailable.

## You must do this manually

1. Create/log into Supabase and Netlify accounts.
2. Create/log into an OpenRouter account and generate an API key.
3. Copy `.env.example` values into Netlify environment variables and local `.env` files.
4. Run `supabase/full_setup.sql` once in Supabase SQL Editor or apply the migration with the Supabase CLI.
5. Trigger the first OpenRouter sync after adding Supabase service credentials.
6. Click deploy in Netlify after connecting the repository.

## Local development

```bash
cd "scores4ai (1)"
npm install
npm run dev
```

## Build and checks

```bash
cd "scores4ai (1)"
npm run lint
npm run build
npm run verify:production-build
```

## Data policy

Scores4AI must never present fake rankings as live rankings. Demo rows are explicitly labeled as demo. Estimated calculations are labeled as estimated. Live OpenRouter and cached Supabase data are labeled separately.

## Key architecture

- **OpenRouter** is the primary live model source via `https://openrouter.ai/api/v1/models?output_modalities=all`; fetch and cache-sync code lives under `src/server/` or Netlify functions, not browser components.
- **Supabase** stores cached normalized model metadata, pricing, sources, reviews, community features, and Prompt Lab results.
- **Scoring** uses a visible weighted formula with adjustable categories: performance, price/value, speed, features, privacy, and community rating.
- **Prompt Lab** estimates tokens, costs, context fit, speed, formatting quality, reasoning quality, hallucination risk, and citations support until live API execution is enabled server-side.
