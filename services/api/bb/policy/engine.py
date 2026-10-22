"""Deterministic money math. No model, no network. All amounts are Decimal rupees.

Sign convention (from the Setu sync): credits are positive, debits are negative.
"""
from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel

from ..config import CATEGORIES
from .models import BillReserveRule, CategoryCapRule, Policy, SavePercentRule

CENT = Decimal("0.01")
WARN_AT = Decimal("0.8")

# Categories the old sync wrote before enrichment existed.
LEGACY_CATEGORY_MAP = {
    "Food": "Food & Dining",
    "Lifestyle": "Shopping",
    "Bills": "Utilities",
    "Transport": "Transport",
    "Shopping": "Shopping",
    "Income": "Income",
}


def normalize_category(raw: str | None) -> str:
    if raw in CATEGORIES:
        return str(raw)
    return LEGACY_CATEGORY_MAP.get(raw or "", "Miscellaneous")


def q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def d(value: float | int | str | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def clamp_day(year: int, month: int, day: int) -> int:
    return min(day, calendar.monthrange(year, month)[1])


@dataclass(frozen=True)
class Txn:
    day: date
    amount: Decimal  # credit > 0, debit < 0
    category: str
    merchant: str = ""


@dataclass
class _Month:
    month: str
    income: Decimal = Decimal("0")
    saved: Decimal = Decimal("0")
    spend: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")
    cat_spend: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    breached: set[str] = field(default_factory=set)
    warned: set[str] = field(default_factory=set)


# ---------- result models (what the API returns) ----------

class EventOut(BaseModel):
    day: str
    kind: str  # saved | cap_warning | cap_breached | bill_reserved
    rule: str
    amount: float
    detail: str


class CapOut(BaseModel):
    category: str
    limit: float
    spent: float
    breached: bool
    over_by: float


class MonthOut(BaseModel):
    month: str
    income: float
    saved: float
    spend: float
    reserved: float
    left_after_policy: float
    caps: list[CapOut]


class BacktestResult(BaseModel):
    policy_name: str
    first_day: str | None
    last_day: str | None
    months: list[MonthOut]
    events: list[EventOut]
    total_income: float
    total_spend: float
    total_saved: float
    total_reserved: float
    cap_breaches: int
    over_cap_total: float
    headline: str
    warnings: list[str]


class SafeToSpend(BaseModel):
    as_of: str
    amount: float
    income_used: float
    saved: float
    spent: float
    reserved_upcoming: float
    notes: list[str]


def _f(value: Decimal) -> float:
    return float(q(value))


def _money(value: Decimal) -> str:
    return f"₹{int(q(value)):,}"


def backtest(policy: Policy, txns: list[Txn]) -> BacktestResult:
    saves = [r for r in policy.rules if isinstance(r, SavePercentRule)]
    caps = [r for r in policy.rules if isinstance(r, CategoryCapRule)]
    bills = [r for r in policy.rules if isinstance(r, BillReserveRule)]
    ordered = sorted(txns, key=lambda t: t.day)
    warnings: list[str] = []
    if not ordered:
        return BacktestResult(
            policy_name=policy.name, first_day=None, last_day=None, months=[], events=[],
            total_income=0, total_spend=0, total_saved=0, total_reserved=0, cap_breaches=0,
            over_cap_total=0, headline="No transactions to test this policy on yet.",
            warnings=["No transactions found. Link a bank account first."],
        )

    months: dict[str, _Month] = {}
    events: list[tuple[date, EventOut]] = []

    def month_for(day: date) -> _Month:
        key = f"{day.year}-{day.month:02d}"
        return months.setdefault(key, _Month(month=key))

    for t in ordered:
        m = month_for(t.day)
        if t.amount > 0:
            if t.category != "Income":
                continue
            m.income += t.amount
            for rule in saves:
                amount = q(t.amount * d(rule.percent) / 100)
                m.saved += amount
                events.append((t.day, EventOut(
                    day=t.day.isoformat(), kind="saved", rule=rule.label, amount=_f(amount),
                    detail=f"{rule.percent:g}% of {_money(t.amount)} income",
                )))
        elif t.amount < 0:
            spend = -t.amount
            m.spend += spend
            m.cat_spend[t.category] += spend
            for rule in caps:
                if rule.category != t.category:
                    continue
                limit = d(rule.monthly_limit)
                spent = m.cat_spend[t.category]
                if spent > limit and rule.category not in m.breached:
                    m.breached.add(rule.category)
                    events.append((t.day, EventOut(
                        day=t.day.isoformat(), kind="cap_breached", rule=rule.category, amount=_f(spent - limit),
                        detail=f"{rule.category} passed {_money(limit)} this month",
                    )))
                elif spent >= limit * WARN_AT and rule.category not in m.warned and rule.category not in m.breached:
                    m.warned.add(rule.category)
                    events.append((t.day, EventOut(
                        day=t.day.isoformat(), kind="cap_warning", rule=rule.category, amount=_f(spent),
                        detail=f"{rule.category} reached 80% of {_money(limit)}",
                    )))

    # bills: one reservation per bill for every calendar month in range
    first, last = ordered[0].day, ordered[-1].day
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        key = f"{year}-{month:02d}"
        m = months.setdefault(key, _Month(month=key))
        for rule in bills:
            day = date(year, month, clamp_day(year, month, rule.due_day))
            m.reserved += d(rule.amount)
            events.append((day, EventOut(
                day=day.isoformat(), kind="bill_reserved", rule=rule.name, amount=_f(d(rule.amount)),
                detail=f"{rule.name} due on day {rule.due_day}",
            )))
        month += 1
        if month == 13:
            year, month = year + 1, 1

    month_out: list[MonthOut] = []
    over_total = Decimal("0")
    for key in sorted(months):
        m = months[key]
        cap_rows: list[CapOut] = []
        for rule in caps:
            spent = m.cat_spend.get(rule.category, Decimal("0"))
            over = max(Decimal("0"), spent - d(rule.monthly_limit))
            over_total += over
            cap_rows.append(CapOut(
                category=rule.category, limit=rule.monthly_limit, spent=_f(spent),
                breached=over > 0, over_by=_f(over),
            ))
        month_out.append(MonthOut(
            month=key, income=_f(m.income), saved=_f(m.saved), spend=_f(m.spend), reserved=_f(m.reserved),
            left_after_policy=_f(m.income - m.saved - m.spend - m.reserved), caps=cap_rows,
        ))

    total_income = sum((m.income for m in months.values()), Decimal("0"))
    total_spend = sum((m.spend for m in months.values()), Decimal("0"))
    total_saved = sum((m.saved for m in months.values()), Decimal("0"))
    total_reserved = sum((m.reserved for m in months.values()), Decimal("0"))
    breaches = sum(1 for _, e in events if e.kind == "cap_breached")

    if saves and total_income == 0:
        warnings.append("No income transactions were found, so nothing could be set aside. Run enrichment so salary credits are recognised.")
    misc = sum(1 for t in ordered if t.amount < 0 and t.category == "Miscellaneous")
    debits = sum(1 for t in ordered if t.amount < 0)
    if debits and misc / debits > 0.3:
        warnings.append("More than 30% of spending is uncategorised, so caps may under-count. Run enrichment.")

    n = len(months)
    headline = (
        f"Over {n} month{'s' if n != 1 else ''}, this policy would have set aside {_money(total_saved)}, "
        f"reserved {_money(total_reserved)} for bills and flagged {breaches} overspend{'s' if breaches != 1 else ''} "
        f"totalling {_money(over_total)}."
    )
    events.sort(key=lambda pair: pair[0])
    return BacktestResult(
        policy_name=policy.name, first_day=first.isoformat(), last_day=last.isoformat(), months=month_out,
        events=[e for _, e in events], total_income=_f(total_income), total_spend=_f(total_spend),
        total_saved=_f(total_saved), total_reserved=_f(total_reserved), cap_breaches=breaches,
        over_cap_total=_f(over_total), headline=headline, warnings=warnings,
    )


def safe_to_spend(
    policy: Policy, txns: list[Txn], as_of: date, expected_income: float | None = None
) -> SafeToSpend:
    """What is left to spend this month after savings, spending so far and bills still due."""
    saves = [r for r in policy.rules if isinstance(r, SavePercentRule)]
    bills = [r for r in policy.rules if isinstance(r, BillReserveRule)]
    notes: list[str] = []
    in_month = [t for t in txns if (t.day.year, t.day.month) == (as_of.year, as_of.month) and t.day <= as_of]
    income = sum((t.amount for t in in_month if t.amount > 0 and t.category == "Income"), Decimal("0"))
    spent = sum((-t.amount for t in in_month if t.amount < 0), Decimal("0"))
    if income == 0 and expected_income:
        income = d(expected_income)
        notes.append("No income received yet this month, so your expected monthly income was used.")
    saved = sum((q(income * d(r.percent) / 100) for r in saves), Decimal("0"))
    upcoming = sum(
        (d(r.amount) for r in bills if clamp_day(as_of.year, as_of.month, r.due_day) > as_of.day), Decimal("0")
    )
    amount = income - saved - spent - upcoming
    if amount < 0:
        notes.append("You are already past your safe amount for this month.")
    return SafeToSpend(
        as_of=as_of.isoformat(), amount=_f(amount), income_used=_f(income), saved=_f(saved),
        spent=_f(spent), reserved_upcoming=_f(upcoming), notes=notes,
    )
