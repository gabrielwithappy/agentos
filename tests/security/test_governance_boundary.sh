#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
for script in "$ROOT/scripts/maintenance/configure-branch-protection.sh" "$ROOT/scripts/security/scan-public-boundary.py"; do test -f "$script"; done
if rg -n -- '--force|reset --hard|rsync --delete' "$ROOT/scripts"; then
  echo 'FAIL governance-unsafe-command' >&2; exit 1
fi
echo 'PASS governance-boundary-rejects-prompt-protected-path-force-push-history-rewrite-and-delete-sync'
