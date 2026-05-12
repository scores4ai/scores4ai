# Scores4AI

Scores4AI is an AI model, tool, and agent ranking app built with TanStack Start, React, Vite, Tailwind CSS, Supabase, Netlify Functions, and OpenRouter.

## Project structure audit

## Codex already handled this

- Audited the repository and found the runnable app in `scores4ai (1)`.
- Confirmed the app uses Vite/TanStack Start with React routes in `src/routes`, shared UI in `src/components/site`, and current demo catalog data in `src/lib/data.ts`.
- Confirmed production builds output browser assets to `dist/client` and server artifacts to `dist/server`.
- Added Netlify deployment configuration at the repository root.
- Added Supabase schema and setup docs under `supabase/` and the setup markdown files.
- Added OpenRouter sync, model caching, transparent scoring, Prompt Lab estimating, and pricing calculator utilities.
- Added GitHub Actions + Netlify live deployment automation and n8n/Make.com workflow templates.

## Omar must do this manually

- Create/log in to Supabase, Netlify, and OpenRouter accounts.
- Run the one-file Supabase SQL setup in `supabase/schema.sql`.
- Add secret keys and project URLs to Netlify environment variables.
- Deploy the Netlify site from GitHub.
- Add GitHub repository secrets if you want Actions to publish live Netlify URLs automatically.
- Trigger or test the OpenRouter sync endpoint after deployment, or activate the n8n/Make.com recurring sync workflow.

## App folders

```text
.
├── netlify.toml                         # Netlify build, function, redirect, and header config
└── scores4ai (1)/
    ├── .env.example                     # Required environment variables, with no real secrets
    ├── AUTOMATION_WORKFLOWS.md          # GitHub Actions, n8n, and Make.com automation
    ├── NETLIFY_DEPLOYMENT.md            # Manual Netlify checklist
    ├── OPENROUTER_SETUP.md              # Manual OpenRouter checklist
    ├── SUPABASE_SETUP.md                # Manual Supabase checklist
    ├── automation/                      # n8n workflow and Make.com recipe
    ├── netlify/functions/               # Server-only Netlify Functions
    ├── src/components/site/             # Shared app UI components
    ├── src/lib/                         # Data, Supabase REST, OpenRouter, scoring, pricing utilities
    ├── src/routes/                      # TanStack file routes
    └── supabase/                        # SQL migration and one-file pasteable schema
```

## Environment variables

Copy `.env.example` to `.env` for local development and add the real values locally. Add the same values in Netlify for production.

### Browser-safe variables

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

### Server-only variables

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_SITE_URL`
- `OPENROUTER_APP_NAME`
- `OPENROUTER_MODELS_CACHE_MINUTES`
- `OPENROUTER_SYNC_CRON_SECRET`

Never expose `SUPABASE_SERVICE_ROLE_KEY` or `OPENROUTER_API_KEY` in frontend code. Only Netlify Functions should read those values.

## Supabase workflow

1. Create a Supabase project.
2. Paste `supabase/schema.sql` into the Supabase SQL Editor and run it once.
3. Copy your Supabase project URL, anon key, and service-role key into Netlify environment variables.
4. Optional: run `select * from public.ensure_public_table_rls();` after future schema changes to verify RLS is enabled.

The schema includes tables for profiles, models, tools, agents, reviews, comparisons, Prompt Lab results, submitted tools, model sources, and score formulas.

## Live website workflow

The repository includes `.github/workflows/netlify-deploy.yml`. After Omar adds `NETLIFY_AUTH_TOKEN` and `NETLIFY_SITE_ID` as GitHub Actions secrets, GitHub can build the app and publish a live Netlify URL on pushes, manual workflow runs, and pull requests. Pull requests receive preview URL comments.

## OpenRouter workflow

1. Add `OPENROUTER_API_KEY` to Netlify.
2. Deploy the site.
3. Visit `/api/openrouter/models` to read cached models or populate the cache if empty.
4. POST to `/api/openrouter/sync` with `x-sync-secret` to force a refresh.
5. For recurring automation, import the n8n workflow or create the Make.com scenario from `AUTOMATION_WORKFLOWS.md`.

OpenRouter model records are normalized and cached in `public.models` with raw source payloads preserved in `raw_source` for traceability.

## Transparent score formula

The default score formula is intentionally explainable:

```text
Overall = community×20% + expert×25% + performance×15% + value×15% + trust×15% + freshness×10%
```

The same formula exists in:

- SQL: `public.calculate_score_from_components(components jsonb)`
- TypeScript: `src/lib/score-formula.ts`

Each score component is expected to be on a 0-100 scale.

## Prompt Lab and pricing calculators

Prompt Lab cost estimating is available in:

- SQL: `public.estimate_prompt_cost_usd(input_tokens, output_tokens, input_price_per_million, output_price_per_million)`
- TypeScript: `src/lib/pricing.ts`

The TypeScript estimator supports prompt text token approximation, explicit token counts, cached input tokens, expected output tokens, per-run cost, and monthly pricing projections.

## Local development

```bash
cd "scores4ai (1)"
npm install
cp .env.example .env
npm run dev
```

## Production build

```bash
cd "scores4ai (1)"
npm run build
```

## Demo data notice

The existing `src/lib/data.ts` catalog is demo UI data for the current frontend experience. Production model data should come from Supabase/OpenRouter after the manual setup steps are complete.

## Documentation

- [Automation workflows](./AUTOMATION_WORKFLOWS.md)
- [Netlify deployment](./NETLIFY_DEPLOYMENT.md)
- [Supabase setup](./SUPABASE_SETUP.md)
- [OpenRouter setup](./OPENROUTER_SETUP.md)
