import json

import pytest

from bb.enrich import enrich_user
from bb.llm import LlmUnavailable, Usage
from bb.schemas import CacheRow


class FakeStore:
    def __init__(self, narrations, cache=None, mapped=None):
        self.narrations = list(narrations)
        self.cache = dict(cache or {})  # key -> CacheRow
        self.mapped_pairs = dict(mapped or {})  # narration -> key

    def distinct_narrations(self):
        return list(self.narrations)

    def mapped(self):
        return dict(self.mapped_pairs)

    def cached_keys(self):
        return {k for k, r in self.cache.items() if r.source != "fallback"}

    def upsert_cache(self, rows):
        for r in rows:
            self.cache[r.key] = r

    def upsert_map(self, pairs):
        for n, k in pairs:
            assert k in self.cache, "map must never point at a missing cache row"
            self.mapped_pairs[n] = k


class FakeLlm:
    """Answers from a dict key -> (name, category, confidence). Records every call."""

    def __init__(self, answers, wrap=None):
        self.answers = answers
        self.calls = []
        self.wrap = wrap or (lambda s: s)

    def complete(self, system, user):
        items = json.loads(user)
        self.calls.append(items)
        out = []
        for item in items:
            if item["text"] in self.answers:
                name, cat, conf = self.answers[item["text"]]
                out.append({"id": item["id"], "name": name, "category": cat, "confidence": conf})
        return self.wrap(json.dumps({"items": out})), Usage(100, 50)


NARR = [
    "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment",
    "UPI/DR/998877665544/SWIGGY/HDFC/swiggy@okaxis/Order 1",
    "UPI-ZOMATO-zomato@ybl-YESB0000262-412345678901-UPI",
]
ANSWERS = {"swiggy": ("Swiggy", "Food & Dining", 0.97), "zomato": ("Zomato", "Food & Dining", 0.95)}


def test_one_call_per_distinct_merchant_and_everything_mapped():
    store, llm = FakeStore(NARR), FakeLlm(ANSWERS)
    result = enrich_user(store, llm, "fake-model")
    assert result.narrations_seen == 3 and result.new_keys == 2
    assert result.llm_calls == 1 and len(llm.calls[0]) == 2
    assert set(store.mapped_pairs) == set(NARR)
    assert result.prompt_tokens == 100 and result.completion_tokens == 50


def test_second_run_makes_zero_calls():
    store, llm = FakeStore(NARR), FakeLlm(ANSWERS)
    enrich_user(store, llm, "m")
    again = enrich_user(store, llm, "m")
    assert again.llm_calls == 0 and again.new_narrations == 0


def test_new_narration_for_known_merchant_needs_no_llm():
    store, llm = FakeStore(NARR), FakeLlm(ANSWERS)
    enrich_user(store, llm, "m")
    store.narrations.append("UPI/DR/111111111111/SWIGGY/SBIN/swiggy@paytm/Payment")
    again = enrich_user(store, llm, "m")
    assert again.new_narrations == 1 and again.llm_calls == 0
    assert store.mapped_pairs["UPI/DR/111111111111/SWIGGY/SBIN/swiggy@paytm/Payment"] == "swiggy"


def test_user_corrections_are_never_overwritten():
    user_row = CacheRow(key="swiggy", clean_name="My Tiffin", category="Groceries", confidence=1.0,
                        needs_review=False, source="user")
    store, llm = FakeStore(NARR, cache={"swiggy": user_row}), FakeLlm(ANSWERS)
    enrich_user(store, llm, "m")
    assert store.cache["swiggy"].clean_name == "My Tiffin"
    assert all(item["text"] != "swiggy" for call in llm.calls for item in call)


def test_invalid_category_becomes_fallback_and_is_retried_next_run():
    bad = {"swiggy": ("Swiggy", "Space Travel", 0.9), "zomato": ("Zomato", "Food & Dining", 0.9)}
    store = FakeStore(NARR)
    first = enrich_user(store, FakeLlm(bad), "m")
    assert first.fallbacks == 1 and store.cache["swiggy"].source == "fallback"
    assert store.cache["swiggy"].needs_review is True
    second = enrich_user(store, FakeLlm(ANSWERS), "m")  # model now answers correctly
    assert store.cache["swiggy"].source == "llm" and second.fallbacks == 0


def test_low_confidence_is_flagged_for_review():
    store = FakeStore(NARR[:1])
    enrich_user(store, FakeLlm({"swiggy": ("Swiggy", "Food & Dining", 0.4)}), "m")
    assert store.cache["swiggy"].needs_review is True


def test_think_block_and_fences_in_reply_are_handled():
    wrap = lambda s: "<think>let me see</think>```json\n" + s + "\n```"
    store = FakeStore(NARR)
    result = enrich_user(store, FakeLlm(ANSWERS, wrap=wrap), "m")
    assert result.fallbacks == 0 and store.cache["zomato"].source == "llm"


def test_api_failure_raises_and_caches_nothing():
    class Down:
        def complete(self, system, user):
            raise LlmUnavailable("boom")

    store = FakeStore(NARR)
    with pytest.raises(LlmUnavailable):
        enrich_user(store, Down(), "m")
    assert store.cache == {} and store.mapped_pairs == {}


def test_unparseable_reply_twice_falls_back_without_crashing():
    class Garbage:
        def complete(self, system, user):
            return "no json here", Usage(10, 5)

    store = FakeStore(NARR)
    result = enrich_user(store, Garbage(), "m")
    assert result.fallbacks == 2 and result.llm_calls == 2  # one retry
    assert set(store.mapped_pairs) == set(NARR)


def test_empty_narration_key_uses_unknown_row_without_llm():
    store, llm = FakeStore(["UPI/DR/412345678901"]), FakeLlm({})
    result = enrich_user(store, llm, "m")
    assert result.llm_calls == 0 and store.mapped_pairs["UPI/DR/412345678901"] == "unknown"
    assert store.cache["unknown"].needs_review is True


def test_batches_of_25():
    narrations = [f"UPI/DR/412345678901/SHOP{i}/YESB/s{i}@ybl/Payment" for i in range(60)]
    answers = {f"shop{i}": (f"Shop{i}", "Shopping", 0.9) for i in range(60)}
    store, llm = FakeStore(narrations), FakeLlm(answers)
    result = enrich_user(store, llm, "m")
    assert result.llm_calls == 3 and [len(c) for c in llm.calls] == [25, 25, 10]
