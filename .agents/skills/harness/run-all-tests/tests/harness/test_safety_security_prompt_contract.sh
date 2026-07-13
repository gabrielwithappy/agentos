#!/usr/bin/env bash
# Validate safety/security/prompt boundary reviewer contracts and careful guard behavior.

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
CARE="${PROJECT_ROOT}/.agents/skills/harness/careful/bin/check-careful.sh"

assert_rg() {
  local pattern="$1"
  shift
  grep -Eq "$pattern" "$@"
}

test_careful() {
  assert_blocked() {
    local command="$1"
    local blocked
    blocked="$(printf '{"command":%s}' "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$command")" | bash "$CARE")"
    python3 - "$blocked" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
assert payload["decision"] == "block", payload
assert "careful-dangerous-command" in payload["reason"], payload
PY
  }

  assert_blocked "rm -rf /tmp/harness-contract"
  assert_blocked "psql -c 'DROP TABLE users'"
  assert_blocked "psql -c 'DROP DATABASE prod'"
  assert_blocked "git push --force origin main"
  assert_blocked "git push -f origin main"
  assert_blocked "git reset --hard"
  assert_blocked "psql -c 'TRUNCATE TABLE users'"
  assert_blocked "mkfs.ext4 /dev/sdb"

  local allowed_output
  allowed_output="$(printf '{"command":"python3 -m pytest"}' | bash "$CARE")"
  test -z "$allowed_output"

  echo "PASS careful-dangerous-command-contract"
}

test_docs() {
  assert_rg "protected path bypass" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "secret leakage" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "environment filtering" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "prompt injection" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "destructive command" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "research-to-implementation creep" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "OWASP" "${PROJECT_ROOT}/catalog/agents/qa-reviewer/AGENT.md"
  assert_rg "Secret/Env Governance" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md"
  assert_rg "Prompt Boundary Governance" "${PROJECT_ROOT}/.agents/agents/harness/principle-auditor.md"
  assert_rg "security-sensitive" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "protected path bypass" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "secret leakage" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "prompt injection" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"
  assert_rg "FAIL" "${PROJECT_ROOT}/.agents/agents/harness/plan-reviewer.md"

  assert_rg "Prompt Injection Boundary" "${PROJECT_ROOT}/.agents/skills/harness/brain/resources/prompt-structure.md"
  assert_rg "instruction precedence" "${PROJECT_ROOT}/.agents/skills/harness/brain/resources/prompt-structure.md"
  assert_rg "Secret leakage" "${PROJECT_ROOT}/.agents/skills/harness/brain/resources/prompt-structure.md"
  assert_rg "Environment filtering" "${PROJECT_ROOT}/.agents/skills/harness/brain/resources/prompt-structure.md"
  assert_rg "careful-dangerous-command" "${PROJECT_ROOT}/.agents/skills/harness/careful/SKILL.md" "$CARE"

  echo "PASS safety-security-prompt-docs-contract"
}

case "${1:-all}" in
  careful)
    test_careful
    ;;
  docs)
    test_docs
    ;;
  all)
    test_careful
    test_docs
    echo "PASS safety-security-prompt-contract"
    ;;
  *)
    echo "usage: $0 [careful|docs|all]" >&2
    exit 2
    ;;
esac
