# P2-02 - Run the 79 tests
Owner: AGENT
Time box: 10 min

## Goal
All Phase 1 + Phase 2 tests pass. The code is already written: you do NOT write code.

## Read first
- AGENTS.md, docs/POLICY_SPEC.md

## May create/edit (nothing else)
- Nothing.

## Must NOT touch
- Every file in the repo. Do not edit any `.py` file, test, or requirements.txt.

## Steps
1. `git checkout -b task/P2-02`
2. `cd services/api`
3. Activate the venv (PowerShell: `.venv\Scripts\Activate.ps1`)
4. `python -m pytest -q`

## Acceptance (paste real output)
- `python -m pytest -q` -> `79 passed`
- `git status --short` -> empty

## STOP and ask if
- Any test fails. Paste the full failure. Do NOT edit code or tests to make it pass.
