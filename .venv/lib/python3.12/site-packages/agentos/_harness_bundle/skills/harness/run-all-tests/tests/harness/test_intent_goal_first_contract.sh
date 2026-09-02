#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

require_pattern() {
  local path="$1"
  local pattern="$2"
  if ! grep -Eq "$pattern" "$PROJECT_ROOT/$path"; then
    echo "missing intent-goal-first contract: $path pattern=$pattern" >&2
    exit 1
  fi
}

require_pattern ".agents/skills/harness/intent-clarification/SKILL.md" "One Question Protocol"
require_pattern ".agents/skills/harness/intent-clarification/SKILL.md" "질문 순서는 항상 사용자 목적"
require_pattern ".agents/skills/harness/intent-clarification/SKILL.md" "표면적인 작업 방식 질문은 목적이 선명해지기 전까지 뒤로 미룬다"
require_pattern ".agents/skills/harness/intent-clarification/SKILL.md" "필수 핵심 질문"
require_pattern ".agents/skills/harness/intent-clarification/SKILL.md" "코드베이스에서 답할 수 있으면"
require_pattern ".agents/skills/harness/intent-clarification/SKILL.md" "선택지를 통해 자기 의도를 스스로 확인"

require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "사용자 목적"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "목적 중심"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "완료 기준"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "표면적인 작업 방식"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "one clear question"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "권장 답"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "반복 질문"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "필수 핵심 질문"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "선택지를 통해 자기 의도를 스스로 확인"

require_pattern ".agents/agents/harness/plan-reviewer.md" "Purpose-first Planning Guard"
require_pattern ".agents/agents/harness/plan-reviewer.md" "표면적인 작업 방식"
require_pattern ".agents/agents/harness/plan-reviewer.md" "반복 질문"
require_pattern ".agents/agents/harness/plan-reviewer.md" "코드베이스에서 답할 수 있으면"
require_pattern ".agents/agents/harness/plan-reviewer.md" "필수 핵심 질문"
require_pattern ".agents/agents/harness/plan-reviewer.md" "agent 기반 Gate 2"
require_pattern ".agents/agents/harness/plan-reviewer.md" "선택지를 통해 자기 의도를 스스로 확인"

require_pattern ".agents/agents/harness/usability-reviewer.md" "one clear question"
require_pattern ".agents/agents/harness/usability-reviewer.md" "반복되거나 near-duplicate 질문"
require_pattern ".agents/agents/harness/usability-reviewer.md" "사용자 목적"
require_pattern ".agents/agents/harness/usability-reviewer.md" "다음 행동"
require_pattern ".agents/agents/harness/usability-reviewer.md" "선택지를 통해 자기 의도를 스스로 확인"

require_pattern "docs/project/02-product-scope-and-requirements.md" "US-06 \\(목적 중심 계획\\)"
require_pattern "docs/project/02-product-scope-and-requirements.md" "REQ-021"
require_pattern "docs/project/02-product-scope-and-requirements.md" "REQ-026"
require_pattern "docs/project/05-agent-operating-contract.md" "계획 인터뷰 계약"
require_pattern "docs/project/05-agent-operating-contract.md" "one clear question"
require_pattern "docs/project/05-agent-operating-contract.md" "표면적인 작업 방식"
require_pattern "docs/project/05-agent-operating-contract.md" "선택지를 통해 자기 의도를 스스로 확인"

echo "PASS intent-goal-first-contract"
