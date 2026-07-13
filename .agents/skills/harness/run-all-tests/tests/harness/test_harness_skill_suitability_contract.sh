#!/usr/bin/env bash
# Verify harness skill suitability inventory coverage and pruning boundaries.

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

python3 - <<'PY'
from pathlib import Path

root = Path(".agents/skills/harness")
inventory = Path("docs/project/reference/decisions/harness-skill-suitability-inventory.md")
routing = Path(".agents/skills/harness/brain/resources/skill-routing.md")

assert inventory.exists(), "missing skill suitability inventory"
assert routing.exists(), "missing skill routing reference"

inventory_text = inventory.read_text(encoding="utf-8")
routing_text = routing.read_text(encoding="utf-8")

skill_dirs = sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
missing = [name for name in skill_dirs if f"`{name}`" not in inventory_text]
assert not missing, "unclassified harness skill directories: " + ", ".join(missing)

removed_skills = ["commit", "skill-creator", "unfreeze"]
assert "## Removed Skills" in inventory_text, "missing removed skills section"
for name in removed_skills:
    assert not (root / name).exists(), f"removed skill directory reappeared: {name}"
    assert f"| `{name}` |" in inventory_text, f"missing removed skill evidence: {name}"
    assert f".agents/skills/harness/{name}/SKILL.md" not in inventory_text, f"removed skill still has live SKILL evidence: {name}"

allowed_non_skill_dirs = {"core-engine"}
non_skill_dirs = sorted(p.name for p in root.iterdir() if p.is_dir() and not (p / "SKILL.md").exists())
unexpected = [name for name in non_skill_dirs if name not in allowed_non_skill_dirs]
assert not unexpected, "unexpected non-skill harness directories: " + ", ".join(unexpected)
for name in allowed_non_skill_dirs:
    assert f"`{name}`" in inventory_text, f"allowlisted non-skill missing from inventory: {name}"

hidden_dirs = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name.startswith("."))
assert not hidden_dirs, "hidden harness skill directories are not allowed: " + ", ".join(hidden_dirs)

required_tokens = [
    "Suitability Criteria",
    "Classification",
    "required",
    "agent-support",
    "operator-tooling",
    "safety-governance",
    "candidate-deprecate",
    "No automatic deletion",
    "zero-reference evidence",
    "No new skill runtime",
    "no MCP automatic enable",
]
combined = inventory_text + "\n" + routing_text
missing_tokens = [token for token in required_tokens if token not in combined]
assert not missing_tokens, "missing suitability boundary tokens: " + ", ".join(missing_tokens)

for forbidden in [
    "delete-now",
    "auto-delete",
    "automatic skill deletion behavior enabled",
    "automatic pruning daemon enabled",
    "new skill runtime enabled",
    "plugin runtime enabled",
    "provider detector enabled",
    "MCP automatic enable enabled",
]:
    assert forbidden not in combined, f"runtime creep or deletion marker found: {forbidden}"

if "Current candidate-deprecate list: none." not in inventory_text:
    assert "zero-reference evidence" in inventory_text, "candidate deprecation requires zero-reference evidence"
    assert "human approval" in inventory_text, "candidate deprecation requires human approval"

print("PASS harness-skill-suitability-contract")
PY
