#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() {
  case "$TMP" in
    /tmp/*) rm -rf "$TMP" ;;
  esac
}
trap cleanup EXIT

python3 -m venv "$TMP/venv"
"$TMP/venv/bin/python" -m pip install -q "$ROOT"
mkdir -p "$TMP/outside"
cd "$TMP/outside"
export AGENTOS_HOME="$TMP/home"

"$TMP/venv/bin/agentos" --help >/dev/null
"$TMP/venv/bin/agentos" setup | grep -q "PASS agentos-setup"
"$TMP/venv/bin/agentos" doctor --json | "$TMP/venv/bin/python" -m json.tool >/dev/null
if "$TMP/venv/bin/agentos" harness 2>"$TMP/harness.err"; then
  echo "expected harness without --project-root to fail" >&2
  exit 1
fi
grep -q "Missing --project-root" "$TMP/harness.err"

echo "PASS agentos-cli-isolated-install"
