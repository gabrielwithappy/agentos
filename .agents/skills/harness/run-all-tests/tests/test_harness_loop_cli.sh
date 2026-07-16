#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CANONICAL="$PROJECT_ROOT/.agents/skills/harness/harness-loop.sh"
FALLBACK="$PROJECT_ROOT/.agents/skills/harness/core-engine/scripts/harness-loop.sh"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

STATE_FILE="$TMP_DIR/loop-state.md"
EVENTS_FILE="$TMP_DIR/events.jsonl"

cat > "$STATE_FILE" <<'EOF'
---
active: true
execution_locked: false
iteration: 3
max_iterations: 30
completion_promise: "HARNESS_COMPLETE"
cli: codex
harness_version: "1.0"
loop_id: "loop-20260409-abc123"
started_at: "2026-04-09T05:35:11Z"
last_run: "2026-04-09T05:37:55Z"
last_checkpoint_at: "2026-04-09T05:37:55Z"
last_event: |
  blocked
current_phase: |
  Phase 4-2
current_task: |
  Runtime verification
current_step: |
  tmux restart
plan_path: |
  .agentos/project/exec-plans/2026-04-09-harness-loop-observability.md
prompt_summary: |
  trace observability plan
result_summary: |
  plan review PASS
  implementation complete
outcome_code: |
  blocked
failure_class: |
  escalation_pending
status_hint: |
  operator response required
blocked_reason: |
  tmux access denied
stop_reason: |
  blocked:tmux
pending_escalation_id: |
  esc-001
pending_escalation_summary: |
  need direction
pending_override_response: |
---

.agentos/project/exec-plans/2026-04-09-harness-loop-observability.md 계획을 실행하라.
EOF

cat > "$EVENTS_FILE" <<'EOF'
{"ts":"2026-04-09T05:35:11Z","type":"loop_started","iteration":1,"summary":"CLI=codex","loop_id":"loop-20260409-abc123","plan_path":".agentos/project/exec-plans/2026-04-09-harness-loop-observability.md"}
{"ts":"2026-04-09T05:37:55Z","type":"blocked","iteration":3,"summary":"tmux access denied","loop_id":"loop-20260409-abc123"}
EOF

run_with_env() {
  HARNESS_LOOP_STATE_FILE="$STATE_FILE" \
  HARNESS_LOOP_EVENTS_FILE="$EVENTS_FILE" \
  "$@"
}

case "${1:-all}" in
  trigger4)
    output="$(python3 - <<'PY' "$FALLBACK"
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding='utf-8')
print(text)
PY
)"
    grep -q 'compact_history.py' <<<"$output"
    grep -q '2026-04-history-archive.md' <<<"$output"
    grep -q -- '--keep-recent-lines 200' <<<"$output"
    ;;
  status)
    output="$(run_with_env "$CANONICAL" status)"
    grep -q 'status: true' <<<"$output"
    grep -q 'loop_id: loop-20260409-abc123' <<<"$output"
    grep -q 'iteration: 3/30' <<<"$output"
    grep -q 'current_task: Runtime verification' <<<"$output"
    grep -q 'outcome_code: blocked' <<<"$output"
    grep -q 'failure_class: escalation_pending' <<<"$output"
    grep -q 'status_hint: operator response required' <<<"$output"
    grep -q 'pending_escalation_id: esc-001' <<<"$output"
    grep -q 'pending_escalation_summary: need direction' <<<"$output"
    ;;
  watch)
    output="$(run_with_env "$CANONICAL" watch --once)"
    grep -q 'status: true' <<<"$output"
    grep -q 'pending_escalation_id: esc-001' <<<"$output"
    grep -q 'outcome_code: blocked' <<<"$output"
    fallback_output="$(run_with_env "$FALLBACK" watch --once)"
    grep -q 'status: true' <<<"$fallback_output"
    ;;
  runtime-diagnostics)
    status_output="$(run_with_env "$CANONICAL" status)"
    inspect_output="$(run_with_env "$CANONICAL" inspect)"
    last_output="$(run_with_env "$CANONICAL" last)"
    watch_output="$(run_with_env "$CANONICAL" watch --once)"
    for output in "$status_output" "$inspect_output" "$last_output" "$watch_output"; do
      grep -q 'outcome_code' <<<"$output"
      grep -q 'failure_class' <<<"$output"
      grep -q 'status_hint' <<<"$output"
      grep -q 'blocked' <<<"$output"
      grep -q 'escalation_pending' <<<"$output"
    done
    echo "PASS runtime-diagnostic-status-surface"
    ;;
  respond)
    output="$(run_with_env "$CANONICAL" respond "switch direction")"
    grep -q 'respond: recorded for esc-001' <<<"$output"
    grep -q 'pending_override_response: |' "$STATE_FILE"
    grep -q '^  switch direction$' "$STATE_FILE"
    ;;
  canonical-wrapper-stagnation-timeout)
    output="$("$CANONICAL" --help)"
    grep -q -- '--stagnation-timeout <초>' <<<"$output"
    grep -q 'Codex child 무진행 정체 판정 시간. 기본: 60' <<<"$output"
    ;;
  fallback-wrapper-stagnation-timeout)
    output="$("$FALLBACK" --help)"
    grep -q -- '--stagnation-timeout <초>' <<<"$output"
    grep -q 'Codex child 무진행 정체 판정 시간. 기본: 60' <<<"$output"
    grep -q 'STAGNATION_TIMEOUT' "$FALLBACK"
    ;;
  all)
    "$0" status
    "$0" watch
    "$0" respond
    "$0" trigger4
    "$0" runtime-diagnostics
    "$0" canonical-wrapper-stagnation-timeout
    "$0" fallback-wrapper-stagnation-timeout
    ;;
  *)
    echo "usage: $0 {status|watch|respond|trigger4|runtime-diagnostics|canonical-wrapper-stagnation-timeout|fallback-wrapper-stagnation-timeout|all}" >&2
    exit 1
    ;;
esac
