# OpenRouter Setup — Scores4AI

## Codex already handled this

- Added OpenRouter model fetching and normalization in server-only source paths and Netlify/script entry points.
- Captures model name, provider, pricing, context window, modality support, supported parameters, description, and timestamps when present.
- Added a standalone sync script at `scores4ai (1)/scripts/sync-openrouter-models.mjs`; browser components only import formatting/pricing helpers and never call OpenRouter directly.
- Added cache freshness constants: models every 12 hours and pricing every 24 hours.
- Added UI labels for Live, Cached, Estimated, and Demo data states.
- Added a setup-status function that verifies OpenRouter Models API reachability server-side.
- Added `/.netlify/functions/openrouter-models` so the app serves live OpenRouter rows only after a successful server-side fetch, then Supabase cache, then demo fallback.

## You must do this manually

1. Create/log into an OpenRouter account.
2. Generate an API key if live execution is later enabled.
3. Add `OPENROUTER_API_KEY` to Netlify/server environment variables.
4. Add Supabase service credentials before running the sync script.
5. Run the first sync:

```bash
cd "scores4ai (1)"
SUPABASE_URL="https://your-project-ref.supabase.co" \
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key" \
npm run sync:openrouter
```

## OpenRouter sync checklist

- [ ] OpenRouter key created.
- [ ] Supabase tables exist.
- [ ] Server-only keys configured.
- [ ] Confirm no OpenRouter request code or service-role key markers are present in `dist/client` by running `npm run verify:production-build`.
- [ ] First sync completed.
- [ ] Model rows show `source_status = live`.
- [ ] `model_sources` has a verified API source row.
