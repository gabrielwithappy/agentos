#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

python3 - <<'PY'
import re
from pathlib import Path

roots = [Path(".agents/skills/harness"), Path(".agents/agents/harness")]
this_contract = Path(".agents/skills/harness/run-all-tests/tests/harness/test_harness_portability_contract.sh")
blocked_patterns = [
    re.compile(r"Current Plan — Discord Agent Pool"),
    re.compile(r"src/discord/handler\.py"),
    re.compile(r"~/.config/claude"),
    re.compile(r"Discord 봇 4개 생성"),
    re.compile(r"/(home|Users)/[^\s`]+"),
    re.compile(r"agent-starter|prj-agent|commit-commands|our\.first\.fluke|First Fluke"),
    re.compile(r"(BOT_TOKEN|API[_-]?KEY|SECRET|PASSWORD)\s*[=:]"),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
]

allowed_fragments = [
    ".agents/skills/harness/run-all-tests/tests/test_cli_adapters.py:/tmp/codex-last-message.txt",
    ".agents/skills/harness/run-all-tests/tests/test_cli_adapters.py:/tmp/codex-trace.log",
    ".agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh:/tmp/nonexistent_",
    ".agents/skills/harness/harness-loop/SKILL.md:/tmp/harness-loop.out",
    ".agents/skills/harness/skill-creator/SKILL.md:/tmp/",
    ".agents/skills/harness/qa/resources/error-playbook.md:/tmp/progress-",
]

violations = []
for root in roots:
    for path in root.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path == this_contract:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in blocked_patterns):
                entry = f"{path}:{lineno}:{line}"
                if not any(fragment in entry for fragment in allowed_fragments):
                    violations.append(entry)

if violations:
    print("\n".join(violations))
    raise SystemExit(1)
PY

echo "PASS harness-portability-contract"
