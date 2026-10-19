"""Measures accuracy and token cost of the enrichment on a labelled CSV, using the REAL model.

Run from services/api with a filled .env:   python eval/run_eval.py
Writes eval/last_run.json. Never prints keys.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bb.enrich import classify_keys  # noqa: E402
from bb.llm import TokenFactoryClient  # noqa: E402
from bb.normalize import merchant_key  # noqa: E402


def squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main() -> None:
    load_dotenv()
    path = Path(__file__).with_name("eval_merchants.csv")
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    key_for = {r["raw_narration"]: (merchant_key(r["raw_narration"]) or "unknown") for r in rows}
    samples: dict[str, str] = {}
    for narration, key in key_for.items():
        samples.setdefault(key, narration)
    keys = sorted(set(key_for.values()) - {"unknown"})

    llm = TokenFactoryClient()
    predicted_rows, usage, calls, fallbacks = classify_keys(keys, samples, llm, llm.model)
    predicted = {r.key: r for r in predicted_rows}

    category_ok = name_ok = 0
    misses: list[dict[str, str]] = []
    for row in rows:
        pred = predicted.get(key_for[row["raw_narration"]])
        if pred is None:
            misses.append({"raw": row["raw_narration"], "why": "no prediction"})
            continue
        cat_match = pred.category == row["expected_category"]
        a, b = squash(pred.clean_name), squash(row["expected_name"])
        name_match = bool(a and b and (a in b or b in a))
        category_ok += cat_match
        name_ok += name_match
        if not (cat_match and name_match):
            misses.append(
                {
                    "raw": row["raw_narration"],
                    "expected": f'{row["expected_name"]} / {row["expected_category"]}',
                    "got": f"{pred.clean_name} / {pred.category} ({pred.confidence:.2f})",
                }
            )

    total_tokens = usage.prompt_tokens + usage.completion_tokens
    summary = {
        "model": llm.model,
        "transactions": len(rows),
        "distinct_keys_sent_to_model": len(keys),
        "llm_calls": calls,
        "fallbacks": fallbacks,
        "category_accuracy": round(category_ok / len(rows), 3),
        "name_accuracy": round(name_ok / len(rows), 3),
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "tokens_per_1000_transactions": round(total_tokens / len(rows) * 1000),
        "misses": misses[:40],
    }
    Path(__file__).with_name("last_run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "misses"}, indent=2))
    print(f"misses recorded: {len(misses)} (see eval/last_run.json)")


if __name__ == "__main__":
    main()
