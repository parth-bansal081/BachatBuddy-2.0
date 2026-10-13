# P1-04 - Enrich the real sandbox data
Owner: HUMAN
Time box: 30 min
Needs: P0-05 done (new frontend live, bank linked), P1-01 done, P1-02 done, P1-03 done

## Goal
Your sandbox transactions get clean names and categories, and the result survives a re-sync.

## Steps
1. Fill the remaining variables in the repo-root `.env`: SUPABASE_URL (same as VITE_SUPABASE_URL), SUPABASE_ANON_KEY (same value as VITE_SUPABASE_PUBLISHABLE_KEY), BB_TEST_EMAIL and BB_TEST_PASSWORD (your test user).
2. Make sure the test user has transactions: sign in on the live app and link the sandbox bank if needed.
3. Terminal in `services/api` with the venv active: `python -m bb.cli enrich`
4. Run the same command a SECOND time.
5. Supabase SQL editor: `select merchant, enriched_merchant, enriched_category, enriched_needs_review from public.transactions_enriched order by date desc limit 30;`
6. In the app, run "Link Bank Account" again (this re-syncs and re-inserts all transactions), then run `python -m bb.cli enrich` a third time.

## Acceptance
- Run 1 prints `new_keys` greater than 0 and `llm_calls` of 1 or more.
- Run 2 prints `llm_calls: 0`.
- Step 5 shows readable names and categories.
- Run 3 (after the re-sync) prints `llm_calls: 0`: enrichment survived the re-sync.

## Send to Claude
The output of runs 1 and 3, `services/api/eval/last_run.json`, and 10 rows from step 5 (merchant text only, no personal data).
