#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
WRITING="$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
EXECUTING="$PROJECT_ROOT/.agents/skills/harness/executing-plans/SKILL.md"

grep -q 'plan=' "$WRITING"
grep -q 'artifact=' "$WRITING"
grep -q 'plan=' "$EXECUTING"
grep -q 'artifact=' "$EXECUTING"
grep -q 'generic health' "$WRITING" || grep -q '하네스 검증 완료' "$EXECUTING"
grep -q '사용자 결과' "$WRITING"
grep -q '진행 스냅샷' "$WRITING"
grep -q '사용자에게 보이는 마일스톤' "$WRITING"
grep -q '진행 스냅샷' "$EXECUTING"
grep -q '완료 신호' "$EXECUTING"
grep -q 'progress DB' "$EXECUTING"

echo "PASS history-checkpoint-contract"
