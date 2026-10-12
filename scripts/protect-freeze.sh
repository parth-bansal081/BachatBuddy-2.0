#!/usr/bin/env bash
# HUMAN ONLY. Regenerates PROTECTED.sha256 from PROTECTED_PATHS.txt and commits it.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum"; else SHA="shasum -a 256"; fi

# Needs a real terminal: an automated agent without a TTY cannot pass this prompt.
read -r -p "HUMAN CONFIRMATION - type FREEZE to regenerate PROTECTED.sha256: " ans </dev/tty
[ "$ans" = "FREEZE" ] || { echo "aborted"; exit 1; }

: > PROTECTED.sha256.tmp
while IFS= read -r p; do
  case "$p" in ''|'#'*) continue ;; esac
  if [ ! -f "$p" ]; then echo "ERROR: protected file missing: $p"; rm -f PROTECTED.sha256.tmp; exit 1; fi
  $SHA "$p" >> PROTECTED.sha256.tmp
done < PROTECTED_PATHS.txt
mv PROTECTED.sha256.tmp PROTECTED.sha256

git add PROTECTED.sha256
PROTECT_FREEZE=1 git commit -m "chore: refreeze protected files (human)" -- PROTECTED.sha256
echo "Frozen. $(grep -c . PROTECTED.sha256) files protected."
