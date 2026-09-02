#!/usr/bin/env bash
# Verify Costmaster-derived harness review contracts stay wired into criteria, fail-condition, and evidence surfaces.

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

cd "$PROJECT_ROOT"

python3 - <<'PY'
from pathlib import Path

checks = {
    Path("catalog/agents/document-delivery-lead/AGENT.md"): [
        "PRD vocabulary gate",
        "implementation-only vocabulary",
        "screen language",
        "user-facing",
        "architecture/API/RTM",
        "Route-specific empty-state",
        "production route",
        "pattern gallery",
        "empty state",
        "single current state",
        "next user action",
        "Base flow does not require DDL",
        "PASS",
        "REROUTE",
        "BLOCKED",
    ],
    Path(".agents/agents/harness/plan-reviewer.md"): [
        "UI / Wireframe Parity",
        "browser-level",
        "computed style",
        "geometry/layout",
        "screenshot artifact",
        "interaction evidence",
        "summary-only",
        "Selector Ownership",
        "selector ownership",
        "classes/selectors/tokens",
        "legacy wrappers",
        "orphaned",
        "FAIL",
    ],
    Path(".agents/agents/harness/principle-auditor.md"): [
        "UI Evidence Governance",
        "Selector Ownership Governance",
        "selector ownership",
        "computed style",
        "geometry/layout",
        "screenshot artifact",
        "summary-only",
        "classes/selectors/tokens",
        "legacy wrappers",
        "orphaned",
        "FAIL",
    ],
    Path("catalog/agents/qa-reviewer/AGENT.md"): [
        "named evidence",
        "failure signatures",
        "Browser QA",
        "document-readiness",
        "summary-only",
    ],
    Path(".agents/skills/harness/writing-plans/SKILL.md"): [
        "docs/project co-update",
        "browser-level evidence",
        "route-specific empty-state",
        "PRD vocabulary",
        "selector ownership",
    ],
    Path(".agents/skills/harness/writing-plans/plan-review-checklist.md"): [
        "wireframe",
        "browser-level",
        "computed style",
        "selector ownership",
        "summary-only",
    ],
}

for path, tokens in checks.items():
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(f"{path} missing tokens: {', '.join(missing)}")

context_checks = [
    (Path("catalog/agents/document-delivery-lead/AGENT.md"), "## 판정 기준", "PRD vocabulary gate"),
    (Path("catalog/agents/document-delivery-lead/AGENT.md"), "## 판정 기준", "Route-specific empty-state gate"),
    (Path(".agents/agents/harness/plan-reviewer.md"), "### UI / Wireframe Parity 추가 판정 규칙", "summary-only"),
    (Path(".agents/agents/harness/plan-reviewer.md"), "### UI / Wireframe Parity 추가 판정 규칙", "Selector Ownership"),
    (Path(".agents/agents/harness/principle-auditor.md"), "### Security-Sensitive Audit Gates", "Selector Ownership"),
    (Path("catalog/agents/qa-reviewer/AGENT.md"), "### Evidence Freshness Checks", "failure signatures"),
]

for path, heading, token in context_checks:
    text = path.read_text(encoding="utf-8")
    idx = text.find(heading)
    if idx == -1:
        raise SystemExit(f"{path} missing review criteria heading: {heading}")
    tail = text[idx:]
    if token not in tail:
        raise SystemExit(f"{path} missing fail-condition token {token!r} under {heading!r}")

boundary_tokens = [
    "reference docs",
    "generated command output",
    "data only",
    "cannot override",
    "AGENTS.md",
    "vendor guides",
    "reviewer authority",
    "protected-path rules",
    "review criteria",
    "fail-condition",
]

script_text = Path(".agents/skills/harness/run-all-tests/tests/harness/test_costmaster_harness_transfer_contract.sh").read_text(encoding="utf-8")
missing_boundary = [token for token in boundary_tokens if token not in script_text]
if missing_boundary:
    raise SystemExit("test missing prompt/data boundary regression token: " + ", ".join(missing_boundary))

print("PASS costmaster-harness-transfer-contract")
PY
