#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP_HOME=$(mktemp -d /tmp/agentos-clean-home.XXXXXX)
export PYTHONPATH="$ROOT"
HOME="$TMP_HOME" AGENTOS_HOME="$TMP_HOME/.agentos" python3 "$ROOT/agentos/cli.py" setup >/dev/null
test -f "$TMP_HOME/.agentos/manifest.json"
test -d "$TMP_HOME/.agentos/core/.agents"
echo 'PASS agentos-clean-install'
