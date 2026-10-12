# P0-02 - Reuse the existing backend (no new Supabase project)
Owner: HUMAN
Time box: 10 min

## Goal
The new frontend can talk to the SAME live backend as the old app.

## Steps
1. Vercel -> the OLD project (bachatbuddy-hq) -> Settings -> Environment Variables.
2. Find `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` (click the eye icon to view the value).
3. In your new repo folder: copy `.env.example` to `.env` and paste those two values.
4. Check: `VITE_SUPABASE_URL` must be `https://anminqetakxavgwnvrqa.supabase.co` (the address hard-coded in the Setu file). If it is different, STOP and tell Claude.
5. Do NOT run any `supabase ...` command and do NOT open the Supabase SQL editor for changes.

## Acceptance
- `.env` has both values and `git status` does NOT list `.env` (it is ignored).
