import json

import pytest

from bb.llm import LlmUnavailable, Usage
from bb.policy.compiler import compile_policy


class Scripted:
    """Returns the scripted replies in order and records what it was asked."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.asked = []

    def complete(self, system, user):
        self.asked.append(user)
        return self.replies.pop(0), Usage(100, 40)


GOOD = json.dumps({
    "policy": {"name": "My money rules", "rules": [
        {"type": "save_percent", "percent": 10, "label": "Savings"},
        {"type": "category_cap", "category": "Food & Dining", "monthly_limit": 3000},
    ]},
    "unsupported": [],
})


def test_valid_reply_compiles():
    r = compile_policy("har income ka 10% bachao, khana pe 3000 se zyada mat kharch karo", Scripted(GOOD))
    assert r.ok and r.policy is not None and len(r.policy.rules) == 2
    assert r.llm_calls == 1 and r.prompt_tokens == 100


def test_reply_with_think_block_and_fences_compiles():
    r = compile_policy("save 10%", Scripted("<think>hmm</think>```json\n" + GOOD + "\n```"))
    assert r.ok


def test_invalid_first_reply_is_retried_with_the_error_shown():
    bad = json.dumps({"policy": {"name": "x", "rules": [{"type": "category_cap", "category": "Space", "monthly_limit": 5}]}, "unsupported": []})
    llm = Scripted(bad, GOOD)
    r = compile_policy("food limit", llm)
    assert r.ok and r.llm_calls == 2
    assert "previous answer was invalid" in llm.asked[1]


def test_two_invalid_replies_give_a_clean_failure_not_a_guess():
    r = compile_policy("???", Scripted("not json", "still not json"))
    assert r.ok is False and r.policy is None and r.llm_calls == 2 and r.message


def test_unsupported_only_returns_not_ok_with_the_list():
    reply = json.dumps({"policy": None, "unsupported": ["Invest 5000 monthly"]})
    r = compile_policy("invest 5000 monthly", Scripted(reply))
    assert r.ok is False and r.unsupported == ["Invest 5000 monthly"] and r.llm_calls == 1


def test_partly_supported_keeps_policy_and_reports_the_rest():
    reply = json.dumps({"policy": {"name": "p", "rules": [{"type": "save_percent", "percent": 10}]}, "unsupported": ["No Zomato after 10pm"]})
    r = compile_policy("save 10% and no Zomato after 10pm", Scripted(reply))
    assert r.ok and r.unsupported == ["No Zomato after 10pm"]


def test_empty_and_too_long_text_never_call_the_model():
    llm = Scripted()
    assert compile_policy("   ", llm).ok is False
    assert compile_policy("x" * 1001, llm).ok is False
    assert llm.asked == []


def test_api_failure_propagates():
    class Down:
        def complete(self, system, user):
            raise LlmUnavailable("down")

    with pytest.raises(LlmUnavailable):
        compile_policy("save 10%", Down())
