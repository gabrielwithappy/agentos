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

export AGENTOS_HOME="$TMP/home"
export AGENTOS_TEST_SECRET="SENTINEL_SECRET"
cd "$ROOT"

.venv/bin/python -m agentos.cli setup | grep -q "PASS agentos-setup"
.venv/bin/python -m agentos.cli doctor --json | .venv/bin/python -m json.tool >/dev/null
.venv/bin/python -m agentos.cli hook list | grep -q "reject_empty"
.venv/bin/python -m agentos.cli hook disable reject_empty >/dev/null
.venv/bin/python -m agentos.cli hook enable reject_empty >/dev/null

.venv/bin/python -m agentos.cli run --once "hello" --json >"$TMP/run.jsonl"
.venv/bin/python - <<'PY' "$TMP/run.jsonl"
import json, sys
events = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
assert [event["type"] for event in events] == ["start", "message_delta", "done"]
assert all("cli" in event.get("metadata", {}) for event in events)
PY

if grep -R "SENTINEL_SECRET" "$TMP" >/dev/null; then
  echo "secret sentinel leaked" >&2
  exit 1
fi

.venv/bin/python tests/helpers/pty_cli_driver.py --self-check | grep -q "PASS pty-cli-driver-ready"

echo "PASS interactive-cli-acceptance"
