-- Scores4AI full Supabase setup: auth-ready schema, RLS, triggers, indexes.
create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.enable_rls_for_new_public_tables()
returns event_trigger language plpgsql as $$
declare obj record;
begin
  for obj in select * from pg_event_trigger_ddl_commands() loop
    if obj.schema_name = 'public' and obj.object_type = 'table' then
      execute format('alter table %s enable row level security', obj.object_identity);
    end if;
  end loop;
end;
$$;

drop event trigger if exists trg_enable_rls_for_new_public_tables;
create event trigger trg_enable_rls_for_new_public_tables
  on ddl_command_end when tag in ('CREATE TABLE')
  execute function public.enable_rls_for_new_public_tables();

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_url text,
  role text not null default 'user' check (role in ('user','reviewer','admin')),
  preferred_use_case text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.models (
  id uuid primary key default gen_random_uuid(),
  openrouter_id text unique,
  canonical_slug text,
  name text not null,
  provider text not null,
  description text,
  context_window integer,
  input_modalities text[] not null default '{}',
  output_modalities text[] not null default '{}',
  tokenizer text,
  instruct_type text,
  supported_parameters text[] not null default '{}',
  prompt_price_per_million numeric(12,6) not null default 0,
  completion_price_per_million numeric(12,6) not null default 0,
  request_price numeric(12,6) not null default 0,
  max_completion_tokens integer,
  is_moderated boolean,
  api_available boolean not null default true,
  website_url text,
  raw_openrouter_payload jsonb not null default '{}'::jsonb,
  source_status text not null default 'cached' check (source_status in ('live','cached','estimated','demo')),
  scoring jsonb not null default '{}'::jsonb,
  openrouter_created_at timestamptz,
  expires_at text,
  last_synced_at timestamptz,
  pricing_last_synced_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.tools (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name text not null,
  provider text,
  category text not null,
  description text,
  website_url text,
  pricing_type text check (pricing_type in ('Free','Freemium','Paid','Open Source')),
  source_status text not null default 'community' check (source_status in ('live','cached','estimated','demo','community')),
  submitted_by uuid references public.profiles(id) on delete set null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agents (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name text not null,
  provider text,
  description text,
  website_url text,
  autonomy_level integer check (autonomy_level between 0 and 5),
  integrations text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.reviews (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  subject_type text not null check (subject_type in ('model','tool','agent')),
  subject_id uuid not null,
  rating numeric(3,1) not null check (rating >= 0 and rating <= 10),
  title text,
  body text,
  verification_status text not null default 'Needs Review' check (verification_status in ('Verified','Estimated','Community Submitted','Needs Review')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(profile_id, subject_type, subject_id)
);

create table if not exists public.comparisons (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references public.profiles(id) on delete set null,
  title text not null,
  subject_ids uuid[] not null,
  weights jsonb not null default '{}'::jsonb,
  result_snapshot jsonb not null default '{}'::jsonb,
  is_public boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.prompt_lab_results (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references public.profiles(id) on delete set null,
  prompt text not null,
  selected_model_ids text[] not null default '{}',
  result_type text not null default 'Estimated' check (result_type in ('Estimated','Live API Result')),
  estimated_input_tokens integer not null default 0,
  estimated_output_tokens integer not null default 0,
  estimated_cost numeric(12,6) not null default 0,
  results jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.submitted_tools (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references public.profiles(id) on delete set null,
  name text not null,
  website_url text,
  category text,
  description text,
  submission_type text not null default 'tool' check (submission_type in ('model','tool','agent')),
  status text not null default 'Needs Review' check (status in ('Verified','Estimated','Community Submitted','Needs Review')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.model_sources (
  id uuid primary key default gen_random_uuid(),
  model_id uuid references public.models(id) on delete cascade,
  source_type text not null check (source_type in ('official_pricing','benchmark','api','community','documentation')),
  source_url text not null,
  verification_status text not null default 'Needs Review' check (verification_status in ('Verified','Estimated','Community Submitted','Needs Review')),
  last_checked_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(source_type, source_url)
);

create table if not exists public.bookmarks (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  subject_type text not null check (subject_type in ('model','tool','agent','comparison')),
  subject_id uuid not null,
  created_at timestamptz not null default now(),
  unique(profile_id, subject_type, subject_id)
);

create table if not exists public.comments (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  subject_type text not null check (subject_type in ('model','tool','agent','review','comparison')),
  subject_id uuid not null,
  body text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.saved_comparisons (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  comparison_id uuid not null references public.comparisons(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique(profile_id, comparison_id)
);

alter table public.profiles enable row level security;
alter table public.models enable row level security;
alter table public.tools enable row level security;
alter table public.agents enable row level security;
alter table public.reviews enable row level security;
alter table public.comparisons enable row level security;
alter table public.prompt_lab_results enable row level security;
alter table public.submitted_tools enable row level security;
alter table public.model_sources enable row level security;
alter table public.bookmarks enable row level security;
alter table public.comments enable row level security;
alter table public.saved_comparisons enable row level security;

create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role = 'admin')
$$;

drop policy if exists "Public read models" on public.models;
create policy "Public read models" on public.models for select using (true);
drop policy if exists "Public read tools" on public.tools;
create policy "Public read tools" on public.tools for select using (true);
drop policy if exists "Public read agents" on public.agents;
create policy "Public read agents" on public.agents for select using (true);
drop policy if exists "Public read sources" on public.model_sources;
create policy "Public read sources" on public.model_sources for select using (true);
drop policy if exists "Public read verified reviews" on public.reviews;
create policy "Public read verified reviews" on public.reviews for select using (verification_status in ('Verified','Community Submitted'));
drop policy if exists "Public read public comparisons" on public.comparisons;
create policy "Public read public comparisons" on public.comparisons for select using (is_public = true);

drop policy if exists "Users read own profile" on public.profiles;
create policy "Users read own profile" on public.profiles for select using (auth.uid() = id or public.is_admin());
drop policy if exists "Users update own profile" on public.profiles;
create policy "Users update own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists "Users manage own reviews" on public.reviews;
create policy "Users manage own reviews" on public.reviews for all using (auth.uid() = profile_id or public.is_admin()) with check (auth.uid() = profile_id or public.is_admin());
drop policy if exists "Users manage own comparisons" on public.comparisons;
create policy "Users manage own comparisons" on public.comparisons for all using (auth.uid() = profile_id or public.is_admin()) with check (auth.uid() = profile_id or public.is_admin());
drop policy if exists "Users manage own prompt results" on public.prompt_lab_results;
create policy "Users manage own prompt results" on public.prompt_lab_results for all using (auth.uid() = profile_id or public.is_admin()) with check (auth.uid() = profile_id or public.is_admin());
drop policy if exists "Users submit tools" on public.submitted_tools;
create policy "Users submit tools" on public.submitted_tools for insert with check (auth.uid() = profile_id);
drop policy if exists "Users read own submissions" on public.submitted_tools;
create policy "Users read own submissions" on public.submitted_tools for select using (auth.uid() = profile_id or public.is_admin());
drop policy if exists "Users manage own bookmarks" on public.bookmarks;
create policy "Users manage own bookmarks" on public.bookmarks for all using (auth.uid() = profile_id) with check (auth.uid() = profile_id);
drop policy if exists "Users manage own comments" on public.comments;
create policy "Users manage own comments" on public.comments for all using (auth.uid() = profile_id or public.is_admin()) with check (auth.uid() = profile_id or public.is_admin());
drop policy if exists "Users manage own saved comparisons" on public.saved_comparisons;
create policy "Users manage own saved comparisons" on public.saved_comparisons for all using (auth.uid() = profile_id) with check (auth.uid() = profile_id);

drop policy if exists "Admins manage models" on public.models;
create policy "Admins manage models" on public.models for all using (public.is_admin()) with check (public.is_admin());
drop policy if exists "Admins manage sources" on public.model_sources;
create policy "Admins manage sources" on public.model_sources for all using (public.is_admin()) with check (public.is_admin());

create or replace function public.create_profile_for_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', new.email), new.raw_user_meta_data->>'avatar_url')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.create_profile_for_new_user();

drop trigger if exists profiles_updated_at on public.profiles;
create trigger profiles_updated_at before update on public.profiles for each row execute function public.set_updated_at();
drop trigger if exists models_updated_at on public.models;
create trigger models_updated_at before update on public.models for each row execute function public.set_updated_at();
drop trigger if exists tools_updated_at on public.tools;
create trigger tools_updated_at before update on public.tools for each row execute function public.set_updated_at();
drop trigger if exists agents_updated_at on public.agents;
create trigger agents_updated_at before update on public.agents for each row execute function public.set_updated_at();
drop trigger if exists reviews_updated_at on public.reviews;
create trigger reviews_updated_at before update on public.reviews for each row execute function public.set_updated_at();
drop trigger if exists comparisons_updated_at on public.comparisons;
create trigger comparisons_updated_at before update on public.comparisons for each row execute function public.set_updated_at();
drop trigger if exists submitted_tools_updated_at on public.submitted_tools;
create trigger submitted_tools_updated_at before update on public.submitted_tools for each row execute function public.set_updated_at();
drop trigger if exists comments_updated_at on public.comments;
create trigger comments_updated_at before update on public.comments for each row execute function public.set_updated_at();

create index if not exists models_provider_idx on public.models(provider);
create index if not exists models_openrouter_id_idx on public.models(openrouter_id);
create index if not exists models_last_synced_idx on public.models(last_synced_at desc);
create index if not exists tools_category_idx on public.tools(category);
create index if not exists agents_name_idx on public.agents(name);
create index if not exists reviews_subject_idx on public.reviews(subject_type, subject_id);
create index if not exists comparisons_profile_idx on public.comparisons(profile_id, created_at desc);
create index if not exists prompt_lab_profile_idx on public.prompt_lab_results(profile_id, created_at desc);
create index if not exists submitted_tools_status_idx on public.submitted_tools(status, created_at desc);
create index if not exists model_sources_model_idx on public.model_sources(model_id, source_type);
create index if not exists bookmarks_profile_idx on public.bookmarks(profile_id, created_at desc);
create index if not exists comments_subject_idx on public.comments(subject_type, subject_id, created_at desc);
