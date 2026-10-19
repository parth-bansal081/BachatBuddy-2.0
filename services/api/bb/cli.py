"""Run enrichment from your terminal as a test user (row-level security applies).

Usage (from services/api, with a filled .env):  python -m bb.cli enrich
Needs: SUPABASE_URL, SUPABASE_ANON_KEY, BB_TEST_EMAIL, BB_TEST_PASSWORD, TOKEN_FACTORY_* variables.
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv
from supabase import create_client

from .config import env
from .enrich import enrich_user
from .llm import TokenFactoryClient
from .store import SupabaseStore


def main() -> None:
    load_dotenv()
    if sys.argv[1:] != ["enrich"]:
        sys.exit("usage: python -m bb.cli enrich")
    url, anon = env("SUPABASE_URL"), env("SUPABASE_ANON_KEY")
    email, password = env("BB_TEST_EMAIL"), env("BB_TEST_PASSWORD")
    if not (url and anon and email and password):
        sys.exit("Missing SUPABASE_URL / SUPABASE_ANON_KEY / BB_TEST_EMAIL / BB_TEST_PASSWORD in .env")
    client = create_client(url, anon)
    session = client.auth.sign_in_with_password({"email": email, "password": password})
    if session.user is None:
        sys.exit("Sign-in failed")
    llm = TokenFactoryClient()
    result = enrich_user(SupabaseStore(client, session.user.id), llm, llm.model)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
