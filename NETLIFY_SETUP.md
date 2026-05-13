# Netlify Setup — Scores4AI

## Codex already handled this

- Added root `netlify.toml` with `base = "scores4ai (1)"`.
- Configured `npm run build` and `dist/client` publish directory; the build now emits `dist/client/index.html` for Netlify fallback routing.
- Set Node 22.
- Added immutable asset caching and baseline security headers.
- Added an SPA fallback redirect to `/index.html` and explicit Netlify Functions bundling from `netlify/functions`.
- Added a scheduled Netlify function for a 12-hour OpenRouter sync cadence.
- Added `/.netlify/functions/setup-status` so the app can report missing Netlify/Supabase/OpenRouter setup without exposing secrets.
- Added `/.netlify/functions/openrouter-models` for live model fetch + cache/demo fallback status in the UI.

## You must do this manually

1. Connect the GitHub repository to Netlify.
2. Confirm the build settings match `netlify.toml`.
3. Add environment variables from `.env.example`.
4. Deploy the site.
5. Confirm Netlify Scheduled Functions are enabled on your plan/team and review the first function log after deploy.

## Netlify deployment checklist

- [ ] Repository connected.
- [ ] Build base directory is `scores4ai (1)`.
- [ ] Build command is `npm run build`.
- [ ] Publish directory is `dist/client`.
- [ ] Environment variables configured.
- [ ] `npm run build` emits `dist/client/index.html`.
- [ ] `npm run verify:production-build` passes before deploy.
- [ ] First deploy completed.
- [ ] Scheduled sync strategy confirmed.
