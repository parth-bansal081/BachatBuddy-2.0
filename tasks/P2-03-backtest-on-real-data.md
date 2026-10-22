# P2-03 - Backtest a policy on your real data (no model key needed)
Owner: HUMAN
Time box: 15 min
Needs: P2-01 done, `.env` has SUPABASE_URL, SUPABASE_ANON_KEY, BB_TEST_EMAIL, BB_TEST_PASSWORD

## Goal
See the engine produce a real headline and monthly table from your sandbox transactions.

## Steps
1. PowerShell in the repo root: `cd services\api` then activate the venv: `.venv\Scripts\Activate.ps1`
2. `python -m bb.cli backtest --policy ..\..\fixtures\example_policy.json`
3. Open `fixtures/example_policy.json`, change a limit (for example Food & Dining to 1500), save, run step 2 again.

## Acceptance
- A headline sentence like "Over N months, this policy would have set aside ...".
- One line per month with income, saved, spent, reserved and caps.
- Changing the limit changes the result.
- If you see a WARNING about uncategorised spending, that is expected before enrichment (P1-04) has run.

## Send to Claude
The headline, the WARNING lines, and the first 3 month lines (numbers only).
