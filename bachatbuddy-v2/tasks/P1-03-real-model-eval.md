# P1-03 - Measure accuracy and token cost with the REAL model
Owner: HUMAN fills `.env`; AGENT runs the script
Time box: 20 min
Needs: P0-06 done (Token Factory works)

## Goal
Real numbers: category accuracy and tokens per 1000 transactions.

## Human steps
1. Open the repo-root `.env` (never paste its values anywhere). Make sure these are filled:
   TOKEN_FACTORY_API_KEY, TOKEN_FACTORY_BASE_URL, TOKEN_FACTORY_MODEL_FAST (the Nano-class model id from docs/LLM.md).
2. The other variables (SUPABASE_*, BB_TEST_*) are not needed for this task.

## Agent steps
Read first: AGENTS.md, docs/ENRICHMENT_SPEC.md. May create/edit: `services/api/eval/last_run.json` (written by the script). Must NOT touch: any other file, especially the prompt in `bb/llm.py`.
1. `git checkout -b task/P1-03`
2. `cd services/api`, activate the venv (see P1-02).
3. `python eval/run_eval.py`
4. `git add services/api/eval/last_run.json && git commit -m "P1-03: first real eval run"`

## Acceptance (paste real output; never print keys)
- The script prints a JSON summary with `model`, `category_accuracy`, `name_accuracy`, `fallbacks`, `tokens_per_1000_transactions`.
- Targets: category_accuracy >= 0.90 and fallbacks = 0. If lower, do NOT change any code or prompt: report the numbers and the first 10 entries of `misses` from eval/last_run.json.

## STOP and ask if
- The script says a variable is missing, or the model API returns an error.
