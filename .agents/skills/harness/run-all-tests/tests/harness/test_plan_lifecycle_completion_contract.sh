#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
LIFECYCLE="$PROJECT_ROOT/.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/plan-lifecycle-completion-XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

PLAN_REL=".agentos/project/exec-plans/active/completed-active-plan.md"
PLAN_PATH="$TMP_ROOT/$PLAN_REL"
mkdir -p "$(dirname "$PLAN_PATH")" "$TMP_ROOT/.agentos/project/exec-plans/archive"

cat > "$PLAN_PATH" <<'MD'
# 완료 Active Fixture 구현 계획

> **상태:** 완료<br>
> **작성일:** 2026-05-20<br>
> reviewed: true<br>
> implementation_started_at: 2026-05-20T00:00:00Z<br>
> implementation_completed_at: 2026-05-20T00:01:00Z<br>
> implementation_duration: 1m 0s<br>

**목표:** 완료된 계획이 active에 남을 수 있음을 증명한다.

**사용자 결과:** 사용자는 archive 전에 완료된 구현 증거를 읽을 수 있다.

**진행 상태:** 완료되었고 사용자 archive 결정을 기다린다.

**아키텍처:** Fixture only.

**기술 스택:** Markdown, Python.

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 / 사용자가 archive할 때까지 active |
| 완료됨 | Fixture implementation complete |
| 현재 위치 | User reviews completion |
| 다음 단계 | User may command archive |
| 완료 신호 | PASS active-completed-plans-remain-active |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | Completed active visibility |
| 누구를 위한 것인가? | Users |
| 일상 사용에서 무엇이 달라지는가? | Archive is a separate decision |
| 무엇은 바뀌지 않는가? | Reviews and verification |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Complete | Plan remains visible | lifecycle | PASS |

## 구현 결과

The fixture completed successfully and remains active.

## 사용 방법

Read the active plan, then archive only when ready.

## 완료 증거

PASS active-completed-plans-remain-active

## 아카이브 결정

This completed plan stays active until the user explicitly commands archive.
MD

python3 "$LIFECYCLE" refresh --root "$TMP_ROOT"

python3 - <<'PY' "$TMP_ROOT/.agents/mission/plan.json" "$PLAN_REL"
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan = sys.argv[2]
active = {entry["path"]: entry for entry in data.get("active_plans", [])}
archived = {entry["path"]: entry for entry in data.get("archived_plans", [])}
if plan not in active:
    raise SystemExit("completed active plan missing from active_plans")
if plan in archived:
    raise SystemExit("completed active plan incorrectly archived by status")
PY
echo "PASS active-completed-plans-remain-active"

python3 "$LIFECYCLE" archive "$PLAN_REL" --status 완료 --root "$TMP_ROOT"

python3 - <<'PY' "$TMP_ROOT/.agents/mission/plan.json"
import json
from pathlib import Path

data = json.loads(Path(__import__("sys").argv[1]).read_text(encoding="utf-8"))
archived = {entry["path"]: entry for entry in data.get("archived_plans", [])}
if ".agentos/project/exec-plans/archive/completed-active-plan.md" not in archived:
    raise SystemExit("explicit archive did not move plan into archived_plans")
PY
test -f "$TMP_ROOT/.agentos/project/exec-plans/archive/completed-active-plan.md"
test ! -e "$PLAN_PATH"
echo "PASS archive-requires-explicit-command"
echo "PASS plan-completion-lifecycle-contract"
