-- 0003_policies.sql  (ADDITIVE ONLY: one new table, nothing existing is touched)
-- Run once in the Supabase SQL editor of the live project, after 0002.

create table if not exists public.policies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  source_text text,
  rules jsonb not null check (jsonb_typeof(rules) = 'array'),
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- A user has at most ONE active policy; older ones stay as inactive history.
create unique index if not exists policies_one_active_per_user
  on public.policies (user_id) where active;

alter table public.policies enable row level security;

drop policy if exists "own policies" on public.policies;
create policy "own policies" on public.policies
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
