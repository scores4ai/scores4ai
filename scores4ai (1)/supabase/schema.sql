-- Scores4AI production schema
-- Paste this whole file into the Supabase SQL editor if you are not using the Supabase CLI.
-- It creates all core tables, indexes, triggers, scoring helpers, and RLS policies.

create extension if not exists pgcrypto;
create extension if not exists citext;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create type public.review_status as enum ('pending', 'approved', 'rejected');
create type public.submission_status as enum ('pending', 'approved', 'rejected');
create type public.source_kind as enum ('openrouter', 'manual', 'benchmark', 'vendor', 'community');
create type public.pricing_unit as enum ('token', 'request', 'minute', 'image', 'second', 'seat', 'unknown');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username citext unique,
  full_name text,
  avatar_url text,
  website_url text,
  bio text,
  role text not null default 'member' check (role in ('member', 'moderator', 'admin')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.models (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  provider text not null,
  name text not null,
  description text,
  context_window integer,
  modalities text[] not null default '{}',
  tokenizer text,
  input_price_per_million numeric(12, 6),
  output_price_per_million numeric(12, 6),
  cached_input_price_per_million numeric(12, 6),
  pricing_unit public.pricing_unit not null default 'token',
  openrouter_id text unique,
  source public.source_kind not null default 'manual',
  raw_source jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  synced_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.tools (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  developer text,
  category text not null,
  tagline text,
  description text,
  website_url text,
  pricing_label text,
  tags text[] not null default '{}',
  is_open_source boolean not null default false,
  is_agent boolean not null default false,
  is_public boolean not null default true,
  score_overall numeric(5, 2),
  score_components jsonb not null default '{}'::jsonb,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.agents (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid not null unique references public.tools(id) on delete cascade,
  autonomy_level smallint check (autonomy_level between 1 and 5),
  execution_environment text,
  supported_integrations text[] not null default '{}',
  requires_browser boolean not null default false,
  supports_sandbox boolean not null default false,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.reviews (
  id uuid primary key default gen_random_uuid(),
  tool_id uuid references public.tools(id) on delete cascade,
  model_id uuid references public.models(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  rating smallint not null check (rating between 1 and 5),
  title text,
  body text,
  pros text[] not null default '{}',
  cons text[] not null default '{}',
  status public.review_status not null default 'pending',
  helpful_count integer not null default 0 check (helpful_count >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint reviews_target_required check (tool_id is not null or model_id is not null)
);

create table public.comparisons (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete set null,
  title text not null,
  description text,
  tool_ids uuid[] not null default '{}',
  model_ids uuid[] not null default '{}',
  criteria jsonb not null default '{}'::jsonb,
  result jsonb not null default '{}'::jsonb,
  is_public boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint comparisons_has_subjects check (cardinality(tool_ids) > 0 or cardinality(model_ids) > 0)
);

create table public.prompt_lab_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete set null,
  model_id uuid references public.models(id) on delete set null,
  prompt_hash text not null,
  prompt_preview text,
  input_tokens integer not null default 0 check (input_tokens >= 0),
  output_tokens integer not null default 0 check (output_tokens >= 0),
  estimated_cost_usd numeric(12, 6) not null default 0 check (estimated_cost_usd >= 0),
  latency_ms integer check (latency_ms >= 0),
  quality_score numeric(5, 2) check (quality_score between 0 and 100),
  metadata jsonb not null default '{}'::jsonb,
  is_public boolean not null default false,
  created_at timestamptz not null default now()
);

create table public.submitted_tools (
  id uuid primary key default gen_random_uuid(),
  submitted_by uuid references public.profiles(id) on delete set null,
  name text not null,
  developer text,
  category text,
  website_url text,
  description text,
  submitter_notes text,
  status public.submission_status not null default 'pending',
  reviewed_by uuid references public.profiles(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.model_sources (
  id uuid primary key default gen_random_uuid(),
  model_id uuid not null references public.models(id) on delete cascade,
  source public.source_kind not null,
  external_id text,
  url text,
  payload jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (source, external_id)
);

create table public.score_formulas (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text not null,
  weights jsonb not null,
  version integer not null default 1,
  is_active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.score_formulas (slug, name, description, weights, is_active)
values (
  'default-v1',
  'Scores4AI Default v1',
  'Transparent weighted score from community, expert, performance, value, trust, and freshness signals. Each component is 0-100; trend is normalized from -100..100 into 0..100.',
  '{"community":0.20,"expert":0.25,"performance":0.15,"value":0.15,"trust":0.15,"freshness":0.10}'::jsonb,
  true
)
on conflict (slug) do nothing;

create or replace function public.calculate_score_from_components(components jsonb)
returns numeric
language sql
immutable
as $$
  select round((
    coalesce((components->>'community')::numeric, 0) * 0.20 +
    coalesce((components->>'expert')::numeric, 0) * 0.25 +
    coalesce((components->>'performance')::numeric, 0) * 0.15 +
    coalesce((components->>'value')::numeric, 0) * 0.15 +
    coalesce((components->>'trust')::numeric, 0) * 0.15 +
    coalesce((components->>'freshness')::numeric, 0) * 0.10
  )::numeric, 2);
$$;

create or replace function public.estimate_prompt_cost_usd(
  input_tokens integer,
  output_tokens integer,
  input_price_per_million numeric,
  output_price_per_million numeric
)
returns numeric
language sql
immutable
as $$
  select round((
    greatest(coalesce(input_tokens, 0), 0)::numeric / 1000000 * coalesce(input_price_per_million, 0) +
    greatest(coalesce(output_tokens, 0), 0)::numeric / 1000000 * coalesce(output_price_per_million, 0)
  )::numeric, 6);
$$;

create or replace function public.create_profile_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, username, full_name, avatar_url)
  values (
    new.id,
    nullif(new.raw_user_meta_data->>'username', ''),
    nullif(new.raw_user_meta_data->>'full_name', ''),
    nullif(new.raw_user_meta_data->>'avatar_url', '')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.create_profile_for_new_user();

create trigger set_profiles_updated_at before update on public.profiles for each row execute function public.set_updated_at();
create trigger set_models_updated_at before update on public.models for each row execute function public.set_updated_at();
create trigger set_tools_updated_at before update on public.tools for each row execute function public.set_updated_at();
create trigger set_agents_updated_at before update on public.agents for each row execute function public.set_updated_at();
create trigger set_reviews_updated_at before update on public.reviews for each row execute function public.set_updated_at();
create trigger set_comparisons_updated_at before update on public.comparisons for each row execute function public.set_updated_at();
create trigger set_submitted_tools_updated_at before update on public.submitted_tools for each row execute function public.set_updated_at();
create trigger set_score_formulas_updated_at before update on public.score_formulas for each row execute function public.set_updated_at();

create index models_provider_idx on public.models(provider);
create index models_openrouter_id_idx on public.models(openrouter_id);
create index tools_category_idx on public.tools(category);
create index tools_tags_idx on public.tools using gin(tags);
create index reviews_tool_id_idx on public.reviews(tool_id);
create index reviews_model_id_idx on public.reviews(model_id);
create index comparisons_public_idx on public.comparisons(is_public);
create index prompt_lab_results_user_idx on public.prompt_lab_results(user_id);
create index model_sources_model_idx on public.model_sources(model_id);

alter table public.profiles enable row level security;
alter table public.models enable row level security;
alter table public.tools enable row level security;
alter table public.agents enable row level security;
alter table public.reviews enable row level security;
alter table public.comparisons enable row level security;
alter table public.prompt_lab_results enable row level security;
alter table public.submitted_tools enable row level security;
alter table public.model_sources enable row level security;
alter table public.score_formulas enable row level security;

create policy "Profiles are public read" on public.profiles for select using (true);
create policy "Users update own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "Models are public read" on public.models for select using (is_active = true);
create policy "Tools are public read" on public.tools for select using (is_public = true);
create policy "Agents are public read" on public.agents for select using (true);
create policy "Model sources are public read" on public.model_sources for select using (true);
create policy "Active score formulas are public read" on public.score_formulas for select using (is_active = true);

create policy "Approved reviews are public read" on public.reviews for select using (status = 'approved' or auth.uid() = user_id);
create policy "Authenticated users create own reviews" on public.reviews for insert to authenticated with check (auth.uid() = user_id);
create policy "Users update own pending reviews" on public.reviews for update to authenticated using (auth.uid() = user_id and status = 'pending') with check (auth.uid() = user_id and status = 'pending');
create policy "Users delete own pending reviews" on public.reviews for delete to authenticated using (auth.uid() = user_id and status = 'pending');

create policy "Public comparisons are readable" on public.comparisons for select using (is_public = true or auth.uid() = user_id);
create policy "Users create own comparisons" on public.comparisons for insert to authenticated with check (auth.uid() = user_id);
create policy "Users update own comparisons" on public.comparisons for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users delete own comparisons" on public.comparisons for delete to authenticated using (auth.uid() = user_id);

create policy "Public prompt lab results are readable" on public.prompt_lab_results for select using (is_public = true or auth.uid() = user_id);
create policy "Users create own prompt lab results" on public.prompt_lab_results for insert to authenticated with check (auth.uid() = user_id);
create policy "Users delete own prompt lab results" on public.prompt_lab_results for delete to authenticated using (auth.uid() = user_id);

create policy "Users can read own submissions" on public.submitted_tools for select using (auth.uid() = submitted_by);
create policy "Authenticated users submit tools" on public.submitted_tools for insert to authenticated with check (auth.uid() = submitted_by);
create policy "Users update own pending submissions" on public.submitted_tools for update to authenticated using (auth.uid() = submitted_by and status = 'pending') with check (auth.uid() = submitted_by and status = 'pending');

-- Admin/moderator helper policies. Service-role requests bypass RLS for sync jobs and moderation automation.
create policy "Moderators manage reviews" on public.reviews for all to authenticated using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('moderator','admin'))) with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('moderator','admin')));
create policy "Admins manage catalog" on public.tools for all to authenticated using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')) with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'));
create policy "Admins manage models" on public.models for all to authenticated using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')) with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'));
create policy "Admins manage agents" on public.agents for all to authenticated using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')) with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'));
create policy "Admins manage submissions" on public.submitted_tools for all to authenticated using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('moderator','admin'))) with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('moderator','admin')));
create policy "Admins manage score formulas" on public.score_formulas for all to authenticated using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')) with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'));

-- Automatic RLS guard for future public tables. New tables in public get RLS enabled automatically.
create or replace function public.enable_rls_for_new_public_tables()
returns event_trigger
language plpgsql
security definer
as $$
declare
  obj record;
begin
  for obj in select * from pg_event_trigger_ddl_commands()
  loop
    if obj.schema_name = 'public' and obj.object_type = 'table' then
      execute format('alter table %s enable row level security', obj.object_identity);
    end if;
  end loop;
end;
$$;

drop event trigger if exists scores4ai_enable_rls_on_create_table;
create event trigger scores4ai_enable_rls_on_create_table
on ddl_command_end
when tag in ('CREATE TABLE', 'CREATE TABLE AS')
execute function public.enable_rls_for_new_public_tables();

create or replace function public.ensure_public_table_rls()
returns table(table_name text, rls_enabled boolean)
language plpgsql
security definer
as $$
declare
  tbl record;
begin
  for tbl in
    select schemaname, tablename
    from pg_tables
    where schemaname = 'public'
  loop
    execute format('alter table %I.%I enable row level security', tbl.schemaname, tbl.tablename);
  end loop;

  return query
  select c.relname::text, c.relrowsecurity
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r'
  order by c.relname;
end;
$$;
