# P0-01 - Create the new repo from the kit
Owner: HUMAN
Time box: 15 min

## Goal
A new GitHub repo containing this kit, with the commit guard installed.

## Steps
1. github.com -> New repository. Name `bachatbuddy-v2`, Public. Do NOT tick README, .gitignore or license (the kit has them). Create it.
2. Unzip the kit. It creates a `bachatbuddy-v2/` folder. Open a terminal inside it (Windows: right-click in the folder -> "Open Git Bash here").
3. Run, one by one:
   - `git init -b main`
   - `git add -A`
   - `git commit -m "chore: initial kit"`
   - `bash scripts/install-hooks.sh`
   - `git remote add origin <your new repo address>`
   - `git push -u origin main`

## Acceptance
- The GitHub repo page shows the files and `LICENSE`.
- `bash scripts/verify-protected.sh` prints: "no PROTECTED.sha256 yet (before first freeze) - skipping."
