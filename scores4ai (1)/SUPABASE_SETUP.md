# Supabase setup for Scores4AI

## Codex already handled this

- Added `supabase/migrations/0001_initial_scores4ai.sql` with all requested tables:
  - `profiles`
  - `models`
  - `tools`
  - `agents`
  - `reviews`
  - `comparisons`
  - `prompt_lab_results`
  - `submitted_tools`
  - `model_sources`
- Added `supabase/schema.sql` as a single pasteable SQL file for the Supabase SQL Editor.
- Added Row Level Security policies for public reads, owner-managed records, moderator/admin flows, and server-side service-role sync.
- Added an event trigger that automatically enables RLS on future tables created in the `public` schema.
- Added `public.ensure_public_table_rls()` as a backup function to enable and audit RLS across all current public tables.
- Added transparent score and Prompt Lab cost SQL helper functions.

## Omar must do this manually

1. Log in to Supabase.
2. Create a new Supabase project.
3. Open **SQL Editor → New query**.
4. Paste the full contents of `supabase/schema.sql`.
5. Click **Run** once. You do **not** need to create tables one by one.
6. If Supabase reports that the automatic event trigger cannot be created due to permissions:
   - Keep the rest of the schema.
   - Run this anytime you add public tables manually:

```sql
select * from public.ensure_public_table_rls();
```

7. Go to **Project Settings → API** and copy:
   - Project URL → `VITE_SUPABASE_URL` and `SUPABASE_URL`
   - anon public key → `VITE_SUPABASE_ANON_KEY`
   - service_role secret key → `SUPABASE_SERVICE_ROLE_KEY`
8. Add those values to Netlify environment variables.
9. Never paste the `service_role` key into frontend code, browser console snippets, or `VITE_` variables.

## Optional verification queries

```sql
select tablename, rowsecurity
from pg_tables
where schemaname = 'public'
order by tablename;
```

```sql
select * from public.score_formulas where is_active = true;
```

```sql
select public.estimate_prompt_cost_usd(1000, 500, 3, 15);
```
