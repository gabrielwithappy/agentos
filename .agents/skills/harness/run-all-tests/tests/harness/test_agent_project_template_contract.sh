#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

required_files=(
  ".agents/skills/harness/requirement-discovery/SKILL.md"
  ".agents/agents/harness/goal-alignment-reviewer.md"
  "docs/project/README.md"
  "docs/project/document-governance.md"
  "docs/project/template/reference/decisions/README.md"
  "docs/project/template/reference/implementation/README.md"
  "docs/project/template/reference/operations/README.md"
  "docs/project/template/00-project-index.md"
  "docs/project/template/01-project-charter.md"
  "docs/project/template/02-product-scope-and-requirements.md"
  "docs/project/template/03-system-contract.md"
  "docs/project/template/04-safety-risk-verification.md"
  "docs/project/template/05-agent-operating-contract.md"
  "docs/project/template/06-decisions-progress-change-log.md"
  "docs/project/template/reference/README.md"
)

for file in "${required_files[@]}"; do
  test -f "$file"
done

alignment_paths=(
  "docs/project/reference/implementation/01-requirement-brief.md"
  "docs/project/reference/implementation/02-user-stories.md"
  "docs/project/reference/implementation/03-rtm.md"
  "docs/project/reference/implementation/04-implementation-guide.md"
)

for path in "${alignment_paths[@]}"; do
  grep -Eq "$path" .agents/skills/harness/requirement-discovery/SKILL.md
done
grep -Eq "docs/project/reference/implementation/01-requirement-brief.md" .agents/agents/harness/goal-alignment-reviewer.md
! grep -Eq "docs/project/01-requirement-brief.md|docs/project/02-user-stories.md|docs/project/03-rtm.md|docs/project/04-implementation-guide.md" \
  .agents/skills/harness/requirement-discovery/SKILL.md \
  .agents/agents/harness/goal-alignment-reviewer.md

grep -Eq "does not override" docs/project/template/reference/implementation/README.md

! grep -Eq "architecture/wireframes" \
  docs/project/README.md \
  docs/project/document-governance.md \
  docs/project/template/01-project-charter.md \
  docs/project/template/06-decisions-progress-change-log.md \
  docs/project/template/reference/README.md

! grep -Eq "reference/alignment/" docs/project/README.md docs/project/document-governance.md docs/project/template/reference/README.md
grep -Eq "supporting docs" docs/project/template/reference/README.md
grep -Eq "root project documents" docs/project/README.md docs/project/template/00-project-index.md docs/project/template/06-decisions-progress-change-log.md
grep -Eq "active execution plan" docs/project/README.md docs/project/document-governance.md docs/project/template/reference/README.md
grep -Eq "프로젝트 문서 템플릿 패키지" docs/project/README.md
grep -Eq "대상 프로젝트" docs/project/README.md
grep -Eq "docs/project/template/" docs/project/README.md
grep -Eq "런타임 경계" docs/project/document-governance.md
grep -Eq "생성된 상태는 template source가 아니다" docs/project/document-governance.md
grep -Eq "Agent Harness 소유 supporting material" docs/project/document-governance.md
grep -Eq 'project document set' docs/project/document-governance.md
grep -Eq "통제된 확장이 촉발될 때만 supporting reference를 추가" docs/project/document-governance.md
grep -Eq "최소 카테고리" docs/project/template/reference/README.md

supporting_categories=(
  "implementation"
  "decisions"
  "operations"
)

for category in "${supporting_categories[@]}"; do
  test -f "docs/project/template/reference/$category/README.md"
  grep -Eq "reference/$category/" docs/project/README.md docs/project/template/00-project-index.md
  grep -Eq "$category/" docs/project/template/reference/README.md
  grep -Eq "template/reference/$category/README.md" bin/aha
  grep -Eq "reference/$category/README.md" bin/aha
  grep -Eq "does not override" "docs/project/template/reference/$category/README.md"
done

! rg -n "Costmaster|ys-costmaster|CostItemMaster|원가항목|Browser QA script" docs/project >/dev/null

grep -Eq "value, stakeholder" docs/project/template/01-project-charter.md
grep -Eq '현재 증거 / 최신성' docs/project/template/01-project-charter.md

grep -Eq "범위 경계" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "Evidence link" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "검증 근거" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "reference/implementation/" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "좋아하는 레퍼런스" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "피해야 하는 레퍼런스" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "information density" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "visual hierarchy" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "tone" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "failure screen characteristics" docs/project/template/02-product-scope-and-requirements.md

grep -Eq "인터페이스 계약" docs/project/template/03-system-contract.md
grep -Eq "Architecture characteristics" docs/project/template/03-system-contract.md
grep -Eq "Architecture style" docs/project/template/03-system-contract.md
grep -Eq "Logical components" docs/project/template/03-system-contract.md
grep -Eq "Architecture decisions" docs/project/template/03-system-contract.md
grep -Eq "reference/implementation/" docs/project/template/03-system-contract.md
grep -Eq "file ownership" docs/project/template/05-agent-operating-contract.md
grep -Eq "interface" docs/project/template/03-system-contract.md
grep -Eq "현재 wireframe/design supporting doc" docs/project/template/02-product-scope-and-requirements.md
grep -Eq "되돌리기 어려운 작업과 복구" docs/project/template/03-system-contract.md

grep -Eq "검증 매트릭스" docs/project/template/04-safety-risk-verification.md
grep -Eq "Run" docs/project/template/04-safety-risk-verification.md
grep -Eq "Expected" docs/project/template/04-safety-risk-verification.md
grep -Eq "artifact manifest" docs/project/template/04-safety-risk-verification.md
grep -Eq "integration or API contract checks" docs/project/template/04-safety-risk-verification.md

grep -Eq "핸드오프 상태" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "next safe action" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "plan=" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "artifact=" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "verification=" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "reference/decisions/" docs/project/template/06-decisions-progress-change-log.md
grep -Eq "최신 검증 근거" docs/project/template/06-decisions-progress-change-log.md

echo "PASS_AGENT_PROJECT_TEMPLATE_CONTRACT"
echo "PASS agent-project-template-contract"
