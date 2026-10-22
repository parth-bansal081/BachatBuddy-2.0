from datetime import date
from decimal import Decimal

from bb.policy.engine import Txn, backtest, normalize_category, safe_to_spend
from bb.policy.models import Policy


def T(day, amount, category, merchant=""):
    return Txn(day=day, amount=Decimal(str(amount)), category=category, merchant=merchant)


def P(*rules, name="test"):
    return Policy.model_validate({"name": name, "rules": list(rules)})


SAVE10 = {"type": "save_percent", "percent": 10}
FOOD3K = {"type": "category_cap", "category": "Food & Dining", "monthly_limit": 3000}
RENT = {"type": "bill_reserve", "name": "Rent", "amount": 6000, "due_day": 1}


def test_save_percent_applies_to_income_credits_only():
    txns = [T(date(2026, 1, 5), 50000, "Income"), T(date(2026, 1, 6), 2000, "Transfers"), T(date(2026, 1, 7), -500, "Groceries")]
    r = backtest(P(SAVE10), txns)
    assert r.total_saved == 5000.0 and r.total_income == 50000.0
    assert [e.kind for e in r.events] == ["saved"]


def test_two_income_credits_each_get_a_cut_and_round_to_paise():
    r = backtest(P({"type": "save_percent", "percent": 12.5}), [T(date(2026, 1, 1), 333.33, "Income"), T(date(2026, 1, 9), 100, "Income")])
    assert r.total_saved == 54.17  # 41.67 + 12.50 (each rounded half-up)


def test_cap_warning_then_breach_once_per_month():
    txns = [
        T(date(2026, 1, 3), -2000, "Food & Dining"),   # 2000 = 66%: nothing
        T(date(2026, 1, 8), -500, "Food & Dining"),    # 2500 = 83%: warning
        T(date(2026, 1, 15), -800, "Food & Dining"),   # 3300: breach (over by 300)
        T(date(2026, 1, 20), -400, "Food & Dining"),   # 3700: no second breach event
    ]
    r = backtest(P(FOOD3K), txns)
    kinds = [e.kind for e in r.events]
    assert kinds == ["cap_warning", "cap_breached"]
    assert r.cap_breaches == 1
    assert r.over_cap_total == 700.0  # month total 3700 - 3000
    assert r.months[0].caps[0].breached is True and r.months[0].caps[0].over_by == 700.0


def test_cap_resets_each_calendar_month():
    txns = [T(date(2026, 1, 28), -3500, "Food & Dining"), T(date(2026, 2, 2), -3500, "Food & Dining")]
    r = backtest(P(FOOD3K), txns)
    assert r.cap_breaches == 2 and r.over_cap_total == 1000.0


def test_exactly_at_limit_is_not_a_breach():
    r = backtest(P(FOOD3K), [T(date(2026, 1, 3), -3000, "Food & Dining")])
    assert r.cap_breaches == 0 and r.months[0].caps[0].breached is False


def test_other_categories_do_not_count_toward_a_cap():
    r = backtest(P(FOOD3K), [T(date(2026, 1, 3), -9000, "Shopping")])
    assert r.cap_breaches == 0


def test_bill_reserved_every_month_in_range_and_clamped_to_month_end():
    bill31 = {"type": "bill_reserve", "name": "Loan", "amount": 1000, "due_day": 31}
    txns = [T(date(2026, 1, 10), -10, "Groceries"), T(date(2026, 3, 10), -10, "Groceries")]
    r = backtest(P(bill31), txns)
    days = [e.day for e in r.events if e.kind == "bill_reserved"]
    assert days == ["2026-01-31", "2026-02-28", "2026-03-31"]  # February has no 31st; empty February still counted
    assert r.total_reserved == 3000.0


def test_left_after_policy_and_headline():
    txns = [T(date(2026, 1, 5), 50000, "Income"), T(date(2026, 1, 9), -4000, "Food & Dining")]
    r = backtest(P(SAVE10, FOOD3K, RENT), txns)
    m = r.months[0]
    assert m.left_after_policy == 50000 - 5000 - 4000 - 6000
    assert "set aside ₹5,000" in r.headline and "1 overspend " in r.headline.replace("overspends", "overspend ")


def test_no_transactions_gives_clear_warning():
    r = backtest(P(SAVE10), [])
    assert r.months == [] and r.warnings and "No transactions" in r.headline


def test_warns_when_no_income_found_for_a_save_rule():
    r = backtest(P(SAVE10), [T(date(2026, 1, 3), -100, "Groceries")])
    assert any("No income" in w for w in r.warnings)


def test_warns_when_most_spending_is_uncategorised():
    txns = [T(date(2026, 1, i + 1), -10, "Miscellaneous") for i in range(5)] + [T(date(2026, 1, 20), -10, "Groceries")]
    assert any("uncategorised" in w for w in backtest(P(FOOD3K), txns).warnings)


def test_unsorted_input_is_handled():
    txns = [T(date(2026, 1, 20), -2000, "Food & Dining"), T(date(2026, 1, 3), -1500, "Food & Dining")]
    r = backtest(P(FOOD3K), txns)
    assert r.cap_breaches == 1 and r.events[0].day == "2026-01-20"


def test_normalize_category_maps_legacy_and_unknown():
    assert normalize_category("Food") == "Food & Dining"
    assert normalize_category("Bills") == "Utilities"
    assert normalize_category("Groceries") == "Groceries"
    assert normalize_category("???") == "Miscellaneous"
    assert normalize_category(None) == "Miscellaneous"


def test_safe_to_spend_basic():
    txns = [T(date(2026, 1, 1), 50000, "Income"), T(date(2026, 1, 4), -8000, "Groceries")]
    s = safe_to_spend(P(SAVE10, RENT), txns, date(2026, 1, 10))
    # income 50000 - save 5000 - spent 8000 - upcoming bills (rent due day 1 already passed) 0
    assert s.amount == 37000.0 and s.reserved_upcoming == 0.0


def test_safe_to_spend_reserves_bills_still_due():
    txns = [T(date(2026, 1, 1), 50000, "Income")]
    bill = {"type": "bill_reserve", "name": "Phone", "amount": 1200, "due_day": 15}
    s = safe_to_spend(P(bill), txns, date(2026, 1, 10))
    assert s.reserved_upcoming == 1200.0 and s.amount == 48800.0


def test_safe_to_spend_uses_expected_income_when_none_yet():
    s = safe_to_spend(P(SAVE10), [], date(2026, 1, 3), expected_income=30000)
    assert s.income_used == 30000.0 and s.saved == 3000.0 and s.amount == 27000.0
    assert any("expected monthly income" in n for n in s.notes)


def test_safe_to_spend_ignores_other_months_and_future_days():
    txns = [T(date(2025, 12, 31), -9999, "Groceries"), T(date(2026, 1, 20), -500, "Groceries"), T(date(2026, 1, 2), 1000, "Income")]
    s = safe_to_spend(P(SAVE10), txns, date(2026, 1, 10))
    assert s.spent == 0.0 and s.income_used == 1000.0
