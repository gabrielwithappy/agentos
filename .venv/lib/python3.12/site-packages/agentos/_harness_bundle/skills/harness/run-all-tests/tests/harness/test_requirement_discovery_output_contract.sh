#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

files=(
  ".agents/skills/harness/requirement-discovery/SKILL.md"
  ".agents/agents/harness/goal-alignment-reviewer.md"
  "catalog/agents/document-delivery-lead/AGENT.md"
  "AGENTS.md"
  "docs/project/README.md"
  "docs/project/document-governance.md"
  "docs/project/template/06-decisions-progress-change-log.md"
)

for file in "${files[@]}"; do
  test -f "$file"
done

grep -Eq "Output Package Contract" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq 'docs/project` 문서 준비 상태' .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "DIAGNOSE" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "PROBE" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "SYNTHESIZE" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "docs/project/reference/implementation/01-requirement-brief.md" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "docs/project/reference/implementation/02-user-stories.md" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "docs/project/reference/implementation/03-rtm.md" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "docs/project/reference/implementation/04-implementation-guide.md" .agents/skills/harness/requirement-discovery/SKILL.md
! grep -Eq "docs/project/01-requirement-brief.md|docs/project/02-user-stories.md|docs/project/03-rtm.md|docs/project/04-implementation-guide.md" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "Intent Handoff" .agents/skills/harness/requirement-discovery/SKILL.md
grep -Eq "supporting discovery package" .agents/skills/harness/requirement-discovery/SKILL.md

grep -Eq "Requirement Brief-only" .agents/agents/harness/goal-alignment-reviewer.md
grep -Eq "supporting discovery package" .agents/agents/harness/goal-alignment-reviewer.md
grep -Eq "docs/project/reference/implementation/01-requirement-brief.md" .agents/agents/harness/goal-alignment-reviewer.md
grep -Eq "docs/project/reference/implementation/02-user-stories.md" .agents/agents/harness/goal-alignment-reviewer.md
grep -Eq "docs/project/reference/implementation/03-rtm.md" .agents/agents/harness/goal-alignment-reviewer.md
grep -Eq "docs/project/reference/implementation/04-implementation-guide.md" .agents/agents/harness/goal-alignment-reviewer.md
! grep -Eq "docs/project/01-requirement-brief.md|docs/project/02-user-stories.md|docs/project/03-rtm.md|docs/project/04-implementation-guide.md" .agents/agents/harness/goal-alignment-reviewer.md

grep -Eq 'docs/project` 문서 준비 상태' catalog/agents/document-delivery-lead/AGENT.md

grep -Eq "project document set" docs/project/README.md
grep -Eq "active execution plan" docs/project/README.md
grep -Eq "project document set" docs/project/document-governance.md
grep -Eq "active execution plan" docs/project/document-governance.md
grep -Eq "handoff state" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "Fresh verification evidence" docs/project/template/06-decisions-progress-change-log.md

grep -Eq "개발 입력 문서 패키지" AGENTS.md
grep -Eq "User Stories" AGENTS.md
grep -Eq "RTM" AGENTS.md
grep -Eq "Implementation Guide" AGENTS.md

echo "PASS requirement-discovery-output-contract"
