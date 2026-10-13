-- 0002_enrichment.sql  (ADDITIVE ONLY: creates new objects, never touches existing tables)
-- Run once in the Supabase SQL editor of the live project.
--
-- Why a cache keyed by merchant instead of columns on `transactions`:
-- the Setu sync deletes and re-inserts every transaction, so anything stored on those rows would be lost.
-- Enrichment lives in two separate tables and is joined back through a view.

create table if not exists public.merchant_cache (
  user_id uuid not null references auth.users(id) on delete cascade,
  key text not null,
  clean_name text not null,
  category text not null,
  confidence real not null default 0,
  needs_review boolean not null default false,
  source text not null check (source in ('llm', 'user', 'rule', 'fallback')),
  model text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, key)
);

create table if not exists public.narration_map (
  user_id uuid not null references auth.users(id) on delete cascade,
  raw_narration text not null,
  key text not null,
  primary key (user_id, raw_narration),
  foreign key (user_id, key) references public.merchant_cache (user_id, key) on delete cascade
);
create index if not exists narration_map_key_idx on public.narration_map (user_id, key);

alter table public.merchant_cache enable row level security;
alter table public.narration_map enable row level security;

drop policy if exists "own merchant_cache" on public.merchant_cache;
create policy "own merchant_cache" on public.merchant_cache
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "own narration_map" on public.narration_map;
create policy "own narration_map" on public.narration_map
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Read model for the app: every transaction plus its enriched name/category (prefixed `enriched_`
-- so it can never clash with columns that already exist on `transactions`).
create or replace view public.transactions_enriched
with (security_invoker = true) as
select
  t.*,
  coalesce(c.clean_name, t.merchant) as enriched_merchant,
  coalesce(c.category, t.category) as enriched_category,
  coalesce(c.needs_review, false) as enriched_needs_review,
  c.source as enriched_source
from public.transactions t
left join public.narration_map m on m.user_id = t.user_id and m.raw_narration = t.merchant
left join public.merchant_cache c on c.user_id = m.user_id and c.key = m.key;
