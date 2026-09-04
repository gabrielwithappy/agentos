#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() {
  case "$TMP" in
    /tmp/*|/var/folders/*) rm -rf "$TMP" ;;
  esac
}
trap cleanup EXIT

uv venv --python 3.11 "$TMP/venv" >/dev/null
uv pip install --python "$TMP/venv/bin/python" "$ROOT" >/dev/null
mkdir -p "$TMP/outside"
cd "$TMP/outside"
export AGENTOS_HOME="$TMP/home"

"$TMP/venv/bin/agentos" --help >/dev/null
"$TMP/venv/bin/agentos" gateway --help > "$TMP/gateway-help.out"
for command in submit worker status events retry prune; do
  grep -q "$command" "$TMP/gateway-help.out"
done
"$TMP/venv/bin/agentos" setup > "$TMP/setup-first.out"
grep -q "PASS agentos-setup" "$TMP/setup-first.out"
grep -q "enabled=codex,claude-code" "$TMP/setup-first.out"
"$TMP/venv/bin/agentos" setup > "$TMP/setup-rerun.out"
grep -q "SKIP existing" "$TMP/setup-rerun.out"
grep -q "enabled=none" "$TMP/setup-rerun.out"
grep -q "skipped_vendors=codex,claude-code" "$TMP/setup-rerun.out"
"$TMP/venv/bin/python" - <<'PY' "$TMP/outside"
import json
import sys
from pathlib import Path

project = Path(sys.argv[1])
codex = json.loads((project / ".codex" / "hooks.json").read_text(encoding="utf-8"))
claude = json.loads((project / ".claude" / "settings.json").read_text(encoding="utf-8"))
text = json.dumps({"codex": codex, "claude": claude})
assert ".agents/hooks" not in text
for command in (
    "agentos hook bridge codex pre-bash",
    "agentos hook bridge codex pre-write",
    "agentos hook bridge claude-code pre-bash",
    "agentos hook bridge claude-code pre-write",
):
    assert command in text, command
PY
printf '%s' '{"tool_input":{"command":"echo safe"}}' | "$TMP/venv/bin/agentos" hook bridge codex pre-bash

if "$TMP/venv/bin/agentos" hook bridge codex unlisted </dev/null; then
  echo "expected unlisted bridge mapping to fail" >&2
  exit 1
fi
mkdir -p "$TMP/existing/.codex"
printf '%s\n' '{"user":"config"}' > "$TMP/existing/.codex/hooks.json"
AGENTOS_HOME="$TMP/existing-home" "$TMP/venv/bin/agentos" setup --path "$TMP/existing" > "$TMP/setup-existing.out"
grep -q "enabled=claude-code" "$TMP/setup-existing.out"
grep -q "skipped_vendors=codex" "$TMP/setup-existing.out"
test "$(cat "$TMP/existing/.codex/hooks.json")" = '{"user":"config"}'
mkdir -p "$TMP/isolated-skill"
printf '%s\n' '---' 'name: isolated-skill' 'description: isolated install skill' '---' > "$TMP/isolated-skill/SKILL.md"
"$TMP/venv/bin/agentos" skill install "$TMP/isolated-skill" | grep -q "Successfully installed skill"
"$TMP/venv/bin/agentos" skill status --json | "$TMP/venv/bin/python" -m json.tool >/dev/null
"$TMP/venv/bin/agentos" project init --path "$TMP/outside" --json | "$TMP/venv/bin/python" -m json.tool >/dev/null
test -f "$TMP/outside/.agentos/project/00-project-index.md"
test -f "$TMP/outside/.agentos/project/06-decisions-progress-change-log.md"

# Task 2 test for isolated install behavior
"$TMP/venv/bin/agentos" project init --path "$TMP/outside" --skills "isolated-skill" --json > "$TMP/init-opt.json"
test -f "$TMP/outside/.agents/skills/isolated-skill/SKILL.md"

# Unmanaged preservation
mkdir -p "$TMP/outside/.agents/skills/unmanaged-skill"
echo "unmanaged" > "$TMP/outside/.agents/skills/unmanaged-skill/SKILL.md"

# Reselecting skips isolated-skill
"$TMP/venv/bin/agentos" project skills select --path "$TMP/outside" --skills "none" --json > "$TMP/select-none.json"
if [ -f "$TMP/outside/.agents/skills/isolated-skill/SKILL.md" ]; then
    echo "isolated-skill should be removed" >&2
    exit 1
fi
test -f "$TMP/outside/.agents/skills/unmanaged-skill/SKILL.md"

"$TMP/venv/bin/agentos" project status --path "$TMP/outside" --json > "$TMP/project-status.json"
"$TMP/venv/bin/python" - <<'PY' "$TMP/project-status.json"
import json
import sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["state"] == "current"
assert payload["project_documents"]["state"] == "current"
assert payload["project_documents"]["missing"] == []
PY
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
