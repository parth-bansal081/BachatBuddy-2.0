from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from ..config import CATEGORIES


class SavePercentRule(BaseModel):
    """Set aside `percent` of every income credit."""

    type: Literal["save_percent"] = "save_percent"
    percent: float = Field(gt=0, le=100)
    label: str = Field(default="Savings", min_length=1, max_length=40)


class CategoryCapRule(BaseModel):
    """Warn at 80% and flag when a category's spending in one calendar month passes `monthly_limit`."""

    type: Literal["category_cap"] = "category_cap"
    category: str
    monthly_limit: float = Field(gt=0)

    @field_validator("category")
    @classmethod
    def category_must_be_spendable(cls, value: str) -> str:
        if value not in CATEGORIES or value == "Income":
            raise ValueError(f"cannot cap category: {value}")
        return value


class BillReserveRule(BaseModel):
    """Keep `amount` aside for a bill due on `due_day` of every month."""

    type: Literal["bill_reserve"] = "bill_reserve"
    name: str = Field(min_length=1, max_length=60)
    amount: float = Field(gt=0)
    due_day: int = Field(ge=1, le=31)


Rule = Annotated[Union[SavePercentRule, CategoryCapRule, BillReserveRule], Field(discriminator="type")]


class Policy(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    rules: list[Rule] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def rules_must_be_consistent(self) -> "Policy":
        total_pct = sum(r.percent for r in self.rules if isinstance(r, SavePercentRule))
        if total_pct > 100:
            raise ValueError("save percentages add up to more than 100")
        caps = [r.category for r in self.rules if isinstance(r, CategoryCapRule)]
        if len(caps) != len(set(caps)):
            raise ValueError("more than one cap for the same category")
        return self
