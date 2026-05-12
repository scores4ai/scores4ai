# Scores4AI automation workflows

## Codex already handled this

- Added a GitHub Actions workflow at `.github/workflows/netlify-deploy.yml` that builds the app on pushes, pull requests, and manual runs.
- Added Netlify preview deployment automation for pull requests and production deployment automation for pushes/manual runs once GitHub secrets are configured.
- Added an importable n8n workflow at `automation/n8n/openrouter-sync.workflow.json` that syncs OpenRouter models every 6 hours or on manual execution.
- Added a Make.com recipe at `automation/make/openrouter-sync.recipe.json` with exact Scheduler and HTTP module settings.
- Added `automation/.env.example` for the only automation variables n8n/Make need.

## Omar must do this manually

### Make the website visible live from GitHub Actions + Netlify

1. Log in to Netlify and open your Scores4AI site.
2. Copy the Netlify **Site ID** from **Site configuration → General → Site details**.
3. Create a Netlify personal access token in **User settings → Applications → Personal access tokens**.
4. In GitHub, open the repository and go to **Settings → Secrets and variables → Actions → New repository secret**.
5. Add these repository secrets:
   - `NETLIFY_AUTH_TOKEN` = your Netlify personal access token
   - `NETLIFY_SITE_ID` = your Netlify Site ID
6. Push to `main` or `work`, or run **Actions → Netlify live deploy → Run workflow**.
7. Open the completed GitHub Actions run and read the live Netlify URL in the job summary.
8. For pull requests, the workflow posts a Netlify preview URL as a PR comment.

### Use n8n for OpenRouter sync automation

1. Log in to n8n.
2. Import `automation/n8n/openrouter-sync.workflow.json`.
3. Add these n8n environment variables or replace the expressions in the HTTP node:
   - `SCORES4AI_SITE_URL`
   - `OPENROUTER_SYNC_CRON_SECRET`
4. Run the workflow manually once.
5. Confirm the HTTP node returns a JSON response with `source`, `count`, and `models`.
6. Activate the workflow to run every 6 hours.

### Use Make.com instead of n8n

1. Log in to Make.com.
2. Create a scenario with two modules:
   - **Tools → Scheduler** set to every 6 hours.
   - **HTTP → Make a request** configured from `automation/make/openrouter-sync.recipe.json`.
3. Use only these values in Make.com:
   - `SCORES4AI_SITE_URL`
   - `OPENROUTER_SYNC_CRON_SECRET`
4. Do **not** add `OPENROUTER_API_KEY` or `SUPABASE_SERVICE_ROLE_KEY` to Make.com. Netlify already stores those server-side secrets.
5. Run once, verify the JSON response, then turn the scenario on.

## Recommended automation path

Use GitHub Actions + Netlify for live website previews and production deploys. Use n8n for the recurring OpenRouter sync because the workflow is already importable and can be run manually before activation.
