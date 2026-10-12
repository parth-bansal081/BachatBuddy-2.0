# P0-06 - First Nemotron call on Token Factory
Owner: HUMAN fills docs/LLM.md and .env; AGENT runs the script
Time box: 30 min

## Goal
One successful reply from a Nemotron model through Nebius Token Factory.

## Human steps
1. In the Token Factory console, create an API key.
2. Fill `docs/LLM.md` with the BASE_URL and exact model IDs from the console/docs.
3. Put `TOKEN_FACTORY_API_KEY`, `TOKEN_FACTORY_BASE_URL`, `TOKEN_FACTORY_MODEL` in your local `.env` (a Nemotron model ID).

## Agent steps
Read first: AGENTS.md, docs/LLM.md. May create/edit: nothing (the script already exists in `scripts/llm_smoke.py`).
1. `git checkout -b task/P0-06`
2. `python3 -m venv .venv && . .venv/bin/activate && pip install openai`
3. Load the variables without printing them: `set -a; . ./.env; set +a`
4. `python scripts/llm_smoke.py`

## Acceptance (paste real output; never paste the API key)
- Output has a `MODEL:` line naming a Nemotron model and `REPLY:` containing "BachatBuddy online".

## STOP and ask if
- docs/LLM.md has an empty field, or the provider's docs say the API is not OpenAI-compatible.
