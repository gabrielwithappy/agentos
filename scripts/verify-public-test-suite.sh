#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test -f "$ROOT/config/public-boundary.json"
test -d "$ROOT/.agents"
python3 "$ROOT/scripts/security/check-license.py" --license "$ROOT/LICENSE" --spdx MIT --require-canonical-text --copyright 'Copyright (c) 2026 gabrielwithappy' >/dev/null
bash "$ROOT/scripts/verify-clean-install.sh" >/dev/null
bash "$ROOT/tests/security/test_public_boundary_rejects_leaks.sh" --entrypoint ci >/dev/null
bash "$ROOT/tests/security/test_governance_boundary.sh" >/dev/null
python3 "$ROOT/scripts/maintenance/check-maintainer-docs.py" >/dev/null
echo 'PASS agentos-public-suite'
