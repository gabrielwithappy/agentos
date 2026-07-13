#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
python3 "$ROOT/scripts/security/scan-public-boundary.py" --worktree
gitleaks detect --source "$ROOT" --no-git >/dev/null
echo 'PASS public-repo-security-boundary'
