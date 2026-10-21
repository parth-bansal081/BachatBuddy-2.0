"""One-call smoke test for Nebius Token Factory. Prints the model's reply.

Loads the repo-root .env by itself, so it works the same in PowerShell and Git Bash.
Needs TOKEN_FACTORY_API_KEY, TOKEN_FACTORY_BASE_URL, TOKEN_FACTORY_MODEL in .env.
Run it with the services/api virtual environment active (it has openai and python-dotenv).
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Missing environment variable: {name} (fill it in .env, see docs/LLM.md)")
    return value


def main() -> None:
    load_dotenv()
    client = OpenAI(
        api_key=require_env("TOKEN_FACTORY_API_KEY"),
        base_url=require_env("TOKEN_FACTORY_BASE_URL"),
    )
    reply = client.chat.completions.create(
        model=require_env("TOKEN_FACTORY_MODEL"),
        messages=[{"role": "user", "content": "Reply with exactly: BachatBuddy online"}],
        max_tokens=1000,
    )
    content = (reply.choices[0].message.content or "").strip()
    print("MODEL:", reply.model)
    print("REPLY:", content)


if __name__ == "__main__":
    main()
