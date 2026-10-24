"""Actions backend: deterministic proposed actions for a user's policy."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from supabase import Client

from .config import CATEGORIES
from .policy.engine import Txn, CENT, WARN_AT, d, q, clamp_day, _Month
from .policy.models import Policy, SavePercentRule, BillReserveRule


def _latest_month_key(txns: list[Txn]) -> str | None:
    """Return the YYYY-MM of the latest transaction's month, or None if no transactions."""
    if not txns:
        return None
    latest = max(txns, key=lambda t: t.day)
    return f"{latest.day.year}-{latest.day.month:02d}"


def _filter_month(txns: list[Txn], month_key: str) -> list[Txn]:
    """Filter transactions to only those in the given month_key (YYYY-MM)."""
    year, month = map(int, month_key.split("-"))
    return [t for t in txns if t.day.year == year and t.day.month == month]


def compute_save_amounts(policy: Policy, txns: list[Txn], month_key: str) -> list[tuple[str, Decimal]]:
    """Compute save_percent amounts per rule for a given month.

    Returns list of (label, amount) where amount is in rupees as Decimal.
    """
    saves = [r for r in policy.rules if isinstance(r, SavePercentRule)]
    if not saves:
        return []

    in_month = _filter_month(txns, month_key)
    income = sum((t.amount for t in in_month if t.amount > 0 and t.category == "Income"), Decimal("0"))

    results: list[tuple[str, Decimal]] = []
    for rule in saves:
        amount = q(income * d(rule.percent) / 100)
        if amount > 0:
            results.append((rule.label, amount))
    return results


def compute_bill_amounts(policy: Policy, month_key: str) -> list[tuple[str, Decimal]]:
    """Compute bill_reserve amounts per rule for a given month.

    Returns list of (name, amount) where amount is in rupees as Decimal.
    """
    bills = [r for r in policy.rules if isinstance(r, BillReserveRule)]
    if not bills:
        return []

    year, month = map(int, month_key.split("-"))
    day = date(year, month, clamp_day(year, month, 1))  # just need a valid date in that month

    results: list[tuple[str, Decimal]] = []
    for rule in bills:
        due_day = clamp_day(year, month, rule.due_day)
        bill_date = date(year, month, due_day)
        # Only create action if the bill date is in this month (always true here)
        results.append((rule.name, d(rule.amount)))
    return results


async def generate_actions(client: Client, user_id: str) -> list[dict[str, Any]]:
    """Generate pending set_aside actions for the user's active policy and latest month.

    Returns the list of actions for that month (newly created or existing).
    """
    # Fetch active policy
    policy_res = await client.table("policies") \
        .select("name,rules") \
        .eq("user_id", user_id) \
        .eq("active", True) \
        .limit(1) \
        .execute()

    rows = list(policy_res.data or [])
    if not rows:
        return []

    policy = Policy.model_validate({"name": rows[0]["name"], "rules": rows[0]["rules"]})

    # Fetch enriched transactions
    data_res = await client.table("transactions_enriched") \
        .select("date,amount,merchant,enriched_category") \
        .eq("user_id", user_id) \
        .order("date") \
        .execute()

    data_rows = list(data_res.data or [])
    txns: list[Txn] = []
    for row in data_rows:
        if row.get("date") is None or row.get("amount") is None:
            continue
        from .policy.engine import normalize_category
        txns.append(Txn(
            day=date.fromisoformat(str(row["date"])[:10]),
            amount=Decimal(str(row["amount"])),
            category=normalize_category(row.get("enriched_category")),
            merchant=str(row.get("merchant") or ""),
        ))

    month_key = _latest_month_key(txns)
    if not month_key:
        return []

    # Compute amounts
    save_results = compute_save_amounts(policy, txns, month_key)
    bill_results = compute_bill_amounts(policy, month_key)

    # Upsert actions (idempotent via unique constraint)
    actions_to_upsert: list[dict[str, Any]] = []
    for label, amount in save_results:
        actions_to_upsert.append({
            "user_id": user_id,
            "kind": "set_aside",
            "label": label,
            "amount": str(q(amount)),
            "month": month_key,
            "status": "pending",
        })
    for label, amount in bill_results:
        actions_to_upsert.append({
            "user_id": user_id,
            "kind": "set_aside",
            "label": label,
            "amount": str(q(amount)),
            "month": month_key,
            "status": "pending",
        })

    if not actions_to_upsert:
        return []

    await client.table("actions").upsert(
        actions_to_upsert,
        on_conflict="user_id,kind,label,month"
    ).execute()

    # Return the actions for this month
    res = await client.table("actions") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("month", month_key) \
        .order("created_at") \
        .execute()

    return list(res.data or [])


async def get_pending_actions(client: Client, user_id: str) -> list[dict[str, Any]]:
    """Get the user's pending actions, newest first."""
    res = await client.table("actions") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("status", "pending") \
        .order("created_at", desc=True) \
        .execute()

    return list(res.data or [])


async def decide_action(client: Client, user_id: str, action_id: str, decision: str) -> dict[str, Any] | None:
    """Set the action's status and decided_at. Returns the action or None if not found/owned."""
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be 'approved' or 'rejected'")

    # First check ownership
    res = await client.table("actions") \
        .select("*") \
        .eq("id", action_id) \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    rows = list(res.data or [])
    if not rows:
        return None

    action = rows[0]
    if action["status"] != "pending":
        raise ValueError("already_decided")

    await client.table("actions") \
        .update({"status": decision, "decided_at": "now()"}) \
        .eq("id", action_id) \
        .execute()

    # Return updated action
    res = await client.table("actions") \
        .select("*") \
        .eq("id", action_id) \
        .limit(1) \
        .execute()

    rows = list(res.data or [])
    return rows[0] if rows else None