#!/usr/bin/env bash
# Runs before every commit (installed by scripts/install-hooks.sh).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

bash scripts/verify-protected.sh || exit 1

staged="$(git diff --cached --name-only)"

if echo "$staged" | grep -qx "PROTECTED.sha256" && [ "${PROTECT_FREEZE:-}" != "1" ]; then
  echo "ERROR: PROTECTED.sha256 may only be changed by scripts/protect-freeze.sh (human)."
  exit 1
fi

if echo "$staged" | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' >/dev/null; then
  echo "ERROR: an .env file is staged. Unstage it: git restore --staged <file>"
  exit 1
fi

if git diff --cached -U0 | grep -E '^\+' | grep -E 'eyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}|(SECRET|SERVICE_ROLE_KEY|API_KEY)[A-Z_]*[[:space:]]*=[[:space:]]*[A-Za-z0-9._-]{16,}' >/dev/null; then
  echo "ERROR: something that looks like a secret/key is in the staged changes. Remove it."
  exit 1
fi

exit 0
