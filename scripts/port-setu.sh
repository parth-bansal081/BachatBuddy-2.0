#!/usr/bin/env bash
# HUMAN ONLY. Copies the working Setu frontend files from the OLD repo, byte for byte. No edits at all.
# The backend (Supabase functions, secrets, Setu dashboard) is NOT touched: it stays live in the old Supabase project.
# Usage: bash scripts/port-setu.sh /path/to/old/BachatBuddy
set -euo pipefail
OLD="${1:?usage: bash scripts/port-setu.sh /path/to/old/BachatBuddy}"
cd "$(git rev-parse --show-toplevel)"

FILES=(
  src/lib/setuService.ts
  src/components/BankSyncButton.tsx
  src/components/ui/button.tsx
  src/components/ui/dialog.tsx
  src/lib/utils.ts
)

for f in "${FILES[@]}"; do
  [ -f "$OLD/$f" ] || { echo "ERROR: missing in old repo: $f"; exit 1; }
  mkdir -p "$(dirname "$f")"
  cp "$OLD/$f" "$f"
  cmp -s "$OLD/$f" "$f" || { echo "ERROR: copy differs: $f"; exit 1; }
  echo "copied (identical): $f"
done
echo "All files are byte-identical to the old repo."
