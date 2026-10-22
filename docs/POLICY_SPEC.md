# Phase 2 - Money brain spec

## What it does
A person writes money rules in plain English or Hinglish. A model turns the words into JSON rules (and nothing else).
A deterministic engine tests those rules on the person's real history (backtest) and later runs them live.
The model never does arithmetic and never sees amounts: all money math is `bb/policy/engine.py`.

## The three rule types (nothing else exists yet)
| Type | Fields | Meaning |
|---|---|---|
| `save_percent` | percent (0-100), label | set aside that percent of every income credit |
| `category_cap` | category, monthly_limit | warn at 80% and flag when a category passes the limit in one calendar month |
| `bill_reserve` | name, amount, due_day (1-31) | keep that amount aside for a monthly bill; day 31 in a short month means the last day |

A policy has 1 to 10 rules. Save percentages may not add up past 100. One cap per category. `Income` cannot be capped.
Anything else a user asks for (investing, daily or weekly limits, one named shop, time of day) is returned as `unsupported`
so the app can say so honestly instead of guessing.

## Conventions
- Credits are positive, debits negative (the Setu sync does this). Money is `Decimal` rupees, rounded half-up to paise.
- Income = a credit whose category is `Income`. Credits from people (`Transfers`) are not income.
- Categories come from enrichment; transactions the old sync categorised with its old names are mapped
  (Food -> Food & Dining, Lifestyle -> Shopping, Bills -> Utilities); anything unknown becomes Miscellaneous.
- Backtest warns when no income was found or when over 30% of spending is uncategorised.

## API (all need the user's bearer token; rows are protected by row-level security)
- `POST /policy/compile` {text} -> {ok, policy, unsupported, message, tokens}. Uses the stronger model. One retry on invalid output.
- `POST /policy/backtest` {policy} -> months, events, totals, a headline sentence built in code, warnings.
- `POST /policy` {policy, source_text} -> {id}. Becomes the single active policy; the old one stays as history.
- `GET /policy/active`, `GET /policy/safe-to-spend`.

## Files
- `db/0003_policies.sql` (additive: one new table), `fixtures/example_policy.json`
- `services/api/bb/policy/` models.py, engine.py, compiler.py; `bb/data.py` (database access)
- `services/api/eval/policy_cases.json` + `run_policy_eval.py` (13 English and Hinglish sentences with the expected rules)

## Decision rule for Hinglish
Run `P2-04`. If Hinglish exact-match is below 0.75, do NOT claim Hinglish in the demo or README. Say "English" and keep Hinglish as a stretch.

## Known limits
- Safe-to-spend uses income received this month, or the expected income you pass in. It does not know account balances.
- Caps are per calendar month and per category only.
- Sandbox amounts are scaled down by the old sync, so example limits may need tuning to your data.
