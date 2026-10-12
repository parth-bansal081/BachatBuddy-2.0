# P0-04 - Make it compile and run locally
Owner: AGENT
Time box: 30 min

## Goal
`npm install`, typecheck and build succeed, and the dev server starts.

## Read first
- AGENTS.md, docs/SETU_PORT.md, package.json

## May create/edit (nothing else)
- `package-lock.json` (created by npm)
- `src/pages/Auth.tsx`, `src/pages/Dashboard.tsx`, `src/pages/LoadingInsights.tsx`, `src/App.tsx`, `src/main.tsx` - ONLY to fix a compile error, and never inside the block marked "SETU CALLBACK HANDLING"
- `tailwind.config.ts`, `src/index.css` - only to fix a build error

## Must NOT touch
- Everything in PROTECTED_PATHS.txt, `src/components/ui/*`, `src/lib/utils.ts`, `src/config/setuFlow.ts`

## Steps
1. `git checkout -b task/P0-04`
2. `npm install`
3. `npm run typecheck`
4. `npm run build`
5. `npm run dev` - confirm it prints a local URL, then stop it with Ctrl+C.
6. If a type error is inside a protected or copied file, DO NOT fix it. Paste the exact error text and STOP.
7. `git add -A && git commit -m "P0-04: install deps, verify build"`

## Acceptance (paste real output)
- `npm run typecheck` -> no errors
- `npm run build` -> ends with "built in ..."
- `git diff --stat main..HEAD` -> only package-lock.json (and files you were allowed to fix)

## STOP and ask if
- Any error mentions a protected file, or you feel the need to add a dependency.
