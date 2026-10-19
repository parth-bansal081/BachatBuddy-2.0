"""Regex shield: turns a raw bank narration into a short, stable merchant KEY.

The same merchant must give the same key even when reference numbers differ,
so the LLM is called once per merchant instead of once per transaction.
The key is for matching only. The pretty name comes from the LLM.
"""
from __future__ import annotations

import re

from .config import MAX_TEXT_LEN

_STOP_TOKENS = {
    "UPI", "DR", "CR", "IMPS", "NEFT", "RTGS", "POS", "ATM", "ECOM", "REF", "TXN", "TRF",
    "TO", "FROM", "PAYMENT", "PAY", "PAID", "VIA", "UPIPAYMENT", "PAYMENTFROMPHONE",
    "PURCHASE", "DEBIT", "CREDIT", "TRANSFER", "MOB", "MOBILE", "BANKING", "NET", "MB",
}
_IFSC = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
_MASKED = re.compile(r"^[0-9X*]{8,}$")
_SPLIT = re.compile(r"[\s/\\|,:;_()\-]+")


def _slash_upi_name(raw: str) -> str | None:
    """UPI/DR/<ref>/<NAME>/<BANK>/<handle>/<note>  ->  <NAME>"""
    parts = [p.strip() for p in raw.split("/")]
    if len(parts) >= 4 and parts[0].upper() == "UPI" and parts[3]:
        return parts[3]
    return None


def _dash_upi_name(raw: str) -> str | None:
    """UPI-<NAME>-<handle>-<IFSC>-<ref>-<note>  ->  <NAME>"""
    if raw.upper().startswith("UPI-"):
        parts = raw.split("-")
        if len(parts) >= 2 and parts[1].strip():
            return parts[1].strip()
    return None


def _filter_tokens(text: str) -> list[str]:
    kept: list[str] = []
    for token in _SPLIT.split(text):
        if not token or "@" in token:
            continue
        upper = token.upper()
        if upper in _STOP_TOKENS or _IFSC.match(upper) or _MASKED.match(upper):
            continue
        clean = re.sub(r"[^A-Za-z0-9&]", "", token)
        if not clean:
            continue
        if clean.isdigit() and len(clean) >= 4:
            continue
        if sum(ch.isdigit() for ch in clean) >= 6:
            continue
        kept.append(clean)
    return kept


def merchant_key(raw: str) -> str:
    """Stable lowercase key for a narration. Empty string if nothing useful is left."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    candidate = _slash_upi_name(raw) or _dash_upi_name(raw) or raw
    tokens = _filter_tokens(candidate)
    if not tokens and candidate != raw:
        tokens = _filter_tokens(raw)
    key = " ".join(token.lower() for token in tokens)
    return key[:MAX_TEXT_LEN].strip()
