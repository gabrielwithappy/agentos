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
"$TMP/venv/bin/agentos" doctor --json >"$TMP/doctor.json"
"$TMP/venv/bin/python" - <<'PY' "$TMP/doctor.json"
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert "launcher" in payload
assert "runtime" in payload
assert "recovery" in payload
assert "next_action" in payload
PY
"$TMP/venv/bin/python" -m agentos.runtime.bench --prompt "Reply with OK only." --provider mock --format json >"$TMP/runtime-bench.json"
"$TMP/venv/bin/python" -m json.tool "$TMP/runtime-bench.json" >/dev/null
if "$TMP/venv/bin/agentos" harness 2>"$TMP/harness.err"; then
  echo "expected harness without --project-root to fail" >&2
  exit 1
fi
grep -q "Missing --project-root" "$TMP/harness.err"

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" "$ROOT/tests/helpers/pty_cli_driver.py" --installed-textual-app "$TMP/venv/bin/python" | grep -q "PASS installed-textual-app"
PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" "$ROOT/tests/helpers/pty_cli_driver.py" --installed-tui-smoke "$TMP/venv/bin/agentos" --cwd "$TMP/outside" | grep -q "PASS installed-tui-pseudo-tty"

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" "$ROOT/tests/helpers/pty_cli_driver.py" --stdout-redirect "$TMP/venv/bin/agentos" >"$TMP/stdout-redirect.out" 2>"$TMP/stdout-redirect.err" || code_redirect=$?
code_redirect="${code_redirect:-0}"
test "$code_redirect" -eq 2
test ! -s "$TMP/stdout-redirect.out"
grep -q 'Interactive mode requires a TTY. Next: agentos run --once "<prompt>".' "$TMP/stdout-redirect.err"

set +e
printf '' | "$TMP/venv/bin/agentos" >"$TMP/notty.out" 2>"$TMP/notty.err"
code_notty=$?
set -e
test "$code_notty" -eq 2
test ! -s "$TMP/notty.out"
grep -q 'Interactive mode requires a TTY. Next: agentos run --once "<prompt>".' "$TMP/notty.err"

echo "PASS installed-tui-smoke"

echo "PASS agentos-cli-isolated-install"
