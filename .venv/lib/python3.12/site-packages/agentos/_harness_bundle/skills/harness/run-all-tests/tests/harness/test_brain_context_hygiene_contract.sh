#!/usr/bin/env bash
# Validate brain context hygiene and file-first handoff contracts.

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

python3 - <<'PY' "$PROJECT_ROOT"
from pathlib import Path
import sys

root = Path(sys.argv[1])
brain = root / ".agents/skills/harness/brain"

index = (brain / "SKILL.md").read_text(encoding="utf-8")
current = (brain / "current-plan.md").read_text(encoding="utf-8")
context = (brain / "resources/context-loading.md").read_text(encoding="utf-8")
routing = (brain / "resources/skill-routing.md").read_text(encoding="utf-8")

memory_paths = [
    brain / "resources/memory-protocol.md",
    brain / "resources/execution/claude.md",
    brain / "resources/execution/codex.md",
    brain / "resources/execution/gemini.md",
]
memory_combined = "\n".join(path.read_text(encoding="utf-8") for path in memory_paths)

governance_paths = [
    brain / "resources/experiment-ledger.md",
    brain / "resources/quality-score.md",
    brain / "resources/exploration-loop.md",
    brain / "resources/session-metrics.md",
    brain / "lessons-learned.md",
]
governance_combined = "\n".join(path.read_text(encoding="utf-8") for path in governance_paths)

reasoning_paths = [
    brain / "resources/difficulty-guide.md",
    brain / "resources/reasoning-templates.md",
    brain / "resources/context-budget.md",
    brain / "resources/vendor-detection.md",
]
reasoning_combined = "\n".join(path.read_text(encoding="utf-8") for path in reasoning_paths)

assert "file-first subagent artifact protocol" in index
assert "Load only when composing an explicit delegated CLI handoff" in index
assert "resources/execution/qwen.md" not in index
assert "Current execution SSOT" in current
assert ".agents/mission/plan.json" in current
assert "Discord Agent Pool" not in current

for forbidden in [
    "../../brain/runtime/memory-protocol.md",
    "resources/examples.md",
    "stack/snippets.md",
    "stack/tech-stack.md",
    "resources/checklist.md",
    "Serena MCP",
    "Auto-loaded (provided by Antigravity)",
]:
    assert forbidden not in context, forbidden
for required in ["memory-protocol.md", "common-checklist.md", "context-budget.md", "Load only when needed"]:
    assert required in context, required

assert not (brain / "resources/execution/qwen.md").exists()
for required in [
    "Current runtime does not configure MCP-backed memory tools",
    "Optional handoff artifacts",
    "If `.agents/traces/task-board.md` exists",
    "Do not create progress/result artifacts for normal single-session work",
]:
    assert required in memory_combined, required
for forbidden in [
    "read_memory",
    "write_memory",
    "edit_memory",
    "memoryConfig.tools",
    '[READ]("task-board.md")',
    "Create `.agents/traces/progress-{agent-id}.md` with initial status",
]:
    assert forbidden not in memory_combined, forbidden

for forbidden in ["oma-", "/orchestrate"]:
    assert forbidden not in routing, forbidden
for required in [
    "plan-reviewer",
    "principle-auditor",
    ".agents/agents/harness/",
    "catalog/agents/backend-engineer",
    "catalog/agents/frontend-engineer",
    "catalog/agents/debug-investigator",
    "catalog/agents/document-delivery-lead",
    "catalog/agents/qa-reviewer",
]:
    assert required in routing, required

for forbidden in [
    "via memory tools",
    "MCP mode",
    "active memory provider",
    "Memory Protocol",
    '[EDIT]("experiment-ledger.md"',
    "MCP memory tool",
    "Auto-generated lessons",
]:
    assert forbidden not in governance_combined, forbidden
for required in [
    ".agents/traces/experiment-ledger.md",
    ".agents/traces/session-metrics.md",
    "human approval",
    "file-first",
    "lesson candidates",
]:
    assert required in governance_combined, required

for forbidden in ["Serena", "MCP memory poll", "progress-{agent-id}.md"]:
    assert forbidden not in reasoning_combined, forbidden
for required in ["rg", "targeted file inspection", "HISTORY.md", "vendor guide"]:
    assert required in reasoning_combined, required

print("PASS brain-context-hygiene-contract")
PY
