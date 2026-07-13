#!/usr/bin/env bash
# harness-loop.sh — canonical harness entrypoint
#
# 사용자-facing 하네스 루프 진입점의 canonical 위치는 이제 이 파일이다.
# 실제 반복 제어/에스컬레이션은 core-engine Python 엔진에 위임한다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON_ENGINE="${PROJECT_ROOT}/.agents/skills/harness/core-engine/harness_loop.py"
STATE_FILE="${HARNESS_LOOP_STATE_FILE:-${PROJECT_ROOT}/.agents/traces/harness/loop-state.md}"
EVENTS_FILE="${HARNESS_LOOP_EVENTS_FILE:-${PROJECT_ROOT}/.agents/traces/harness/events.jsonl}"
PYTHON_CMD="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"

if [[ ! -f "$PYTHON_ENGINE" ]]; then
  echo "❌ 하네스 엔진을 찾을 수 없습니다: $PYTHON_ENGINE" >&2
  exit 1
fi

if [[ -z "$PYTHON_CMD" ]]; then
  echo "❌ Python 3가 설치되어 있지 않습니다." >&2
  exit 1
fi

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    cat <<'EOF'
harness-loop.sh — canonical harness loop entrypoint

사용법:
  ./.agents/skills/harness/harness-loop.sh "자연어 프롬프트"
  ./.agents/skills/harness/harness-loop.sh "구현 요구사항을 작성하세요" --cli codex
  ./.agents/skills/harness/harness-loop.sh --resume

옵션:
  --cli <이름>                  gemini | claude | codex | auto (기본: auto)
  --yes                         시작 확인 프롬프트 생략
  --max-iterations <N>          최대 반복 횟수 (0 = 무제한). 기본: 30
  --completion-promise <텍스트>  완료 신호 문구. 기본: HARNESS_COMPLETE
  --stagnation-timeout <초>      Codex child 무진행 정체 판정 시간. 기본: 60
  --resume                      기존 loop-state.md 에서 재개
  --dry-run                     실제 CLI 호출 없이 loop-state.md 만 초기화
  -h, --help                    이 도움말 표시

내부 구조:
  canonical 진입점       → .agents/skills/harness/harness-loop.sh
  반복 제어/에스컬레이션 → .agents/skills/harness/core-engine/harness_loop.py
  CLI 어댑터            → .agents/skills/harness/core-engine/cli_adapters.py
  루프 상태 파일         → .agents/traces/harness/loop-state.md
  이벤트 로그           → .agents/traces/harness/events.jsonl

관측 명령:
  ./.agents/skills/harness/harness-loop.sh status
  ./.agents/skills/harness/harness-loop.sh watch [--once]
  ./.agents/skills/harness/harness-loop.sh respond "새 방향"
EOF
    exit 0
  fi
done

read_state_field() {
  local field="$1"
  if [[ ! -f "$STATE_FILE" ]]; then
    return 0
  fi
  "$PYTHON_CMD" - "$PYTHON_ENGINE" "$STATE_FILE" "$field" <<'PY'
from pathlib import Path
import sys

engine_path = Path(sys.argv[1])
state_path = Path(sys.argv[2])
field = sys.argv[3]
sys.path.insert(0, str(engine_path.parent))
from loop_state import LoopState

state = LoopState.from_file(state_path)
value = getattr(state, field, "")
if isinstance(value, bool):
    print(str(value).lower())
else:
    print(value)
PY
}

read_prompt_body() {
  if [[ ! -f "$STATE_FILE" ]]; then
    return 0
  fi
  awk '/^---$/{i++; next} i>=2' "$STATE_FILE"
}

print_status() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "status: inactive"
    echo "state_file: missing"
    return 0
  fi
  echo "status: $(read_state_field active)"
  echo "iteration: $(read_state_field iteration)/$(read_state_field max_iterations)"
  echo "cli: $(read_state_field cli)"
  echo "loop_id: $(read_state_field loop_id)"
  echo "plan_path: $(read_state_field plan_path)"
  echo "started_at: $(read_state_field started_at)"
  echo "last_run: $(read_state_field last_run)"
  echo "last_checkpoint_at: $(read_state_field last_checkpoint_at)"
  echo "last_event: $(read_state_field last_event)"
  echo "outcome_code: $(read_state_field outcome_code)"
  echo "failure_class: $(read_state_field failure_class)"
  echo "status_hint: $(read_state_field status_hint)"
  echo "current_phase: $(read_state_field current_phase)"
  echo "current_task: $(read_state_field current_task)"
  echo "current_step: $(read_state_field current_step)"
  echo "pending_escalation_id: $(read_state_field pending_escalation_id)"
  echo "pending_escalation_summary: $(read_state_field pending_escalation_summary)"
}

print_inspect() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "inspect: no state file"
    return 0
  fi
  echo "cli: $(read_state_field cli)"
  echo "loop_id: $(read_state_field loop_id)"
  echo "plan_path: $(read_state_field plan_path)"
  echo "completion_promise: $(read_state_field completion_promise)"
  echo "max_iterations: $(read_state_field max_iterations)"
  echo "prompt_summary: $(read_state_field prompt_summary)"
  echo "result_summary: $(read_state_field result_summary)"
  echo "outcome_code: $(read_state_field outcome_code)"
  echo "failure_class: $(read_state_field failure_class)"
  echo "status_hint: $(read_state_field status_hint)"
  echo "prompt:"
  read_prompt_body
}

print_last() {
  if [[ -f "$EVENTS_FILE" ]]; then
    echo "last_event:"
    tail -n 1 "$EVENTS_FILE"
  else
    echo "last_event: none"
  fi
  if [[ -f "$STATE_FILE" ]]; then
    echo "state_snapshot:"
    echo "  loop_id=$(read_state_field loop_id)"
    echo "  plan_path=$(read_state_field plan_path)"
    echo "  last_event=$(read_state_field last_event)"
    echo "  outcome_code=$(read_state_field outcome_code)"
    echo "  failure_class=$(read_state_field failure_class)"
    echo "  status_hint=$(read_state_field status_hint)"
    echo "  result_summary=$(read_state_field result_summary)"
    echo "  blocked_reason=$(read_state_field blocked_reason)"
    echo "  stop_reason=$(read_state_field stop_reason)"
  fi
}

watch_loop() {
  local once="${1:-}"
  if [[ "$once" == "--once" ]]; then
    print_status
    return 0
  fi
  while true; do
    clear
    print_status
    sleep 2
  done
}

respond_override() {
  local response="${1:-}"
  local py_cmd
  if [[ -z "$response" ]]; then
    echo "respond: response text required" >&2
    return 1
  fi
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "respond: state file missing" >&2
    return 1
  fi
  HARNESS_RESPOND_ENGINE="$PYTHON_ENGINE" \
  HARNESS_RESPOND_STATE_FILE="$STATE_FILE" \
  HARNESS_RESPOND_TEXT="$response" \
  "$PYTHON_CMD" - <<'PY'
from pathlib import Path
import os
import sys

engine = Path(os.environ["HARNESS_RESPOND_ENGINE"])
state_file = Path(os.environ["HARNESS_RESPOND_STATE_FILE"])
response = os.environ["HARNESS_RESPOND_TEXT"]
sys.path.insert(0, str(engine.parent))
from loop_state import LoopState

state = LoopState.from_file(state_file)
pending_id = state.pending_escalation_id
if not state.loop_id or not pending_id:
    print("respond: no pending escalation", file=sys.stderr)
    sys.exit(1)

state.pending_override_response = response.strip()
state.to_file(state_file)
print(f"respond: recorded for {pending_id}")
PY
}

case "${1:-}" in
  status)
    print_status
    exit 0
    ;;
  inspect)
    print_inspect
    exit 0
    ;;
  last)
    print_last
    exit 0
    ;;
  watch)
    shift
    watch_loop "${1:-}"
    exit 0
    ;;
  respond)
    shift
    respond_override "$*"
    exit 0
    ;;
esac

cd "$PROJECT_ROOT"
exec "$PYTHON_CMD" "$PYTHON_ENGINE" "$@"
