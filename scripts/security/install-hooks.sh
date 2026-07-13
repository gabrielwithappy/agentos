#!/usr/bin/env bash
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
install -m 0755 "$ROOT/scripts/security/pre-commit" "$ROOT/.git/hooks/pre-commit"
echo 'PASS public-hooks-installed'
