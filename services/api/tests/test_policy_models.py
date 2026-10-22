import pytest
from pydantic import ValidationError

from bb.policy.models import Policy


def policy(*rules):
    return {"name": "p", "rules": list(rules)}


SAVE = {"type": "save_percent", "percent": 10}
CAP = {"type": "category_cap", "category": "Food & Dining", "monthly_limit": 3000}
BILL = {"type": "bill_reserve", "name": "Rent", "amount": 6000, "due_day": 1}


def test_valid_policy_parses_all_three_rule_types():
    p = Policy.model_validate(policy(SAVE, CAP, BILL))
    assert [r.type for r in p.rules] == ["save_percent", "category_cap", "bill_reserve"]


@pytest.mark.parametrize(
    "bad",
    [
        policy({"type": "save_percent", "percent": 0}),
        policy({"type": "save_percent", "percent": 101}),
        policy({"type": "category_cap", "category": "Space Travel", "monthly_limit": 10}),
        policy({"type": "category_cap", "category": "Income", "monthly_limit": 10}),
        policy({"type": "category_cap", "category": "Groceries", "monthly_limit": -5}),
        policy({"type": "bill_reserve", "name": "Rent", "amount": 100, "due_day": 0}),
        policy({"type": "bill_reserve", "name": "Rent", "amount": 100, "due_day": 32}),
        policy({"type": "invest", "amount": 5000}),
        {"name": "p", "rules": []},
    ],
)
def test_invalid_policies_are_rejected(bad):
    with pytest.raises(ValidationError):
        Policy.model_validate(bad)


def test_save_percentages_must_not_exceed_100():
    with pytest.raises(ValidationError):
        Policy.model_validate(policy({"type": "save_percent", "percent": 60}, {"type": "save_percent", "percent": 50}))


def test_duplicate_category_caps_rejected():
    with pytest.raises(ValidationError):
        Policy.model_validate(policy(CAP, CAP))
