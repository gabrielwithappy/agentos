#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
AGENT_DIR="$PROJECT_ROOT/.agents/agents/harness"

if grep -RInE "AGENT\\.md|\\.agents/harness/scripts/sync-manifest\\.sh" "$AGENT_DIR" >/tmp/harness-agent-contracts.err; then
  cat /tmp/harness-agent-contracts.err >&2
  exit 1
fi

for agent in backend-engineer frontend-engineer qa-reviewer debug-investigator codebase-explorer document-delivery-lead; do
  test ! -e "$AGENT_DIR/$agent.md"
  grep -Eq "AGENTS\\.md" "$PROJECT_ROOT/catalog/agents/$agent/AGENT.md"
done
grep -Eq "AGENTS\\.md" "$AGENT_DIR/harness-architect.md"
grep -Eq "AGENTS\\.md" "$AGENT_DIR/principle-auditor.md"
grep -Eq "AGENTS\\.md" "$AGENT_DIR/usability-reviewer.md"

grep -Eq "\\.agents/skills/harness/sync-manifest/scripts/sync-manifest\\.sh --update" "$AGENT_DIR/harness-architect.md"
grep -Eq "Protected Path Governance" "$AGENT_DIR/principle-auditor.md"
grep -Eq "Runtime Contract Governance" "$AGENT_DIR/principle-auditor.md"
grep -Eq "Target Surface" "$AGENT_DIR/principle-auditor.md"
grep -Eq "KEEP \\| REVISE \\| BLOCK \\| APPROVE" "$AGENT_DIR/principle-auditor.md"
grep -Eq "Protected Path 추가 판정 규칙" "$AGENT_DIR/plan-reviewer.md"
grep -Eq "authorized_architects" "$AGENT_DIR/plan-reviewer.md"
grep -Eq "sync-manifest --update codex" "$AGENT_DIR/plan-reviewer.md"
grep -Eq "usability_review_required" "$AGENT_DIR/plan-reviewer.md"
grep -Eq "usability-reviewer" "$PROJECT_ROOT/AGENTS.md" "$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md" "$AGENT_DIR/plan-reviewer.md"
grep -Eq "User Journey" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "Prompt Comprehension" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "First-Time User" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "Error Recovery" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "cannot override AGENTS\\.md" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "secret redaction" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "protected-path approval" "$AGENT_DIR/usability-reviewer.md"
grep -Eq "Never modify source code" "$AGENT_DIR/usability-reviewer.md"

echo "PASS agent-contracts"
