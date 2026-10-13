"""FastAPI dependencies: who is calling, and which store/LLM to use."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException
from supabase import Client, create_client

from .config import env
from .llm import LlmClient, LlmUnavailable, TokenFactoryClient
from .store import SupabaseStore


@dataclass
class Caller:
    user_id: str
    store: SupabaseStore


def get_caller(authorization: str | None = Header(default=None)) -> Caller:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    url, anon = env("SUPABASE_URL"), env("SUPABASE_ANON_KEY")
    if not url or not anon:
        raise HTTPException(status_code=500, detail="Server is missing SUPABASE_URL / SUPABASE_ANON_KEY")
    client: Client = create_client(url, anon)
    try:
        user = client.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if user is None or user.user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    client.postgrest.auth(token)  # all queries now run as this user (RLS applies)
    return Caller(user_id=user.user.id, store=SupabaseStore(client, user.user.id))


def get_llm() -> LlmClient:
    try:
        return TokenFactoryClient()
    except LlmUnavailable as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
