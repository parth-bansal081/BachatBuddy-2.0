# P2-01 - Create the policies table (additive SQL)
Owner: HUMAN
Time box: 5 min

## Goal
One new table `policies` in the live Supabase project. Nothing existing changes.

## Steps
1. Supabase dashboard -> the LIVE project -> SQL Editor -> New query (a fresh "Untitled query").
2. Open `db/0003_policies.sql` in Notepad or VS Code, Ctrl+A, Ctrl+C, paste into the editor, click Run.

## Acceptance
- Result says "Success. No rows returned".
- Table Editor shows `policies` with RLS enabled.
- The old app still works.
