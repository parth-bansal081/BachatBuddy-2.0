# Phase 1 - Enrichment spec (data spine)

## What it does
Turns raw bank narrations (e.g. `UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment`) into a clean merchant name
and one category, at minimal model cost, without ever touching the protected Setu code.

## Why it is built this way
- The Setu sync deletes and re-inserts every transaction, so nothing can be stored on transaction rows.
  Results live in two separate tables and are joined back with the view `transactions_enriched`.
- Cost scales with DISTINCT MERCHANTS, not transactions: a regex shield turns every narration into a stable key
  (`swiggy`), and the model sees each key once. On the 137-row synthetic eval set that is 47 keys.
- The model never does arithmetic and never sees amounts or account numbers: only merchant text.
- The API acts as the signed-in user with the anon key. No service-role key exists anywhere in this project.

## Flow (`bb/enrich.py`)
1. Read distinct narrations from `transactions` (this user, via row-level security).
2. Narrations not yet in `narration_map` get a key from `merchant_key()` (regex shield).
3. Keys without a FINAL answer in `merchant_cache` are pending. Final = source `llm`, `user` or `rule`.
   Keys stored as `fallback` are retried on every run until the model answers them properly.
4. Pending keys go to the model in batches of 25. The reply is parsed strictly; each item is validated alone.
   Invalid items become `fallback` rows (category Miscellaneous, needs_review true).
5. If the model API itself fails, nothing is written and the API returns 502. Never cache a failure as an answer.
6. Rows are upserted: cache first, then the map (foreign key).
7. `source = 'user'` rows (corrections made in the app) are never overwritten.

## Single category list (do not change without a task card)
Food & Dining, Groceries, Utilities, Transport, Shopping, Entertainment, Investment, Medical,
Rent & Housing, Education, Transfers, Income, Miscellaneous. Lives in `services/api/bb/config.py`.

## Review rule
`needs_review = confidence < 0.7 OR category == Miscellaneous`.

## Files
- `db/0002_enrichment.sql`  additive migration (human runs it in the SQL editor)
- `services/api/bb/`  normalize.py, llm.py, enrich.py, store.py, deps.py, main.py, cli.py
- `services/api/tests/`  31 tests, no network needed
- `services/api/eval/`  `eval_merchants.csv` (synthetic, labelled) and `run_eval.py` (real model)

## Known limits
- The eval set is synthetic. After the first real sync, add real narrations from the sandbox data and re-label them.
- Keys include city words for card (POS) narrations, so the same shop in two cities counts as two keys.
- A key the model keeps failing is retried on every run (two model calls each time).
