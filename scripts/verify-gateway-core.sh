#!/usr/bin/env bash
set -euo pipefail

uv run --offline pytest tests/test_gateway_store.py tests/test_gateway_service.py tests/test_gateway_worker.py -q

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export AGENTOS_HOME="$tmp/home"
project="$tmp/project"
mkdir -p "$project/.git"

run_json="$(uv run --offline agentos gateway submit --provider mock --cwd "$project" --record-policy full "verify gateway" --json)"
run_id="$(uv run --offline python -c 'import json,sys; print(json.loads(sys.argv[1])["run_id"])' "$run_json")"
uv run --offline agentos gateway worker --once --json >/dev/null
uv run --offline agentos gateway status "$run_id" --json | uv run --offline python -c 'import json,sys; assert json.load(sys.stdin)["status"] == "succeeded"'
uv run --offline agentos gateway events "$run_id" --json >/dev/null

echo "PASS agentos-gateway-core"
