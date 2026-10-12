# Setu - how we keep it safe

DECISION: the backend is NOT rebuilt. It stays exactly as it is in the OLD Supabase project:
the Edge Functions (create-consent, setu-webhook, sync-bank-data), their secrets, the tables, and the Setu dashboard settings.
The new app is only a new frontend that talks to that same backend.

## Frozen frontend files (copied byte for byte by `scripts/port-setu.sh`, never edited)
- src/lib/setuService.ts
- src/components/BankSyncButton.tsx
- Generic shadcn pieces they import: src/components/ui/button.tsx, src/components/ui/dialog.tsx, src/lib/utils.ts

## Must stay exactly like this in the new frontend
- Route `/loading-insights` exists, behind a login check, and goes to `/dashboard` (as the old app does: it drops the query string).
- `Dashboard.tsx` keeps the block marked "SETU CALLBACK HANDLING".
- `Auth.tsx` keeps the `setu_consent_pending` handling after sign-in.
- `src/config/setuFlow.ts` stays `FORWARD_SETU_PARAMS = false` (= old behaviour). Only a human may change it, and only after the diagnosis in task P0-00.

## Environment
- The new Vercel deployment must use the SAME `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` as the old deployment.
- The new frontend takes over the SAME Vercel domain, so the Setu redirect allow-list and `create-consent` need no change.

## Never (agents AND humans, until a task card says otherwise)
- `supabase functions deploy`, `supabase db push`, `supabase secrets set` against the old project.
- Editing anything in the Setu dashboard.

## Rollback
Vercel keeps every old deployment. If anything is wrong after the swap, promote the previous deployment back to production (Deployments tab).
