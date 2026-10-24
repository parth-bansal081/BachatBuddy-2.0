-- 0004_actions.sql  (ADDITIVE ONLY: one new table, nothing existing is touched)
-- Run once in the Supabase SQL editor of the live project, after 0003.

create table if not exists public.actions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('set_aside')),
  label text not null,
  amount numeric(12,2) not null check (amount > 0),
  month text not null,
  status text not null check (status in ('pending','approved','rejected')) default 'pending',
  created_at timestamptz not null default now(),
  decided_at timestamptz,
  unique (user_id, kind, label, month)
);

alter table public.actions enable row level security;

drop policy if exists "own actions" on public.actions;
create policy "own actions" on public.actions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Index for efficient pending queries
create index if not exists actions_user_pending_idx
  on public.actions (user_id, status) where status = 'pending';