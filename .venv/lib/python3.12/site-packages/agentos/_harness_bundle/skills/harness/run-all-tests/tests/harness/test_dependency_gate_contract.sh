#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
from pathlib import Path

writing = Path(".agents/skills/harness/writing-plans/SKILL.md").read_text(encoding="utf-8")
checklist = Path(".agents/skills/harness/writing-plans/plan-review-checklist.md").read_text(encoding="utf-8")
reviewer = Path(".agents/agents/harness/plan-reviewer.md").read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit(message)

def between(text, start, end):
    require(start in text, f"missing section start: {start}")
    body = text.split(start, 1)[1]
    if end:
        require(end in body, f"missing section end after {start}: {end}")
        body = body.split(end, 1)[0]
    return body

dependency_contract = between(
    writing,
    "## 의존성 분석",
    "## HISTORY Checkpoint Tagging Contract",
)
for token in [
    "## 의존성 게이트",
    "외부 의존성: 없음",
    "스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.",
    "external-service",
    "credential",
    "plugin",
    "mcp",
    "live-runtime",
    "network",
    "nonstandard-local-tool",
    "preflight:",
    "Run:",
    "Expected:",
    "fallback:",
    "available: false",
    "reason:",
    "failure_behavior: NEEDS_CONTEXT",
    "available: true",
    "trigger:",
    "action:",
    "limits:",
    "verification:",
    "failure_behavior: use_fallback",
    "Task 0",
    "자동",
]:
    require(token in dependency_contract, f"missing dependency contract token: {token}")

gate0 = between(writing, "### Gate 0: Plan Quality Gate", "### Gate 1:")
gate1 = between(writing, "### Gate 1:", "### Worktree Decision Gate")
for token in [
    "의존성 분석",
    "의존성 게이트",
    "기술 스택",
    "파일 구조",
    "planned `Run:` commands",
    "runtime assumptions",
    "preflight",
    "fallback",
    "failure_behavior",
]:
    require(token in gate0 + gate1, f"missing Gate 0/Gate 1 dependency token: {token}")

for token in [
    "의존성 분석",
    "의존성 게이트",
    "preflight",
    "fallback.available",
    "fallback verification",
    "failure_behavior",
    "writing-plans/SKILL.md",
]:
    require(token in checklist, f"missing checklist dependency token: {token}")

for token in [
    "External Dependency",
    "의존성 분석",
    "의존성 게이트",
    "undeclared external dependency",
    "preflight Run/Expected",
    "fallback verification",
    "failure_behavior",
    "NEEDS_CONTEXT",
    "MCP",
    "automatic enable",
]:
    require(token in reviewer, f"missing reviewer dependency token: {token}")

mcp_fixture = """
## 의존성 분석
- 외부 의존성: 아래에 선언함
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.

## 의존성 게이트
### codex-mcp
- name: codex-mcp
- type: mcp
- required: true
- purpose: inspect external MCP registry
- preflight:
  Run: `bash .codex/use-mcp-config.sh --check && echo PASS codex-mcp-ready`
  Expected: `PASS codex-mcp-ready`
- fallback:
  available: false
  reason: `MCP registry inspection has no local equivalent`
- failure_behavior: NEEDS_CONTEXT
"""
none_fixture = """
## 의존성 분석
- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.
"""
for token in ["type: mcp", "preflight:", "Expected: `PASS codex-mcp-ready`", "failure_behavior: NEEDS_CONTEXT"]:
    require(token in mcp_fixture, f"bad mcp fixture: {token}")
for token in ["외부 의존성: 없음", "스캔 기준: 기술 스택"]:
    require(token in none_fixture, f"bad none fixture: {token}")

print("PASS dependency-gate-contract")
PY
