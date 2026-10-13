"""Core enrichment logic. Pure Python: the database and the LLM are passed in, so it is fully testable."""
from __future__ import annotations

from typing import Iterable, Protocol

from pydantic import ValidationError

from .config import BATCH_SIZE, REVIEW_CONFIDENCE_THRESHOLD, UNKNOWN_KEY
from .llm import LlmClient, SYSTEM_PROMPT, Usage, build_user_prompt, extract_json
from .normalize import merchant_key
from .schemas import CacheRow, EnrichResult, LlmItem


class Store(Protocol):
    def distinct_narrations(self) -> list[str]: ...
    def mapped(self) -> dict[str, str]:
        """narration -> key for everything already mapped."""
        ...
    def cached_keys(self) -> set[str]:
        """Keys that are final (source llm/user/rule). Keys stored as 'fallback' are NOT included, so they are retried."""
        ...
    def upsert_cache(self, rows: list[CacheRow]) -> None: ...
    def upsert_map(self, pairs: list[tuple[str, str]]) -> None: ...


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _fallback(key: str) -> CacheRow:
    return CacheRow(
        key=key,
        clean_name=key.title(),
        category="Miscellaneous",
        confidence=0.0,
        needs_review=True,
        source="fallback",
        model=None,
    )


def _unknown_row() -> CacheRow:
    # Final on purpose (source 'rule'): a narration with nothing useful left is never sent to the model.
    return CacheRow(
        key=UNKNOWN_KEY,
        clean_name="Unknown",
        category="Miscellaneous",
        confidence=0.0,
        needs_review=True,
        source="rule",
        model=None,
    )


def classify_keys(
    keys: list[str], samples: dict[str, str], llm: LlmClient, model_name: str
) -> tuple[list[CacheRow], Usage, int, int]:
    """Classify merchant keys. Returns (rows, total usage, llm_calls, fallback_count).

    Raises LlmUnavailable if the API itself fails: nothing must be cached in that case.
    Individual items the model gets wrong become 'fallback' rows (retried on the next run).
    """
    rows: list[CacheRow] = []
    total = Usage()
    calls = 0
    fallbacks = 0
    for batch in _chunks(keys, BATCH_SIZE):
        items = [{"id": i, "text": key, "sample": samples.get(key, "")[:120]} for i, key in enumerate(batch)]
        answers: dict[int, LlmItem] = {}
        for attempt in range(2):  # one retry for malformed output
            text, usage = llm.complete(SYSTEM_PROMPT, build_user_prompt(items))
            calls += 1
            total.prompt_tokens += usage.prompt_tokens
            total.completion_tokens += usage.completion_tokens
            try:
                payload = extract_json(text)
            except ValueError:
                continue
            raw_items = payload.get("items")
            if not isinstance(raw_items, list):
                continue
            for raw in raw_items:
                try:
                    item = LlmItem.model_validate(raw)
                except ValidationError:
                    continue
                if 0 <= item.id < len(batch):
                    answers[item.id] = item
            if len(answers) == len(batch):
                break
        for index, key in enumerate(batch):
            item = answers.get(index)
            if item is None:
                rows.append(_fallback(key))
                fallbacks += 1
                continue
            rows.append(
                CacheRow(
                    key=key,
                    clean_name=item.name.strip(),
                    category=item.category,
                    confidence=item.confidence,
                    needs_review=item.confidence < REVIEW_CONFIDENCE_THRESHOLD or item.category == "Miscellaneous",
                    source="llm",
                    model=model_name,
                )
            )
    return rows, total, calls, fallbacks


def enrich_user(store: Store, llm: LlmClient, model_name: str) -> EnrichResult:
    narrations = [n for n in store.distinct_narrations() if n and n.strip()]
    mapped = store.mapped()
    new_narrations = [n for n in narrations if n not in mapped]

    key_by_narration = {n: (merchant_key(n) or UNKNOWN_KEY) for n in new_narrations}
    all_pairs = {**mapped, **key_by_narration}  # narration -> key (old and new)
    cached = store.cached_keys()
    # Pending = keys with no FINAL answer yet: brand-new keys AND keys stored as 'fallback' (retried).
    pending = sorted({k for k in all_pairs.values() if k not in cached})

    samples: dict[str, str] = {}
    for narration, key in all_pairs.items():
        samples.setdefault(key, narration)

    rows: list[CacheRow] = []
    usage = Usage()
    calls = 0
    fallbacks = 0
    if UNKNOWN_KEY in pending:
        rows.append(_unknown_row())
    keys_for_llm = [k for k in pending if k != UNKNOWN_KEY]
    if keys_for_llm:
        llm_rows, usage, calls, fallbacks = classify_keys(keys_for_llm, samples, llm, model_name)
        rows.extend(llm_rows)

    if rows:
        store.upsert_cache(rows)  # first: the map has a foreign key to the cache
    if key_by_narration:
        store.upsert_map(list(key_by_narration.items()))

    return EnrichResult(
        narrations_seen=len(narrations),
        new_narrations=len(new_narrations),
        new_keys=len(pending),
        llm_calls=calls,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        fallbacks=fallbacks,
        needs_review=sum(1 for r in rows if r.needs_review),
    )
