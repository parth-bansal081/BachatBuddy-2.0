# P0-05 - Put the new frontend on the same domain, run the golden path, freeze
Owner: HUMAN
Time box: 45 min

## Goal
The new frontend runs on the existing production domain and the Setu golden path works.

## Before you start (safety)
- Vercel -> old project -> Deployments tab. Note which deployment is currently "Production". That is your way back.

## Steps
1. Merge the reviewed task branches into `main`: `git checkout main && git merge task/P0-03 && git merge task/P0-04 && git push`.
2. Vercel -> old project -> Settings -> Git -> Disconnect, then connect the NEW repository (production branch `main`). Keep the existing environment variables as they are.
3. Trigger a deploy (a push to `main`, or "Redeploy" in the Deployments tab). Wait until it shows Ready.
4. Open https://bachatbuddy-hq.vercel.app and run the golden path (see docs/PLAN.md).
5. If it works: `bash scripts/protect-freeze.sh` (type FREEZE), then `git tag setu-ported-ok && git push --tags`.
6. If it does NOT work: Deployments tab -> the old deployment from "Before you start" -> menu -> Promote to Production. The old app is back in about a minute. Then do P0-00 and send Claude the results.

## Acceptance
- After logging in and linking the sandbox bank, accounts and transactions appear on the new dashboard.
- `bash scripts/verify-protected.sh` prints "OK: protected files intact".
- Tag `setu-ported-ok` exists on GitHub.
