"""One-call smoke test for Nebius Token Factory. Prints the model's reply.

Reads TOKEN_FACTORY_API_KEY, TOKEN_FACTORY_BASE_URL, TOKEN_FACTORY_MODEL from the environment
(export them or `set -a; source .env; set +a`). Requires: pip install openai
"""
import os
import sys

from openai import OpenAI


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Missing environment variable: {name} (see docs/LLM.md)")
    return value


def main() -> None:
    client = OpenAI(
        api_key=require_env("TOKEN_FACTORY_API_KEY"),
        base_url=require_env("TOKEN_FACTORY_BASE_URL"),
    )
    reply = client.chat.completions.create(
        model=require_env("TOKEN_FACTORY_MODEL"),
        messages=[{"role": "user", "content": "Reply with exactly: BachatBuddy online"}],
        max_tokens=20,
    )
    print("MODEL:", reply.model)
    print("REPLY:", reply.choices[0].message.content)


if __name__ == "__main__":
    main()
