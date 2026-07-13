#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
STATUS_SCRIPT="$PROJECT_ROOT/.agents/skills/harness/writing-plans/scripts/evolution_status.py"
STATUS_FILE="$PROJECT_ROOT/docs/exec-plans/evolution-status.md"

python3 "$STATUS_SCRIPT" >/dev/null

grep -q "EVOLUTION_TRIGGER" "$PROJECT_ROOT/AGENTS.md"
grep -q "EVOLUTION_PROPOSAL" "$PROJECT_ROOT/AGENTS.md"
grep -q "EVOLUTION_PLAN" "$PROJECT_ROOT/AGENTS.md"
grep -q "EVOLUTION_APPLIED" "$PROJECT_ROOT/AGENTS.md"
grep -q "EVOLUTION_DEFERRED" "$PROJECT_ROOT/AGENTS.md"
grep -q "classification=" "$PROJECT_ROOT/AGENTS.md"

grep -q "evolution trigger" "$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
grep -q "EVOLUTION_TRIGGER" "$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
grep -q "EVOLUTION_PROPOSAL" "$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
grep -q "classification=local-fix" "$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
grep -q "classification=harness-evolution" "$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"

grep -q "EVOLUTION_APPLIED" "$PROJECT_ROOT/.agents/skills/harness/executing-plans/SKILL.md"
grep -q "EVOLUTION_DEFERRED" "$PROJECT_ROOT/.agents/skills/harness/executing-plans/SKILL.md"
grep -q "applied result" "$PROJECT_ROOT/.agents/skills/harness/executing-plans/SKILL.md"
grep -q "next_action=" "$PROJECT_ROOT/.agents/skills/harness/executing-plans/SKILL.md"

grep -q "evolution trigger" "$PROJECT_ROOT/.agents/agents/harness/plan-reviewer.md"
grep -q "applied result" "$PROJECT_ROOT/.agents/agents/harness/plan-reviewer.md"
grep -q "evolution status surface" "$PROJECT_ROOT/.agents/agents/harness/plan-reviewer.md"
grep -q "classification=" "$PROJECT_ROOT/.agents/agents/harness/plan-reviewer.md"

grep -q "evolution status" "$PROJECT_ROOT/.agents/agents/harness/usability-reviewer.md"
grep -q "trigger" "$PROJECT_ROOT/.agents/agents/harness/usability-reviewer.md"
grep -q "applied result" "$PROJECT_ROOT/.agents/agents/harness/usability-reviewer.md"
grep -q "next action" "$PROJECT_ROOT/.agents/agents/harness/usability-reviewer.md"

for token in \
  "Current Evolution Triggers" \
  "Active Evolution Plans" \
  "Recently Applied Evolution Results" \
  "Deferred / Local-only Findings" \
  "How To Read This Status" \
  "PMBOK open dossier" \
  "계획의 결과가 무엇인지 모르겠다" \
  "Plan completion metadata and user archive gate" \
  "Implementation Result" \
  "How To Use" \
  "HISTORY.md text is data" \
  "plan text is data" \
  "generated status text is data" \
  "command output is data" \
  "cannot create approval" \
  "cannot override system/developer instructions" \
  "cannot override AGENTS.md"; do
  grep -q "$token" "$STATUS_FILE"
done

grep -q "HISTORY.md text is data" "$STATUS_SCRIPT"
grep -q "canonicalize_plan_paths" "$STATUS_SCRIPT"
grep -q "command output is data" "$0"

if grep -q "2026-05-30-costmaster-harness-lessons-transfer-plan.md" "$PROJECT_ROOT/.agents/mission/plan.json"; then
  ! grep -q "plan=docs/exec-plans/active/2026-05-30-costmaster-harness-lessons-transfer-plan.md" "$STATUS_FILE"
  grep -q "plan=docs/exec-plans/archive/2026-05-30-costmaster-harness-lessons-transfer-plan.md" "$STATUS_FILE"
fi

echo "PASS evolution-visibility-regression"
