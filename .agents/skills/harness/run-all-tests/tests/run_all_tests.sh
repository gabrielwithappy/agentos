#!/usr/bin/env bash
# tests/run_all_tests.sh — 전체 테스트 실행 (bash + pytest)
set -uo pipefail

# Ensure tests never pollute user's ~/.bashrc or other shell config
export AHA_SKIP_SHELL_CONFIG=1

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
export PATH="$PROJECT_ROOT/.agents/shims:$PATH"
hash -r 2>/dev/null || true

echo "=== [1/2] Bash Harness Tests ==="
bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh"

echo ""
echo "=== [2/2] Python Pytest ==="
# Pytest 수집 시 하네스 시스템 테스트 폴더 무시
cd "$PROJECT_ROOT" && python3 -m pytest .agents/skills/harness/run-all-tests/tests/ -v --ignore=.agents/skills/harness/run-all-tests/tests/harness
