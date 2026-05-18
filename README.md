# Scores4AI

Scores4AI is a transparent AI ranking and comparison platform for LLMs, AI tools, AI agents, and AI APIs. The product direction is Rotten Tomatoes + Consumer Reports + IMDb/Product Hunt/Hugging Face for AI, with live model metadata, visible formulas, source labeling, Prompt Lab benchmarking, and personalized rankings.

## Codex already handled this

- Added a production Netlify configuration at the repository root with the app base directory, Node 22, static asset caching, security headers, an SPA fallback backed by a generated `dist/client/index.html`, explicit function bundling, and a scheduled OpenRouter sync placeholder.
- Added a complete Supabase setup under `supabase/` with a one-shot `full_setup.sql` and migration file for profiles, models, tools, agents, reviews, comparisons, prompt lab results, submitted tools, model sources, bookmarks, comments, and saved comparisons.
- Added RLS, policies, auth profile trigger, updated-at triggers, indexes, and automatic RLS enablement for future public tables.
- Added reusable scoring/pricing modules for the client and moved OpenRouter fetch/normalization plus Supabase service-role cache sync into server-only source paths.
- Improved the UI for Prompt Lab, pricing calculator, transparent scoring sliders, personalized rankings, model profile sources, and setup transparency labels.
- Added setup documentation for Supabase, Netlify, and OpenRouter.

## You must do this manually

1. Create/log into Supabase and Netlify accounts.
2. Create/log into an OpenRouter account and generate an API key.
3. Copy `.env.example` values into Netlify environment variables and local `.env` files.
4. Run `supabase/full_setup.sql` once in Supabase SQL Editor or apply the migration with the Supabase CLI.
5. Trigger the first OpenRouter sync after adding Supabase service credentials.
6. Click deploy in Netlify after connecting the repository.

## Local development

From the repository root, install dependencies once and run the app with a Codex-friendly host binding:

```bash
npm run setup
npm run dev:codex
```

The `dev:codex` command starts Vite on `0.0.0.0:5173`, which lets Codex expose the local web preview. Open the preview URL in the Codex in-app browser, click around the site, and use Codex browser comments/annotations to point at exact UI changes you want.

You can still run commands from the nested app directory when preferred:

```bash
cd "scores4ai (1)"
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Build and checks

```bash
npm run lint
npm run build
npm run verify:production-build
```

For a production-style Codex preview after building, run:

```bash
npm run preview:codex
```

## Data policy

Scores4AI must never present fake rankings as live rankings. Demo rows are explicitly labeled as demo. Estimated calculations are labeled as estimated. Live OpenRouter and cached Supabase data are labeled separately.

## Key architecture

- **OpenRouter** is the primary live model source via `https://openrouter.ai/api/v1/models?output_modalities=all`; fetch and cache-sync code lives under `src/server/` or Netlify functions, not browser components.
- **Supabase** stores cached normalized model metadata, pricing, sources, reviews, community features, and Prompt Lab results.
- **Scoring** uses a visible weighted formula with adjustable categories: performance, price/value, speed, features, privacy, and community rating.
- **Prompt Lab** estimates tokens, costs, context fit, speed, formatting quality, reasoning quality, hallucination risk, and citations support until live API execution is enabled server-side.
