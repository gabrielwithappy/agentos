#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if rg -n "packages/coding-agent|\\bBun\\b|\\bbun\\b|prompt_toolkit|Urwid" \
  "$ROOT/agentos" "$ROOT/tests" "$ROOT/scripts" "$ROOT/pyproject.toml" "$ROOT/uv.lock" \
  --glob '!verify-tui-reference-boundary.sh' >/tmp/agentos-tui-reference-boundary.out 2>/dev/null; then
  cat /tmp/agentos-tui-reference-boundary.out >&2
  exit 1
fi

echo "PASS tui-reference-not-copied"
