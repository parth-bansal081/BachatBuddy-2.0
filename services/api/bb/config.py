from __future__ import annotations

import os

# ONE category list for the whole product. Do not add or rename without a task card.
CATEGORIES: tuple[str, ...] = (
    "Food & Dining",
    "Groceries",
    "Utilities",
    "Transport",
    "Shopping",
    "Entertainment",
    "Investment",
    "Medical",
    "Rent & Housing",
    "Education",
    "Transfers",
    "Income",
    "Miscellaneous",
)

REVIEW_CONFIDENCE_THRESHOLD = 0.7  # below this, the user is asked to confirm
BATCH_SIZE = 25  # merchants per LLM call
MAX_TEXT_LEN = 80
UNKNOWN_KEY = "unknown"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()
