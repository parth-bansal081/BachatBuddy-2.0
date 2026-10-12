#!/usr/bin/env bash
# One-time, human: installs the pre-commit hook.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
printf '#!/usr/bin/env bash\nexec bash scripts/pre-commit.sh\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit scripts/*.sh
echo "pre-commit hook installed."
