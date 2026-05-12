# OpenRouter setup for Scores4AI

## Codex already handled this

- Added `src/lib/openrouter.ts` to fetch OpenRouter models, normalize pricing and metadata, and upsert cached model records into Supabase.
- Added `netlify/functions/openrouter-models.ts` as the server-only API endpoint.
- Added redirects so `/api/openrouter/models` and `/api/openrouter/sync` call the Netlify Function.
- Added environment variable placeholders to `.env.example`.
- Added Supabase columns for OpenRouter IDs, raw source payloads, sync timestamps, context windows, modalities, tokenizers, and token pricing.
- Added n8n and Make.com automation templates for recurring syncs.

## Omar must do this manually

1. Log in to OpenRouter.
2. Create or copy an API key.
3. Add the key to Netlify as `OPENROUTER_API_KEY`.
4. Set `OPENROUTER_SITE_URL` to your production URL, for example `https://scores4ai.netlify.app`.
5. Set `OPENROUTER_APP_NAME` to `Scores4AI`.
6. Set `OPENROUTER_SYNC_CRON_SECRET` to a long random value.
7. Deploy on Netlify after adding the variables.
8. Warm the cache by opening:

```text
https://YOUR_SITE.netlify.app/api/openrouter/models
```

9. Optional: automate recurring syncs with n8n by importing `automation/n8n/openrouter-sync.workflow.json`, or build the Make.com scenario from `automation/make/openrouter-sync.recipe.json`.
10. Force a refresh when needed:

```bash
curl -X POST \
  -H "x-sync-secret: YOUR_OPENROUTER_SYNC_CRON_SECRET" \
  https://YOUR_SITE.netlify.app/api/openrouter/sync
```

## How caching works

- First request checks Supabase for cached OpenRouter models.
- If cached rows exist, the function returns them without calling OpenRouter.
- If cache is empty or a forced sync is requested, the function fetches from OpenRouter and upserts rows into `public.models`.
- `OPENROUTER_MODELS_CACHE_MINUTES` controls freshness for programmatic sync calls.
