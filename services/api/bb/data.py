"""Supabase access for the money brain. Bound to the user's token, so row-level security applies."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from supabase import Client

from .policy.engine import Txn, normalize_category
from .policy.models import Policy

PAGE = 1000


class SupabaseDataStore:
    def __init__(self, client: Client, user_id: str) -> None:
        self.client = client
        self.user_id = user_id

    def enriched_transactions(self) -> list[Txn]:
        out: list[Txn] = []
        start = 0
        while True:
            res = (
                self.client.table("transactions_enriched")
                .select("date,amount,merchant,enriched_category")
                .eq("user_id", self.user_id)
                .order("date")
                .range(start, start + PAGE - 1)
                .execute()
            )
            rows = list(res.data or [])
            for row in rows:
                if row.get("date") is None or row.get("amount") is None:
                    continue
                out.append(
                    Txn(
                        day=date.fromisoformat(str(row["date"])[:10]),
                        amount=Decimal(str(row["amount"])),
                        category=normalize_category(row.get("enriched_category")),
                        merchant=str(row.get("merchant") or ""),
                    )
                )
            if len(rows) < PAGE:
                return out
            start += PAGE

    def save_policy(self, policy: Policy, source_text: str | None) -> str:
        """Makes this the user's single active policy (the previous one is kept, inactive)."""
        self.client.table("policies").update({"active": False}).eq("user_id", self.user_id).eq("active", True).execute()
        res = (
            self.client.table("policies")
            .insert(
                {
                    "user_id": self.user_id,
                    "name": policy.name,
                    "source_text": source_text,
                    "rules": [r.model_dump() for r in policy.rules],
                    "active": True,
                }
            )
            .execute()
        )
        return str((res.data or [{}])[0].get("id", ""))

    def active_policy(self) -> tuple[Policy, str | None] | None:
        res = (
            self.client.table("policies")
            .select("name,rules,source_text")
            .eq("user_id", self.user_id)
            .eq("active", True)
            .limit(1)
            .execute()
        )
        rows: list[dict[str, Any]] = list(res.data or [])
        if not rows:
            return None
        row = rows[0]
        return Policy.model_validate({"name": row["name"], "rules": row["rules"]}), row.get("source_text")
