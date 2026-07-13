#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$ROOT_DIR"

assert_contains() {
  local file="$1"
  local token="$2"
  if ! grep -Fq "$token" "$file"; then
    echo "FAIL missing token: $token ($file)" >&2
    exit 1
  fi
}

assert_contains "catalog/agents/document-delivery-lead/AGENT.md" "current wireframe pair"
assert_contains "catalog/agents/document-delivery-lead/AGENT.md" "docs/project bundle readiness"
assert_contains ".agents/skills/harness/requirement-discovery/SKILL.md" "current wireframe pair"
assert_contains ".agents/skills/harness/requirement-discovery/SKILL.md" "좋아하는 레퍼런스"
assert_contains ".agents/skills/harness/requirement-discovery/SKILL.md" "One Question Protocol"
assert_contains ".agents/skills/harness/intent-clarification/SKILL.md" "user-facing frontend"
assert_contains ".agents/skills/harness/intent-clarification/SKILL.md" "docs/project bundle readiness"
assert_contains ".agents/skills/harness/intent-clarification/SKILL.md" "실패로 볼 화면 특성"
assert_contains "docs/project/README.md" "wireframe/design reference"
assert_contains "docs/project/document-governance.md" "supporting docs cannot override"
assert_contains "docs/project/document-governance.md" "UI work needs wireframe"
assert_contains "docs/project/template/reference/wireframes/README.md" "latest update handoff"
assert_contains "docs/project/template/reference/wireframes/README.md" "supporting refinement path"
assert_contains "docs/project/template/02-product-scope-and-requirements.md" "current wireframe/design supporting doc"
assert_contains "docs/project/template/02-product-scope-and-requirements.md" "Visual intent"
assert_contains "docs/project/template/05-agent-operating-contract.md" "unresolved scope question"
assert_contains "docs/project/template/06-decisions-progress-change-log.md" "Handoff state"

echo "PASS frontend-ui-intent-routing-contract"
