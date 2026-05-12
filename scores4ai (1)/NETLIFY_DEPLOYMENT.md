# Netlify deployment for Scores4AI

## Codex already handled this

- Added a root `netlify.toml` that builds from the `scores4ai (1)` app folder, publishes `dist/client`, wires Netlify Functions, adds API redirects, SPA fallback routing, security headers, and immutable asset caching.
- Added `.env.example` with all public and server-only variables.
- Added the OpenRouter Netlify Function at `netlify/functions/openrouter-models.ts`.
- Added `.gitignore` entries so secrets, build output, and dependencies are not committed.
- Added GitHub Actions automation so pushes and pull requests can publish live Netlify URLs after you add Netlify repository secrets.

## Omar must do this manually

1. Push this branch to GitHub.
2. Log in to Netlify.
3. Create a new site from the GitHub repository.
4. Confirm these build settings if Netlify does not auto-read `netlify.toml`:
   - Base directory: `scores4ai (1)`
   - Build command: `npm run build`
   - Publish directory: `dist/client`
   - Functions directory: `netlify/functions`
5. Add these environment variables in **Site configuration → Environment variables**:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_SITE_URL`
   - `OPENROUTER_APP_NAME`
   - `OPENROUTER_MODELS_CACHE_MINUTES`
   - `OPENROUTER_SYNC_CRON_SECRET`
6. Deploy the site.
7. Optional but recommended: add GitHub repository secrets so Actions can publish live URLs automatically:
   - `NETLIFY_AUTH_TOKEN`
   - `NETLIFY_SITE_ID`
8. After deploy, test:
   - `https://YOUR_SITE.netlify.app/`
   - `https://YOUR_SITE.netlify.app/api/openrouter/models`
9. To force an OpenRouter refresh after deployment, send a POST request with the sync secret:

```bash
curl -X POST \
  -H "x-sync-secret: $OPENROUTER_SYNC_CRON_SECRET" \
  https://YOUR_SITE.netlify.app/api/openrouter/sync
```

## Notes

- Secret keys are only used in Netlify Functions and are not referenced by frontend code.
- The frontend uses `VITE_` variables only for browser-safe Supabase access.
- The app currently deploys as a Vite/TanStack client build with Netlify Functions for server-only API work.
- GitHub Actions writes the live production or preview URL to the workflow summary. Pull requests also receive a preview URL comment.
