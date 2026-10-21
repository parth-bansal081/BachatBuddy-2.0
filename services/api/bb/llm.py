"""Token Factory client + strict JSON parsing. Nothing here knows about the database."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from .config import CATEGORIES, env


class LlmUnavailable(Exception):
    """The model API failed (network, auth, quota). Never cache anything when this happens."""


# Reasoning models consume tokens in the completion window.
# Keep a single constant so every call uses a budget large enough for thinking + output.
MAX_TOKENS = 8000


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LlmClient(Protocol):
    def complete(self, system: str, user: str) -> tuple[str, Usage]: ...


SYSTEM_PROMPT = (
    "You classify Indian bank-statement merchants. You receive a JSON list of items. "
    "Each item has an id, a cleaned merchant text, and a sample of the raw narration.\n"
    "For EVERY item return: id (same integer), name (the merchant's human-readable name, "
    "properly capitalised, or the person's name for person-to-person payments), "
    "category (exactly one of: " + ", ".join(CATEGORIES) + "), "
    "confidence (0 to 1; use below 0.7 when unsure).\n"
    "Rules: a person's name with no business context is Transfers. Salary or interest credits are Income. "
    "If you cannot tell, use Miscellaneous with a low confidence. Never invent a merchant.\n"
    'Answer with ONLY a JSON object of the form {"items":[{"id":0,"name":"...","category":"...","confidence":0.9}]} '
    "and nothing else: no explanation, no markdown."
)


def build_user_prompt(items: list[dict[str, object]]) -> str:
    return json.dumps(items, ensure_ascii=False)


_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"```(?:json)?", re.IGNORECASE)


def extract_json(text: str) -> dict[str, object]:
    """Pull the first JSON object out of a model reply (handles <think> blocks and code fences)."""
    cleaned = _FENCE.sub("", _THINK.sub("", text)).strip()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("no JSON object in model reply")
    obj, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    if not isinstance(obj, dict):
        raise ValueError("model reply JSON is not an object")
    return obj


class TokenFactoryClient:
    """OpenAI-compatible chat client. Needs TOKEN_FACTORY_API_KEY, TOKEN_FACTORY_BASE_URL and a model id."""

    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI  # imported here so tests never need the network

        api_key = env("TOKEN_FACTORY_API_KEY")
        base_url = env("TOKEN_FACTORY_BASE_URL")
        self.model = model or env("TOKEN_FACTORY_MODEL_FAST") or env("TOKEN_FACTORY_MODEL")
        if not (api_key and base_url and self.model):
            raise LlmUnavailable(
                "Missing TOKEN_FACTORY_API_KEY / TOKEN_FACTORY_BASE_URL / TOKEN_FACTORY_MODEL_FAST (see docs/LLM.md)"
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, system: str, user: str) -> tuple[str, Usage]:
        try:
            reply = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0,
                max_tokens=MAX_TOKENS,
            )
        except Exception as exc:  # network, auth, quota: surface as one error type
            raise LlmUnavailable(f"{type(exc).__name__}: {exc}") from exc
        choice = reply.choices[0]
        text = (choice.message.content or "").strip()
        finish_reason = getattr(choice, "finish_reason", None)
        if not text or finish_reason == "length":
            raise LlmUnavailable(f"empty content or length finish_reason: {finish_reason}")
        usage = Usage(
            prompt_tokens=getattr(reply.usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(reply.usage, "completion_tokens", 0) or 0,
        )
        return text, usage
