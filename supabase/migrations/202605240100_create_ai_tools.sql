create extension if not exists pgcrypto;

create table if not exists public.ai_tools (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  category text not null,
  description text not null,
  website_url text,
  overall_score numeric(5,2) not null default 0,
  created_at timestamptz not null default now()
);

alter table public.ai_tools enable row level security;

drop policy if exists "Public read ai_tools" on public.ai_tools;
create policy "Public read ai_tools" on public.ai_tools for select using (true);
