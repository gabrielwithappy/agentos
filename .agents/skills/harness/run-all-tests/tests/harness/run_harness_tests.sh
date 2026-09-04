#!/usr/bin/env bash
# .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh — 하네스 컴포넌트 검증
# Usage: bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh

set -uo pipefail

# Ensure tests never pollute user's ~/.bashrc or other shell config
export AHA_SKIP_SHELL_CONFIG=1

PASS=0; FAIL=0
PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
export PATH="$PROJECT_ROOT/.agents/shims:$PATH"
hash -r 2>/dev/null || true
CD_SCRIPT="$PROJECT_ROOT/.agents/skills/harness/core-engine/scripts/score-cd.sh"
AGENT_MD="$PROJECT_ROOT/AGENTS.md"
HISTORY_MD="$PROJECT_ROOT/HISTORY.md"
LOOP_STATE="$PROJECT_ROOT/.agents/traces/harness/loop-state.md"

check() {
  local name="$1"; shift
  if eval "$@" 2>/dev/null; then
    echo "  PASS: $name"; PASS=$((PASS+1))
  else
    echo "  FAIL: $name"; FAIL=$((FAIL+1))
  fi
}

# ─────────────────────────────────────────────────────
echo "=== [T1] score-cd.sh ==="

# T1-1: 없는 파일 → 0
check "T1-1: nonexistent → 0" \
  '[[ "$(bash "$CD_SCRIPT" /tmp/nonexistent_$$)" == "0" ]]'

# T1-2: ESCALATION 없는 HISTORY → 0
TMP=$(mktemp)
echo "# Harness Evolution History" > "$TMP"
echo "[2026-03-25T00:00:00Z] [INIT] test" >> "$TMP"
check "T1-2: no ESCALATION → 0" \
  '[[ "$(bash "$CD_SCRIPT" "$TMP")" == "0" ]]'
rm -f "$TMP"

# T1-3: ESCALATION 1개 → 1
TMP=$(mktemp)
echo "[2026-03-25T00:00:00Z] [ESCALATION] test1" > "$TMP"
check "T1-3: 1 ESCALATION → 1" \
  '[[ "$(bash "$CD_SCRIPT" "$TMP")" == "1" ]]'
rm -f "$TMP"

# T1-4: ESCALATION 3개 → 3
TMP=$(mktemp)
printf "[ESCALATION] a\n[ESCALATION] b\n[ESCALATION] c\n" > "$TMP"
check "T1-4: 3 ESCALATION → 3" \
  '[[ "$(bash "$CD_SCRIPT" "$TMP")" == "3" ]]'
rm -f "$TMP"

# T1-5: 단일 출력 (줄 수 = 1)
TMP=$(mktemp)
echo "[INIT] test" > "$TMP"
check "T1-5: single line output" \
  '[[ "$(bash "$CD_SCRIPT" "$TMP" | wc -l | tr -d " ")" == "1" ]]'
rm -f "$TMP"

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T3] AGENTS.md 구조 (Done When 체크리스트) ==="

check "T3-1: 섹션 6개 이상 존재" \
  '[[ "$(grep -c "^## " "$AGENT_MD")" -ge 6 ]]'

check "T3-2: 핵심 우선순위 (신뢰성/지속성/효율성/단순성)" \
  'grep -q "신뢰성" "$AGENT_MD" && grep -q "지속성" "$AGENT_MD" && grep -q "효율성" "$AGENT_MD" && grep -q "단순성" "$AGENT_MD"'

check "T3-3: Rule 1~5 규칙" \
  '[[ "$(grep -c "^### Rule [1-5]" "$AGENT_MD")" -ge 4 ]]'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T4] 파일 구조 및 접근성 ==="

check "T4-1: HISTORY.md 존재 및 기록 가능" \
  'test -s "$HISTORY_MD"'

check "T4-2: .agents/skills/harness/ 파일 확인" \
  '[[ $(find "$PROJECT_ROOT/.agents/skills/harness/" -type f ! -path "*/__pycache__/*" | wc -l) -ge 10 ]]'

check "T4-3: escalation-template.md 존재" \
  'test -f "$PROJECT_ROOT/.agents/skills/harness/core-engine/templates/escalation-template.md"'

check "T4-4: Score-cd.sh 실행 권한" \
  'test -x "$CD_SCRIPT"'

check "T4-6: Brain 폴더 구조 확인" \
  'test -d "$PROJECT_ROOT/.agents/skills/harness/brain/resources/"'

check "T4-7: history checkpoint contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_history_checkpoint_contract.sh" | grep -qEx "PASS[- ]history-checkpoint-contract"'

check "T4-8: harness agent contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh" | grep -qEx "PASS[- ]agent-contracts"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T6] requirement-discovery output contract ==="

check "T6-1: requirement-discovery output contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_requirement_discovery_output_contract.sh" | grep -qE "PASS[- ]requirement-discovery-output-contract"'

echo ""
echo "=== [T7] agent project template contract ==="

check "T7-1: agent project template contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_agent_project_template_contract.sh" | grep -qE "PASS[- ]agent-project-template-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T8] dependency gate contract ==="

check "T8-1: dependency-gate-contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_dependency_gate_contract.sh" | grep -qEx "PASS[- ]dependency-gate-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T9] safety security prompt contract ==="

check "T9-1: safety security prompt contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_safety_security_prompt_contract.sh" all | grep -qE "PASS[- ]safety-security-prompt-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T11] brain context hygiene contract ==="

check "T11-1: brain context hygiene contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_brain_context_hygiene_contract.sh"'

# ─────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────
echo ""
echo "=== [T18] plan lifecycle completion contract ==="

check "T18-1: plan lifecycle completion contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_plan_lifecycle_completion_contract.sh" | grep -qEx "PASS[- ]plan-completion-lifecycle-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T19] evolution visibility contract ==="

check "T19-1: evolution visibility contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_evolution_visibility_contract.sh" | grep -qEx "PASS[- ]evolution-visibility-regression"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T20] user-facing terminology clarity ==="

check "T20-1: user-facing terminology clarity contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_user_facing_terminology_clarity_contract.sh" | grep -qEx "PASS[- ]user-facing-terminology-clarity-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T21] plan markdown metadata rendering ==="

check "T21-1: plan markdown metadata contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_plan_markdown_metadata_contract.sh" | grep -qEx "PASS[- ]plan-markdown-metadata-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T22] Costmaster harness transfer contract ==="

check "T22-1: costmaster-harness-transfer-contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_costmaster_harness_transfer_contract.sh" | grep -qEx "PASS[- ]costmaster-harness-transfer-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T23] intent-goal-first contract ==="

check "T23-1: intent-goal-first contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_intent_goal_first_contract.sh" | grep -qEx "PASS[- ]intent-goal-first-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T24] harness pass protocol ==="

check "T24-1: normalized pass contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_harness_pass_protocol.sh" | grep -qEx "PASS[- ]normalized-pass-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "PASS=${PASS} FAIL=${FAIL}"
echo "결과: ${PASS} PASS / $((PASS+FAIL)) 전체"
[ "$FAIL" -eq 0 ] && echo "✅ 전체 통과" || echo "❌ ${FAIL}개 실패"
echo "========================================="

# HISTORY.md에 결과 기록
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [CHECKPOINT] 하네스 검증 완료 | PASS=${PASS} FAIL=${FAIL} | .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh" >> "$HISTORY_MD"

[ "$FAIL" -eq 0 ]
