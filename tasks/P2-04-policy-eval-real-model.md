# P2-04 - Does the model understand English and Hinglish rules?
Owner: HUMAN fills `.env`; AGENT runs the script
Time box: 20 min
Needs: P0-06 done (Token Factory works), TOKEN_FACTORY_MODEL_SMART filled

## Agent steps
Read first: AGENTS.md, docs/POLICY_SPEC.md. May create/edit: `services/api/eval/last_policy_run.json` (written by the script). Must NOT touch: any other file, especially the prompt in `bb/policy/compiler.py`. Do NOT open, read or print `.env`.
1. `git checkout -b task/P2-04`
2. `cd services/api`, activate the venv.
3. `python eval/run_policy_eval.py`
4. `git add services/api/eval/last_policy_run.json && git commit -m "P2-04: first real policy eval"`

## Acceptance (paste real output; never print keys)
- The script prints `exact_match`, `by_language`, `rule_precision`, `rule_recall`, token counts.
- Targets: overall exact_match >= 0.85 and hinglish >= 0.75. If lower, do NOT change any code or prompt: report the numbers and the first 5 entries of `failures`.

## STOP and ask if
- The script says a variable is missing or the API returns an error (paste the text without any key).
