# Supabase Setup — Scores4AI

## Codex already handled this

- Created `supabase/migrations/202605130001_full_scores4ai_setup.sql`.
- Created `supabase/full_setup.sql` for one-shot setup.
- Included tables for profiles, models, tools, agents, reviews, comparisons, prompt lab results, submitted tools, model sources, bookmarks, comments, and saved comparisons.
- Enabled Row Level Security on all public tables.
- Added policies for public reads, authenticated user-owned writes, admin management, and community submissions.
- Added triggers for `updated_at`, profile creation on signup, and automatic RLS for future public tables.
- Added indexes for model lookup, sync freshness, reviews, comparisons, prompt lab history, and community features.

## You must do this manually

1. Create a Supabase project.
2. Open the SQL Editor.
3. Paste and run `supabase/full_setup.sql`, or apply `supabase/migrations/202605130001_full_scores4ai_setup.sql` with the Supabase CLI.
4. Copy these values into Netlify and local `.env`:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
5. Keep `SUPABASE_SERVICE_ROLE_KEY` server-side only.

## Supabase setup checklist

- [ ] Project created.
- [ ] SQL setup completed successfully.
- [ ] RLS enabled on all public tables.
- [ ] Auth signup creates a row in `profiles`.
- [ ] Service role key stored only in Netlify/server environment variables.
- [ ] First OpenRouter model sync completed.

## Refresh cadence

- Models: every 12 hours.
- Pricing: every 24 hours.
- Source rows record `last_checked_at` and verification status.
