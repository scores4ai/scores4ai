-- Scores4AI production cache schema.
-- Keep private service-role writes on the server; expose only read-safe views to clients.
create extension if not exists pgcrypto;

create table if not exists public.openrouter_model_cache (
  id text primary key,
  canonical_slug text,
  name text not null,
  description text,
  context_length integer,
  input_modalities text[] not null default '{}',
  output_modalities text[] not null default '{}',
  supported_parameters text[] not null default '{}',
  prompt_price_per_token numeric(20, 12) not null default 0,
  completion_price_per_token numeric(20, 12) not null default 0,
  raw jsonb not null,
  fetched_at timestamptz not null default now()
);

create table if not exists public.score_snapshots (
  id uuid primary key default gen_random_uuid(),
  tool_id text not null,
  source text not null check (source in ('benchmark', 'community', 'programmer')),
  score numeric(5, 2) not null check (score >= 0 and score <= 100),
  evidence_count integer not null default 0 check (evidence_count >= 0),
  methodology_version text not null,
  raw jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists score_snapshots_tool_source_created_idx
  on public.score_snapshots (tool_id, source, created_at desc);

create table if not exists public.vetted_programmers (
  user_id uuid primary key,
  public_handle text not null unique,
  verification_status text not null check (verification_status in ('pending', 'vetted', 'suspended')),
  evidence_url text,
  created_at timestamptz not null default now()
);

alter table public.openrouter_model_cache enable row level security;
alter table public.score_snapshots enable row level security;
alter table public.vetted_programmers enable row level security;

create policy "public can read cached model metadata"
  on public.openrouter_model_cache for select using (true);

create policy "public can read score snapshots"
  on public.score_snapshots for select using (true);

create policy "public can read vetted handles only"
  on public.vetted_programmers for select using (verification_status = 'vetted');
