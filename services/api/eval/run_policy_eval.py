"""Checks how well the model turns plain language (English + Hinglish) into rules, with the REAL model.

Run from services/api with a filled .env:   python eval/run_policy_eval.py
Writes eval/last_policy_run.json. Never prints keys.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bb.config import env  # noqa: E402
from bb.llm import TokenFactoryClient  # noqa: E402
from bb.policy.compiler import compile_policy  # noqa: E402


def canon(rule: dict[str, Any]) -> tuple[Any, ...]:
    kind = rule["type"]
    if kind == "save_percent":
        return ("save", float(rule["percent"]))
    if kind == "category_cap":
        return ("cap", rule["category"], float(rule["monthly_limit"]))
    return ("bill", float(rule["amount"]), int(rule["due_day"]))  # bill name is free text, so it is not compared


def main() -> None:
    load_dotenv()
    cases = json.loads(Path(__file__).with_name("policy_cases.json").read_text(encoding="utf-8"))
    llm = TokenFactoryClient(model=env("TOKEN_FACTORY_MODEL_SMART") or env("TOKEN_FACTORY_MODEL"))

    exact = 0
    by_lang: dict[str, list[int]] = {}
    tp = fp = fn = 0
    prompt_tokens = completion_tokens = 0
    failures: list[dict[str, Any]] = []
    for case in cases:
        result = compile_policy(case["text"], llm)
        prompt_tokens += result.prompt_tokens
        completion_tokens += result.completion_tokens
        got = {canon(r.model_dump()) for r in result.policy.rules} if result.policy else set()
        want = {canon(r) for r in case["expected"]["rules"]}
        unsupported_ok = len(result.unsupported) == case["expected"]["unsupported"]
        ok = got == want and unsupported_ok
        exact += ok
        by_lang.setdefault(case["lang"], []).append(int(ok))
        tp += len(got & want)
        fp += len(got - want)
        fn += len(want - got)
        if not ok:
            failures.append({"text": case["text"], "expected": sorted(map(str, want)), "got": sorted(map(str, got)),
                             "unsupported_got": len(result.unsupported), "unsupported_expected": case["expected"]["unsupported"],
                             "message": result.message})

    summary = {
        "model": llm.model,
        "cases": len(cases),
        "exact_match": round(exact / len(cases), 3),
        "by_language": {lang: round(sum(v) / len(v), 3) for lang, v in by_lang.items()},
        "rule_precision": round(tp / (tp + fp), 3) if tp + fp else 0.0,
        "rule_recall": round(tp / (tp + fn), 3) if tp + fn else 0.0,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "failures": failures,
    }
    Path(__file__).with_name("last_policy_run.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "failures"}, indent=2))
    print(f"failures recorded: {len(failures)} (see eval/last_policy_run.json)")


if __name__ == "__main__":
    main()
