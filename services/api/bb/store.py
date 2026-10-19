"""Supabase access. The client is bound to the USER's token, so row-level security applies: no service-role key anywhere."""
from __future__ import annotations

from typing import Any

from supabase import Client

from .schemas import CacheRow

PAGE = 1000
CHUNK = 500


class SupabaseStore:
    def __init__(self, client: Client, user_id: str) -> None:
        self.client = client
        self.user_id = user_id

    def _select_all(self, table: str, columns: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        start = 0
        while True:
            res = (
                self.client.table(table)
                .select(columns)
                .eq("user_id", self.user_id)
                .range(start, start + PAGE - 1)
                .execute()
            )
            rows = list(res.data or [])
            out.extend(rows)
            if len(rows) < PAGE:
                return out
            start += PAGE

    def distinct_narrations(self) -> list[str]:
        rows = self._select_all("transactions", "merchant")
        return sorted({str(r["merchant"]) for r in rows if r.get("merchant")})

    def mapped(self) -> dict[str, str]:
        rows = self._select_all("narration_map", "raw_narration,key")
        return {str(r["raw_narration"]): str(r["key"]) for r in rows}

    def cached_keys(self) -> set[str]:
        rows = self._select_all("merchant_cache", "key,source")
        return {str(r["key"]) for r in rows if r.get("source") != "fallback"}

    def upsert_cache(self, rows: list[CacheRow]) -> None:
        payload = [{"user_id": self.user_id, **row.model_dump()} for row in rows]
        for start in range(0, len(payload), CHUNK):
            self.client.table("merchant_cache").upsert(
                payload[start : start + CHUNK], on_conflict="user_id,key"
            ).execute()

    def upsert_map(self, pairs: list[tuple[str, str]]) -> None:
        payload = [{"user_id": self.user_id, "raw_narration": n, "key": k} for n, k in pairs]
        for start in range(0, len(payload), CHUNK):
            self.client.table("narration_map").upsert(
                payload[start : start + CHUNK], on_conflict="user_id,raw_narration"
            ).execute()
