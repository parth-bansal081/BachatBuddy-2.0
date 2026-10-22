"""Plain language (English / Hinglish) -> validated Policy. The model only translates words into rules;
all money math happens later in engine.py."""
from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from ..config import CATEGORIES
from ..llm import LlmClient, extract_json
from .models import Policy

MAX_TEXT = 1000

POLICY_SYSTEM = (
    "You turn a person's money rules, written in English or Hinglish, into JSON rules for a budgeting engine.\n"
    "Supported rule types (nothing else exists):\n"
    '1. {"type":"save_percent","percent":<number 0-100>,"label":"Savings"}  set aside a percent of every income credit.\n'
    '2. {"type":"category_cap","category":"<category>","monthly_limit":<rupees>}  spending limit per calendar month.\n'
    '3. {"type":"bill_reserve","name":"<bill name>","amount":<rupees>,"due_day":<1-31>}  keep money aside for a monthly bill.\n'
    "Allowed categories for category_cap: " + ", ".join(c for c in CATEGORIES if c != "Income") + ".\n"
    "Map everyday words to categories: khana/food/restaurant/delivery -> Food & Dining; ration/sabzi/groceries -> Groceries; "
    "bijli/electricity/phone/recharge/gas -> Utilities; auto/cab/petrol/travel -> Transport; "
    "kapde/online shopping -> Shopping; movies/OTT -> Entertainment; dawai/doctor -> Medical; fees/courses -> Education.\n"
    "Amounts are Indian rupees: 5k = 5000, 1.5k = 1500, 1 lakh = 100000. Every rule is monthly.\n"
    "Anything that is not one of the three rule types (investing, weekly or daily limits, limits for one named shop, "
    "time-of-day limits) must go into the list `unsupported` as a short sentence. Never invent rules or numbers.\n"
    'Reply with ONLY this JSON and nothing else: {"policy": {"name": "<short name>", "rules": [...]} or null, '
    '"unsupported": ["..."]}. Use null for policy when no supported rule is present.\n'
    "Examples:\n"
    'Input: har income ka 10% bachao, khana pe 3000 se zyada mat kharch karo, rent 6000 har mahine 1 tarikh ko\n'
    'Output: {"policy":{"name":"My money rules","rules":[{"type":"save_percent","percent":10,"label":"Savings"},'
    '{"type":"category_cap","category":"Food & Dining","monthly_limit":3000},'
    '{"type":"bill_reserve","name":"Rent","amount":6000,"due_day":1}]},"unsupported":[]}\n'
    'Input: Save 20% of my salary and keep groceries under 5k a month\n'
    'Output: {"policy":{"name":"My money rules","rules":[{"type":"save_percent","percent":20,"label":"Savings"},'
    '{"type":"category_cap","category":"Groceries","monthly_limit":5000}]},"unsupported":[]}\n'
    'Input: invest 5000 in mutual funds every month and no Zomato after 10pm\n'
    'Output: {"policy":null,"unsupported":["Invest 5000 in mutual funds every month","No Zomato after 10pm"]}'
)


class CompileResult(BaseModel):
    ok: bool
    policy: Policy | None = None
    unsupported: list[str] = []
    message: str | None = None
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


def compile_policy(text: str, llm: LlmClient) -> CompileResult:
    """Raises LlmUnavailable if the model API fails. Never guesses: invalid output becomes ok=False."""
    text = (text or "").strip()
    if not text:
        return CompileResult(ok=False, message="Write at least one rule first.")
    if len(text) > MAX_TEXT:
        return CompileResult(ok=False, message=f"Please keep it under {MAX_TEXT} characters.")

    calls = prompt_tokens = completion_tokens = 0
    user = text
    last_error = ""
    for _ in range(2):  # one retry with the validation error shown to the model
        reply, usage = llm.complete(POLICY_SYSTEM, user)
        calls += 1
        prompt_tokens += usage.prompt_tokens
        completion_tokens += usage.completion_tokens
        try:
            payload = extract_json(reply)
            raw_unsupported = payload.get("unsupported", [])
            unsupported = [str(u) for u in raw_unsupported if isinstance(u, str)] if isinstance(raw_unsupported, list) else []
            raw_policy = payload.get("policy")
            if raw_policy is None:
                return CompileResult(
                    ok=False, unsupported=unsupported, llm_calls=calls, prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    message="None of those rules can be set up yet." if unsupported else "No rules found in that text.",
                )
            policy = Policy.model_validate(raw_policy)
            return CompileResult(
                ok=True, policy=policy, unsupported=unsupported, llm_calls=calls,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            )
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)[:300]
            user = f"{text}\n\nYour previous answer was invalid ({last_error}). Return corrected JSON only."
    return CompileResult(
        ok=False, llm_calls=calls, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        message="Could not turn that into valid rules. Try rephrasing it more simply.",
    )


def policy_to_json(policy: Policy) -> str:
    return json.dumps(policy.model_dump(), ensure_ascii=False, indent=2)
