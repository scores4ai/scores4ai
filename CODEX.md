# Codex Instructions for Scores4AI

## Project mission
Scores4AI is a transparent AI ranking and comparison platform: Rotten Tomatoes + Consumer Reports + IMDb/Product Hunt/Hugging Face for AI tools, models, agents, and APIs.

## Primary goal
Make the site production-ready with real data retrieval, clear source labels, and a simple review workflow using GitHub PRs and Netlify Deploy Previews.

## Repository structure
The app lives inside:

```bash
scores4ai (1)
```

Use this directory for local commands unless editing repository-root config files.

## Standard commands
Before finishing any task, run the relevant checks:

```bash
cd "scores4ai (1)"
npm install
npm run lint
npm run build
npm run verify:production-build
```

If a command fails, fix the issue before marking the task complete. If a command cannot be run in the environment, explain exactly why.

## Data rules
- Never present fake/demo rows as live rankings.
- Demo rows must be clearly labeled as demo.
- Estimated pricing/scoring must be clearly labeled as estimated.
- Live OpenRouter data and cached Supabase data must be labeled separately.
- Browser/client code must not expose service-role keys or private API keys.

## Environment variables
Expected variables may include:

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
OPENROUTER_API_KEY=
SUPABASE_SERVICE_ROLE_KEY=
```

Do not hard-code secrets. Use Netlify environment variables, GitHub secrets, or Codex environment secrets.

## Netlify expectations
- Root `netlify.toml` is the source of truth for deployment.
- Build base: `scores4ai (1)`
- Build command: `npm run build`
- Publish directory: `dist/client`
- Node version: `22`

Every PR should be compatible with Netlify Deploy Previews.

## PR workflow
For every meaningful change:
1. Create a focused branch.
2. Make the smallest safe changes.
3. Run build/checks.
4. Open a PR with a clear summary and testing notes.
5. Wait for Netlify Deploy Preview.
6. If reviewer feedback or Netlify Drawer feedback exists, fix it in the same PR.

## Review/annotation workflow
The intended human review flow is:

1. Codex opens a GitHub PR.
2. Netlify creates a Deploy Preview for that PR.
3. The reviewer opens the preview and leaves visual feedback using Netlify Drawer when available.
4. Codex reads the PR comments/feedback and pushes fixes to the same branch.

## Current priority
Fix any issue that causes demo seed data to appear when real Supabase/OpenRouter data should be used. Validate env-var handling, fallback logic, API routes/functions, and production build behavior.
