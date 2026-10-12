#!/usr/bin/env bash
# Fails if any protected file differs from its recorded hash.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum"; else SHA="shasum -a 256"; fi
MANIFEST="PROTECTED.sha256"

if [ ! -f "$MANIFEST" ]; then
  echo "verify-protected: no PROTECTED.sha256 yet (before first freeze) - skipping."
  exit 0
fi

if ! $SHA -c "$MANIFEST" >/tmp/verify-protected.out 2>&1; then
  grep -v ': OK$' /tmp/verify-protected.out || true
  echo "ERROR: a PROTECTED file changed or is missing. Revert it with: git restore --source=HEAD --staged --worktree -- <path>"
  exit 1
fi

while IFS= read -r p; do
  case "$p" in ''|'#'*) continue ;; esac
  if ! grep -q "  $p\$" "$MANIFEST"; then
    echo "ERROR: $p is in PROTECTED_PATHS.txt but not in the manifest. A human must run scripts/protect-freeze.sh"
    exit 1
  fi
done < PROTECTED_PATHS.txt

echo "OK: protected files intact"
