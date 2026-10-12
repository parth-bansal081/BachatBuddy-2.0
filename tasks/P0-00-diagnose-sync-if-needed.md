# P0-00 - OPTIONAL: diagnose the sync (only if the golden path fails in P0-04)
Owner: HUMAN
Time box: 20 min

## When to do this
ONLY if, after the new frontend is live, you link the bank and no transactions appear.
If the golden path works, skip this card.

## Goal
Find out what the old app does after the Setu approval, so the new frontend can copy it.

## Steps
1. Open the OLD deployment from Vercel's Deployments tab (every old deployment keeps its own URL), or temporarily promote it back to production.
2. Chrome -> F12 -> Network -> tick "Preserve log". Sign in. Link Bank Account -> Proceed to Link. Setu screen: phone 9999999999, OTP 123456, approve.
3. Write down: (a) the full web address you land on, including everything after `?`; (b) whether a request named `sync-bank-data` appears in the Network tab; (c) whether transactions appear by themselves.
4. Send these three answers to Claude. Do not edit any code yourself.
