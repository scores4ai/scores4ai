create extension if not exists pgcrypto;

create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.ai_categories (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null unique,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ai_tools (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  tagline text,
  description text not null,
  category_id uuid not null references public.ai_categories(id) on delete restrict,
  subcategory text,
  website_url text,
  logo_url text,
  pricing_type text not null check (pricing_type in ('Free','Freemium','Paid','Open Source','Enterprise')),
  starting_price numeric(10,2),
  free_plan boolean not null default false,
  best_for text,
  strengths text,
  weaknesses text,
  supported_platforms text[] not null default '{}',
  open_source boolean not null default false,
  api_available boolean not null default false,
  featured boolean not null default false,
  editor_pick boolean not null default false,
  last_verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ai_tool_scores (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid not null unique references public.ai_tools(id) on delete cascade,
  benchmark_score numeric(5,2) not null check (benchmark_score between 0 and 100),
  community_score numeric(5,2) not null check (community_score between 0 and 100),
  programmer_score numeric(5,2) not null check (programmer_score between 0 and 100),
  design_score numeric(5,2) not null check (design_score between 0 and 100),
  ease_of_use_score numeric(5,2) not null check (ease_of_use_score between 0 and 100),
  value_score numeric(5,2) not null check (value_score between 0 and 100),
  overall_score numeric(5,2) not null check (overall_score between 0 and 100),
  confidence_score numeric(5,2) not null check (confidence_score between 0 and 100),
  scoring_version text not null,
  source_note text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ai_tool_pricing (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid not null references public.ai_tools(id) on delete cascade,
  plan_name text not null,
  monthly_price numeric(10,2),
  annual_price numeric(10,2),
  currency text not null default 'USD',
  billing_notes text,
  is_current boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(tool_id, plan_name)
);

create table if not exists public.ai_tool_reviews (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid not null references public.ai_tools(id) on delete cascade,
  reviewer_name text,
  reviewer_role text,
  rating numeric(5,2) not null check (rating between 0 and 100),
  review_title text,
  review_body text,
  review_source text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ai_tool_benchmarks (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid not null references public.ai_tools(id) on delete cascade,
  benchmark_name text not null,
  benchmark_score numeric(5,2) not null check (benchmark_score between 0 and 100),
  benchmark_date date,
  source_url text,
  source_note text,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_tool_trending_snapshots (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid not null references public.ai_tools(id) on delete cascade,
  snapshot_date date not null,
  trend_score numeric(5,2) not null check (trend_score between 0 and 100),
  rank_delta integer not null default 0,
  mention_count integer not null default 0,
  created_at timestamptz not null default now(),
  unique(tool_id, snapshot_date)
);

create index if not exists idx_ai_categories_slug on public.ai_categories(slug);
create index if not exists idx_ai_tools_slug on public.ai_tools(slug);
create index if not exists idx_ai_tools_category on public.ai_tools(category_id);
create index if not exists idx_ai_tools_featured on public.ai_tools(featured);
create index if not exists idx_ai_tools_editor_pick on public.ai_tools(editor_pick);
create index if not exists idx_ai_tool_scores_overall on public.ai_tool_scores(overall_score desc);
create index if not exists idx_ai_tool_trending_score on public.ai_tool_trending_snapshots(trend_score desc);

alter table public.ai_categories enable row level security;
alter table public.ai_tools enable row level security;
alter table public.ai_tool_scores enable row level security;
alter table public.ai_tool_pricing enable row level security;
alter table public.ai_tool_reviews enable row level security;
alter table public.ai_tool_benchmarks enable row level security;
alter table public.ai_tool_trending_snapshots enable row level security;

drop policy if exists "Public read ai_categories" on public.ai_categories;
create policy "Public read ai_categories" on public.ai_categories for select using (true);
drop policy if exists "Public read ai_tools" on public.ai_tools;
create policy "Public read ai_tools" on public.ai_tools for select using (true);
drop policy if exists "Public read ai_tool_scores" on public.ai_tool_scores;
create policy "Public read ai_tool_scores" on public.ai_tool_scores for select using (true);
drop policy if exists "Public read ai_tool_pricing" on public.ai_tool_pricing;
create policy "Public read ai_tool_pricing" on public.ai_tool_pricing for select using (true);
drop policy if exists "Public read ai_tool_reviews" on public.ai_tool_reviews;
create policy "Public read ai_tool_reviews" on public.ai_tool_reviews for select using (true);
drop policy if exists "Public read ai_tool_benchmarks" on public.ai_tool_benchmarks;
create policy "Public read ai_tool_benchmarks" on public.ai_tool_benchmarks for select using (true);
drop policy if exists "Public read ai_tool_trending_snapshots" on public.ai_tool_trending_snapshots;
create policy "Public read ai_tool_trending_snapshots" on public.ai_tool_trending_snapshots for select using (true);

drop policy if exists "Service role manage ai_categories" on public.ai_categories;
create policy "Service role manage ai_categories" on public.ai_categories for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
drop policy if exists "Service role manage ai_tools" on public.ai_tools;
create policy "Service role manage ai_tools" on public.ai_tools for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
drop policy if exists "Service role manage ai_tool_scores" on public.ai_tool_scores;
create policy "Service role manage ai_tool_scores" on public.ai_tool_scores for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
drop policy if exists "Service role manage ai_tool_pricing" on public.ai_tool_pricing;
create policy "Service role manage ai_tool_pricing" on public.ai_tool_pricing for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
drop policy if exists "Service role manage ai_tool_reviews" on public.ai_tool_reviews;
create policy "Service role manage ai_tool_reviews" on public.ai_tool_reviews for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
drop policy if exists "Service role manage ai_tool_benchmarks" on public.ai_tool_benchmarks;
create policy "Service role manage ai_tool_benchmarks" on public.ai_tool_benchmarks for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
drop policy if exists "Service role manage ai_tool_trending_snapshots" on public.ai_tool_trending_snapshots;
create policy "Service role manage ai_tool_trending_snapshots" on public.ai_tool_trending_snapshots for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create trigger trg_ai_categories_updated before update on public.ai_categories for each row execute function public.touch_updated_at();
create trigger trg_ai_tools_updated before update on public.ai_tools for each row execute function public.touch_updated_at();
create trigger trg_ai_tool_scores_updated before update on public.ai_tool_scores for each row execute function public.touch_updated_at();
create trigger trg_ai_tool_pricing_updated before update on public.ai_tool_pricing for each row execute function public.touch_updated_at();
create trigger trg_ai_tool_reviews_updated before update on public.ai_tool_reviews for each row execute function public.touch_updated_at();
