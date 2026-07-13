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
LOOP_SCRIPT="$PROJECT_ROOT/.agents/skills/harness/harness-loop.sh"
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
echo "=== [T2] canonical harness-loop.sh ==="

# T2-1: --help 정상 출력
check "T2-1: --help exits 0" \
  'bash "$LOOP_SCRIPT" --help > /dev/null'

# T2-2: --dry-run 정상 동작 (cli 호출 없음)
check "T2-2: --dry-run exits 0" \
  'bash "$LOOP_SCRIPT" "test prompt" --dry-run --cli claude > /dev/null'

# T2-3: --resume without state file → exit 1
STATE_FILE="$PROJECT_ROOT/.agents/traces/harness/loop-state.md"
[ -f "$STATE_FILE" ] && cp "$STATE_FILE" "${STATE_FILE}.bak.$$"
rm -f "$STATE_FILE"
check "T2-3: --resume no state → exit 1" \
  '! bash "$LOOP_SCRIPT" --resume 2>/dev/null'
[ -f "${STATE_FILE}.bak.$$" ] && mv "${STATE_FILE}.bak.$$" "$STATE_FILE"

# T2-4: 프롬프트 없이 실행 → exit 1
check "T2-4: no prompt → exit 1" \
  '! bash "$LOOP_SCRIPT" 2>/dev/null'

# T2-5: loop-state.md가 --dry-run 후 생성됨
[ -f "$STATE_FILE" ] && cp "$STATE_FILE" "${STATE_FILE}.bak.$$"
rm -f "$STATE_FILE"
bash "$LOOP_SCRIPT" "test" --dry-run --cli claude > /dev/null 2>&1 || true
check "T2-5: loop-state.md created after dry-run" \
  'test -f "$STATE_FILE"'
rm -f "$STATE_FILE"
[ -f "${STATE_FILE}.bak.$$" ] && mv "${STATE_FILE}.bak.$$" "$STATE_FILE"

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T3] AGENTS.md 구조 (Done When 체크리스트) ==="

check "T3-1: 섹션 6개 이상 존재" \
  '[[ "$(grep -c "^## " "$AGENT_MD")" -ge 6 ]]'

check "T3-2: 핵심 우선순위 (신뢰성/지속성/효율성/단순성)" \
  'grep -q "신뢰성" "$AGENT_MD" && grep -q "지속성" "$AGENT_MD" && grep -q "효율성" "$AGENT_MD" && grep -q "단순성" "$AGENT_MD"'

check "T3-3: Rule 1~5 규칙" \
  '[[ "$(grep -c "^### Rule [1-5]" "$AGENT_MD")" -ge 4 ]]'

check "T3-4: 파라미터 4개" \
  '[[ "$(grep -c "^| \`repeat_error_threshold\`\|^| \`max_loop_iterations\`\|^| \`cd_score_limit\`\|^| \`heartbeat_interval\`" "$AGENT_MD")" == "4" ]]'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T4] 파일 구조 및 접근성 ==="

check "T4-1: HISTORY.md 첫 줄 포함" \
  'head -1 "$HISTORY_MD" | grep -q "Harness Evolution History"'

check "T4-2: .agents/skills/harness/ 파일 확인" \
  '[[ $(find "$PROJECT_ROOT/.agents/skills/harness/" -type f ! -path "*/__pycache__/*" | wc -l) -ge 10 ]]'

check "T4-3: escalation-template.md 존재" \
  'test -f "$PROJECT_ROOT/.agents/skills/harness/core-engine/templates/escalation-template.md"'

check "T4-4: Score-cd.sh 실행 권한" \
  'test -x "$CD_SCRIPT"'

check "T4-5: canonical harness-loop.sh 실행 권한" \
  'test -x "$LOOP_SCRIPT"'

check "T4-6: Brain 폴더 구조 확인" \
  'test -d "$PROJECT_ROOT/.agents/skills/harness/brain/resources/"'

check "T4-7: history checkpoint contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_history_checkpoint_contract.sh" | grep -qx "PASS history-checkpoint-contract"'

check "T4-8: harness agent contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh" | grep -qx "PASS agent-contracts"'

check "T4-9: global-aha install contract" \
  '(tmp="$(mktemp)"; bash "$PROJECT_ROOT/tests/harness/test_aha_installed_command_health.sh" > "$tmp"; rc=$?; if [[ "$rc" -eq 0 ]]; then grep -q "PASS aha-wrapper-root-resolution" "$tmp"; rc=$?; fi; rm -f "$tmp"; exit "$rc")'

check "T4-10: global routine helper contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_global_routine_helper_contract.sh" | grep -qx "PASS installed-routine-cli-contract"'

check "T4-11: routine executor contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_routine_executor_contract.sh" | grep -qx "PASS routine-executor-focused-regression"'

check "T4-12: routine scheduler contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_routine_scheduler_contract.sh" | grep -qx "PASS aha-routine-scheduler-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T5] loop-state.md 일관성 ==="

# dry-run으로 loop-state.md 생성 후 검사
[ -f "$LOOP_STATE" ] && cp "$LOOP_STATE" "${LOOP_STATE}.bak.$$"
rm -f "$LOOP_STATE"
bash "$LOOP_SCRIPT" "test" --dry-run --cli claude > /dev/null 2>&1 || true

check "T5-1: loop-state.md 생성됨" \
  'test -f "$LOOP_STATE"'

check "T5-2: harness_version 존재" \
  'grep -q "harness_version" "$LOOP_STATE"'

check "T5-3: harness_version = 1.0" \
  'grep -q "harness_version.*1.0" "$LOOP_STATE"'

rm -f "$LOOP_STATE"
[ -f "${LOOP_STATE}.bak.$$" ] && mv "${LOOP_STATE}.bak.$$" "$LOOP_STATE"

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T6] requirement-discovery output contract ==="

check "T6-1: requirement-discovery output contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_requirement_discovery_output_contract.sh" | grep -q "PASS requirement-discovery-output-contract"'

echo ""
echo "=== [T7] agent project template contract ==="

check "T7-1: agent project template contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_agent_project_template_contract.sh" | grep -q "PASS agent-project-template-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T8] dependency gate contract ==="

check "T8-1: dependency-gate-contract" \
  '[[ "$(bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_dependency_gate_contract.sh")" == "PASS dependency-gate-contract" ]]'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T9] safety security prompt contract ==="

check "T9-1: safety security prompt contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_safety_security_prompt_contract.sh" all | grep -q "PASS safety-security-prompt-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T10] skill inspection reference contract ==="

check "T10-1: skill inspection reference contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_skill_inspection_reference_contract.sh" | grep -q "PASS skill-inspection-reference-contract"'

echo ""
echo "=== [T11] brain context hygiene contract ==="

check "T11-1: brain context hygiene contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_brain_context_hygiene_contract.sh"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T12] harness skill suitability contract ==="

check "T12-1: harness skill suitability contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_harness_skill_suitability_contract.sh" | grep -q "PASS harness-skill-suitability-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T13] AHA real folder workflow ==="

check "T13-1: AHA setup/apply real folder workflow" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_installed_command_health.sh" | grep -q "PASS aha-installed-real-folder-workflow"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T14] AHA project runtime verification ==="

check "T14-1: AHA project runtime verification" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_project_runtime_verification.sh" --simulated-only | grep -q "PASS aha-project-runtime-smoke"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T15] AHA Skill Catalog install ==="

check "T15-1: AHA Skill Catalog install" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_skill_catalog_install.sh" | grep -q "PASS aha-skill-catalog-install"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T16] AHA agent catalog install ==="

check "T16-1: AHA agent catalog install" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_agent_catalog_install.sh" | grep -qx "PASS aha-agent-catalog-install"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T17] AHA evolution intake ==="

check "T17-1: AHA evolution intake" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_evolution_intake.sh" | grep -qx "PASS aha-evolution-intake"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T18] plan lifecycle completion contract ==="

check "T18-1: plan lifecycle completion contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_plan_lifecycle_completion_contract.sh" | grep -qx "PASS plan-completion-lifecycle-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T19] evolution visibility contract ==="

check "T19-1: evolution visibility contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_evolution_visibility_contract.sh" | grep -qx "PASS evolution-visibility-regression"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T20] user-facing terminology clarity ==="

check "T20-1: user-facing terminology clarity contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_user_facing_terminology_clarity_contract.sh" | grep -qx "PASS user-facing-terminology-clarity-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T21] plan markdown metadata rendering ==="

check "T21-1: plan markdown metadata contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_plan_markdown_metadata_contract.sh" | grep -qx "PASS plan-markdown-metadata-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T22] Costmaster harness transfer contract ==="

check "T22-1: costmaster-harness-transfer-contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_costmaster_harness_transfer_contract.sh" | grep -qx "PASS costmaster-harness-transfer-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T23] intent-goal-first contract ==="

check "T23-1: intent-goal-first contract" \
  'bash "$PROJECT_ROOT/.agents/skills/harness/run-all-tests/tests/harness/test_intent_goal_first_contract.sh" | grep -qx "PASS intent-goal-first-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T24] AHA knowledge observability contract ==="

check "T24-1: AHA knowledge observability contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_knowledge_observability_contract.sh" | grep -qx "PASS aha-knowledge-observability-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T25] AHA active plan management contract ==="

check "T25-1: AHA active plan management contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_active_plan_management_contract.sh" | grep -qx "PASS aha-active-plan-management-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T26] AHA knowledge tags contract ==="

check "T26-1: AHA knowledge tags contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_knowledge_tags_contract.sh" | grep -qx "PASS aha-knowledge-tags-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T27] AHA knowledge import contract ==="

check "T27-1: AHA knowledge import contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_aha_knowledge_import_contract.sh" | grep -qx "PASS aha-knowledge-import-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T28] YouTube transcript knowledge skill ==="

check "T28-1: youtube-transcript-knowledge-skill" \
  'bash "$PROJECT_ROOT/tests/harness/test_youtube_transcript_knowledge_skill.sh" | grep -qx "PASS youtube-transcript-knowledge-skill"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T29] token resume checkpoint contract ==="

check "T29-1: token resume checkpoint contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_token_resume_checkpoint_contract.sh" | grep -qx "PASS token-resume-checkpoint-contract"'

# ─────────────────────────────────────────────────────
echo ""
echo "=== [T30] token resume Discord alert contract ==="

check "T30-1: token resume Discord alert contract" \
  'bash "$PROJECT_ROOT/tests/harness/test_token_resume_discord_alert_contract.sh" | grep -qx "PASS token-resume-discord-alert-contract"'

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
