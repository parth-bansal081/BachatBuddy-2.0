from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .config import CATEGORIES


class LlmItem(BaseModel):
    """One merchant classification returned by the model (validated strictly)."""

    id: int
    name: str = Field(min_length=1, max_length=80)
    category: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("category")
    @classmethod
    def category_must_be_known(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"unknown category: {value}")
        return value


class CacheRow(BaseModel):
    key: str
    clean_name: str
    category: str
    confidence: float
    needs_review: bool
    source: str  # 'llm' | 'fallback' | 'user' | 'rule'
    model: str | None = None


class EnrichResult(BaseModel):
    narrations_seen: int = 0
    new_narrations: int = 0
    new_keys: int = 0
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    fallbacks: int = 0
    needs_review: int = 0
