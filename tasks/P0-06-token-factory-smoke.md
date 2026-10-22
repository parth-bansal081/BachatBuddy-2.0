# P0-06 - First Nemotron call on Token Factory (v2: works in PowerShell)
Owner: HUMAN fills docs/LLM.md and .env; AGENT runs the script
Time box: 30 min

## Goal
One successful reply from a Nemotron model through Nebius Token Factory.

## Human steps
1. Token Factory console: create an API key. Never paste it into chat, a doc or a commit.
2. Fill `docs/LLM.md` with the BASE_URL and exact model IDs from the console/docs (no key in it).
3. In the repo-root `.env` fill: TOKEN_FACTORY_API_KEY, TOKEN_FACTORY_BASE_URL, TOKEN_FACTORY_MODEL, TOKEN_FACTORY_MODEL_FAST (a small Nano-class id), TOKEN_FACTORY_MODEL_SMART (a stronger id, can be the same as the others for now).

## Agent steps
Read first: AGENTS.md, docs/LLM.md. May create/edit: nothing (the script exists). Do NOT open, read or print `.env`.
1. `git checkout -b task/P0-06`
2. `cd services/api`, activate the venv (PowerShell: `.venv\Scripts\Activate.ps1`), then `cd ..\..`
3. `python scripts/llm_smoke.py`   (the script loads `.env` itself)

## Acceptance (paste real output; never paste the API key)
- Output has a `MODEL:` line naming a Nemotron model and `REPLY:` containing "BachatBuddy online".

## STOP and ask if
- docs/LLM.md has an empty field, the script reports a missing variable, or the API returns an error. Paste the error text WITHOUT any key.
