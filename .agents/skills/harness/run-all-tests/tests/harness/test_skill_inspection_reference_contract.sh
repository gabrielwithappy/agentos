#!/usr/bin/env bash
# Validate Hermes-derived skill inspection and architecture reference contracts.

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

SKILL_ROUTING="$PROJECT_ROOT/.agents/skills/harness/brain/resources/skill-routing.md"
CONTEXT_LOADING="$PROJECT_ROOT/.agents/skills/harness/brain/resources/context-loading.md"
WRITING_PLANS="$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
BACKLOG="$PROJECT_ROOT/docs/project/reference/decisions/hermes-adoption-implementation-backlog.md"
ARCH_README="$PROJECT_ROOT/docs/project/reference/decisions/README.md"
REF_README="$PROJECT_ROOT/docs/project/reference/README.md"

grep -Eq "Progressive Disclosure|progressive disclosure" "$SKILL_ROUTING" "$CONTEXT_LOADING"
grep -Eq "SKILL.md" "$SKILL_ROUTING" "$CONTEXT_LOADING"
grep -Eq "referenced files|referenced files only|필요한.*파일" "$SKILL_ROUTING" "$CONTEXT_LOADING"
grep -Eq "user skill.*harness skill|user skill first" "$SKILL_ROUTING" "$CONTEXT_LOADING"
grep -Eq 'no Hermes skill runtime|No new skill runtime|no `skill_view` tool' "$SKILL_ROUTING" "$CONTEXT_LOADING" "$BACKLOG"

grep -Eq "analysis artifact|backlog filter|not implementation approval|separate reviewed plan" "$WRITING_PLANS"

test -s "$BACKLOG"
grep -Eq "2026-05-03-hermes-agent-harness-adoption-analysis.md" "$BACKLOG"
grep -Eq "runtime diagnostics" "$BACKLOG"
grep -Eq "skill inspection" "$BACKLOG"
grep -Eq "safety security prompt" "$BACKLOG"
grep -Eq "Rejected or deferred" "$BACKLOG"
grep -Eq "No Hermes gateway" "$BACKLOG"

grep -Eq "hermes-adoption-implementation-backlog" "$ARCH_README" "$REF_README"
grep -Eq "execution plan SSOT|active execution plan|architecture reference" "$ARCH_README" "$REF_README"

if grep -nE "from hermes|import hermes|skill_view\\(|HermesSkill|plugin_runtime|gateway service" \
  "$SKILL_ROUTING" "$CONTEXT_LOADING" "$WRITING_PLANS" "$BACKLOG" "$ARCH_README" "$REF_README" |
  grep -Ev 'no `skill_view` tool|No new skill runtime|no Hermes skill runtime|No Hermes plugin-runtime|No Hermes memory provider|No Hermes gateway|not a Hermes skill runtime|no plugin-runtime import'; then
  echo "FAIL unexpected Hermes runtime import wording"
  exit 1
fi

echo "PASS skill-inspection-reference-contract"
