"""Run things from your terminal as a test user (row-level security applies).

From services/api, with a filled .env:
  python -m bb.cli enrich
  python -m bb.cli backtest --policy ../../fixtures/example_policy.json      (no model needed)
  python -m bb.cli compile --text "har income ka 10% bachao"                 (needs the model key)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

from .config import env
from .data import SupabaseDataStore
from .enrich import enrich_user
from .llm import TokenFactoryClient
from .policy.compiler import compile_policy
from .policy.engine import backtest
from .policy.models import Policy
from .store import SupabaseStore


def _login() -> tuple[Client, str]:
    url, anon = env("SUPABASE_URL"), env("SUPABASE_ANON_KEY")
    email, password = env("BB_TEST_EMAIL"), env("BB_TEST_PASSWORD")
    if not (url and anon and email and password):
        sys.exit("Missing SUPABASE_URL / SUPABASE_ANON_KEY / BB_TEST_EMAIL / BB_TEST_PASSWORD in .env")
    client = create_client(url, anon)
    session = client.auth.sign_in_with_password({"email": email, "password": password})
    if session.user is None:
        sys.exit("Sign-in failed")
    return client, session.user.id


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="bb.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("enrich")
    bt = sub.add_parser("backtest")
    bt.add_argument("--policy", required=True, help="path to a policy JSON file")
    cp = sub.add_parser("compile")
    cp.add_argument("--text", required=True)
    args = parser.parse_args()

    client, user_id = _login()
    if args.command == "enrich":
        llm = TokenFactoryClient()
        print(enrich_user(SupabaseStore(client, user_id), llm, llm.model).model_dump_json(indent=2))
    elif args.command == "backtest":
        policy = Policy.model_validate(json.loads(Path(args.policy).read_text(encoding="utf-8")))
        result = backtest(policy, SupabaseDataStore(client, user_id).enriched_transactions())
        print(result.headline)
        for w in result.warnings:
            print("WARNING:", w)
        for m in result.months:
            caps = ", ".join(f"{c.category} {c.spent:.0f}/{c.limit:.0f}{' OVER' if c.breached else ''}" for c in m.caps)
            print(f"{m.month}  income {m.income:>9.0f}  saved {m.saved:>8.0f}  spent {m.spend:>9.0f}  reserved {m.reserved:>7.0f}  {caps}")
    else:
        llm = TokenFactoryClient(model=env("TOKEN_FACTORY_MODEL_SMART") or env("TOKEN_FACTORY_MODEL"))
        print(compile_policy(args.text, llm).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
