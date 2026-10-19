# P1-02 - Set up Python and run the 31 tests
Owner: AGENT
Time box: 20 min

## Goal
The Phase 1 code installs and all tests pass on this machine. The code is already written: you do NOT write code.

## Read first
- AGENTS.md, docs/ENRICHMENT_SPEC.md

## May create/edit (nothing else)
- `services/api/.venv/` (created by the commands below; git ignores it)

## Must NOT touch
- Every file in the repo. Do not edit any `.py` file, any test, `requirements.txt`, or the SQL.

## Steps
1. `git checkout -b task/P1-02`
2. `cd services/api`
3. `python -m venv .venv`
4. Activate it. PowerShell: `.venv\Scripts\Activate.ps1`   Git Bash: `source .venv/Scripts/activate`
5. `pip install -r requirements.txt`
6. `python -m pytest -q`

## Acceptance (paste real output)
- `python --version` -> 3.11 or newer
- `python -m pytest -q` -> `31 passed`
- `git status --short` -> empty (nothing to commit)

## STOP and ask if
- Any test fails. Paste the full failure text. Do NOT edit code or tests to make it pass.
- `pip install` fails. Paste the error. Do not change versions in requirements.txt.
