#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP_HOME=$(mktemp -d /tmp/agentos-clean-home.XXXXXX)
cleanup() {
  case "$TMP_HOME" in
    /tmp/agentos-clean-home.*) rm -rf "$TMP_HOME" ;;
  esac
}
trap cleanup EXIT
export PYTHONPATH="$ROOT"
if test -x "$ROOT/.venv/bin/python"; then
  PY="$ROOT/.venv/bin/python"
else
  PY=python3
fi
HOME="$TMP_HOME" AGENTOS_HOME="$TMP_HOME/.agentos" "$PY" "$ROOT/agentos/cli.py" setup >/dev/null
test -f "$TMP_HOME/.agentos/state-manifest.json"
test -d "$TMP_HOME/.agentos/sessions"
test -d "$TMP_HOME/.agentos/context"
test -f "$TMP_HOME/.agentos/core/.agents/skills/.agentos-skills.json"
test -f "$TMP_HOME/.agentos/core/.agents/skills/agentos-core-guidance/SKILL.md"
skill_count=$(find "$TMP_HOME/.agentos/core/.agents/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -type f | wc -l | tr -d ' ')
test "$skill_count" = 21
echo 'PASS agentos-clean-install'
