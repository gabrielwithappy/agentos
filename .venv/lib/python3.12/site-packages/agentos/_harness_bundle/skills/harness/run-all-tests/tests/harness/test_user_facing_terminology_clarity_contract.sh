#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

require_pattern() {
  local path="$1"
  local pattern="$2"
  if ! grep -Eq "$pattern" "$PROJECT_ROOT/$path"; then
    echo "missing term clarity contract: $path pattern=$pattern" >&2
    exit 1
  fi
}

require_pattern ".agents/agents/harness/usability-reviewer.md" "### Term Clarity"
require_pattern ".agents/agents/harness/usability-reviewer.md" "user language before implementation language"
require_pattern ".agents/agents/harness/usability-reviewer.md" "first use"
require_pattern ".agents/agents/harness/usability-reviewer.md" "specialist terms"
require_pattern ".agents/agents/harness/usability-reviewer.md" "action, safety, recovery, or completion"

require_pattern ".agents/agents/harness/plan-reviewer.md" "unexplained specialist terms"
require_pattern ".agents/agents/harness/plan-reviewer.md" "사용자 언어"
require_pattern ".agents/agents/harness/plan-reviewer.md" "다음 행동, 완료 판단, 안전, 복구"

require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "user language before technical terms"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "first use"
require_pattern ".agents/skills/harness/writing-plans/SKILL.md" "specialist term"

require_pattern ".agents/skills/harness/writing-plans/plan-review-checklist.md" "Term Clarity"
require_pattern ".agents/skills/harness/writing-plans/plan-review-checklist.md" "용어 명확성"
require_pattern ".agents/skills/harness/writing-plans/plan-review-checklist.md" "다음 행동.*완료 판단.*안전.*복구"

scan_paths=(
  "README.md"
  "README.ko.md"
  "bootstrap/README.md"
  "docs/project/README.md"
  "docs/project/document-governance.md"
  "docs/project/template"
  "bin/aha"
  "setup.sh"
  ".agents/agents/harness/usability-reviewer.md"
  ".agents/agents/harness/plan-reviewer.md"
  ".agents/skills/harness/writing-plans/SKILL.md"
  ".agents/skills/harness/writing-plans/plan-review-checklist.md"
)

while IFS= read -r path; do
  if grep -Eqi "dossier" "$PROJECT_ROOT/$path"; then
    if ! grep -Eqi "dossier[[:space:]]*(means|is|=|:|\\(|는|란)" "$PROJECT_ROOT/$path"; then
      echo "offending path: $path" >&2
      echo "recovery expectation: replace 'dossier' with user-language wording or explain the term at first use" >&2
      exit 1
    fi
  fi
done < <(
  for item in "${scan_paths[@]}"; do
    if [ -d "$PROJECT_ROOT/$item" ]; then
      find "$PROJECT_ROOT/$item" -type f -name '*.md' -o -type f -name '*.sh' -o -type f -name '*.py'
    elif [ -f "$PROJECT_ROOT/$item" ]; then
      printf '%s\n' "$PROJECT_ROOT/$item"
    fi
  done | sed "s#^$PROJECT_ROOT/##" | sort -u
)

echo "PASS user-facing-terminology-clarity-contract"
