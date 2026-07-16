#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
SKILL="$PROJECT_ROOT/.agents/skills/harness/writing-plans/SKILL.md"
LIFECYCLE="$PROJECT_ROOT/.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/plan-metadata-contract-XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

python3 - <<'PY' "$SKILL"
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
metadata_line = re.compile(
    r"^> (?:(?:\*\*(?:상태|작성일):\*\*)|reviewed:|implementation_(?:started_at|completed_at|duration):)",
)
bad = [line for line in text.splitlines() if metadata_line.search(line) and "<br>" not in line]
if bad:
    raise SystemExit("metadata blockquote lines without <br>: " + repr(bad))
if "hard line break" not in text:
    raise SystemExit("missing hard line break guidance")
PY

PLAN_REL=".agentos/project/exec-plans/active/metadata-hardbreak-plan.md"
PLAN_PATH="$TMP_ROOT/$PLAN_REL"
mkdir -p "$(dirname "$PLAN_PATH")"
cat > "$PLAN_PATH" <<'MD'
# Metadata Hardbreak Fixture 구현 계획

> **상태:** 구현 계획 (실행 대기)<br>
> **작성일:** 2026-05-30<br>
> reviewed: true<br>

**사용자 결과:** Metadata renders as separate visible lines.

**진행 상태:** Fixture.
MD

python3 "$LIFECYCLE" refresh --root "$TMP_ROOT"
python3 - <<'PY' "$TMP_ROOT/.agents/mission/plan.json" "$PLAN_REL"
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan = sys.argv[2]
entries = {entry["path"]: entry for entry in data.get("active_plans", [])}
entry = entries.get(plan)
if not entry:
    raise SystemExit("fixture plan missing from active registry")
if entry.get("status") != "구현 계획 (실행 대기)":
    raise SystemExit(f"status was not parsed without <br>: {entry!r}")
if entry.get("reviewed", False) is not False or entry.get("review_evidence_status") != "missing":
    raise SystemExit(f"reviewed status did not fail closed without review evidence: {entry!r}")
if entry.get("user_outcome") != "Metadata renders as separate visible lines.":
    raise SystemExit(f"Korean user outcome was not parsed: {entry!r}")
if entry.get("progress") != "Fixture.":
    raise SystemExit(f"Korean progress was not parsed: {entry!r}")
PY

echo "PASS plan-markdown-metadata-contract"
