# P1-01 - Create the enrichment tables (additive SQL)
Owner: HUMAN
Time box: 10 min

## Goal
Two new tables and one view exist in the live Supabase project. Nothing existing is changed.

## Steps
1. Supabase dashboard -> the LIVE project (the one in VITE_SUPABASE_URL) -> SQL Editor -> New query.
2. First run this READ-ONLY check and confirm all five names come back:
   `select column_name from information_schema.columns where table_schema='public' and table_name='transactions' and column_name in ('user_id','merchant','category','amount','date');`
   If fewer than 5 rows: STOP and send the result to Claude.
3. New query: paste the WHOLE of `db/0002_enrichment.sql` and click Run. It only creates new objects and can be re-run safely.

## Acceptance
- Table Editor shows `merchant_cache` and `narration_map` (RLS enabled).
- `select count(*) from public.transactions_enriched;` runs without error.
- The old app still works (log in, open the dashboard).
