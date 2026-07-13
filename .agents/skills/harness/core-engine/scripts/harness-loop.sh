#!/usr/bin/env bash
# harness-loop.sh — 내부 shell launcher / engine wrapper
#
# [아키텍처 역할]
# 이 스크립트는 core-engine 내부 launcher다. canonical 사용자-facing 진입점은
# .agents/skills/harness/harness-loop.sh 이며, 그 스크립트가 Python 엔진
# (harness_loop.py)을 호출한다.
#
# 역할 분리:
#   .agents/skills/harness/harness-loop.sh ← canonical CLI wrapper (자연어 진입점)
#   루트 harness-loop.sh                 ← 하위 호환 shim
#   이 파일 (core-engine/scripts/)    ← 내부 shell 루프 엔진 (Python 대안 경로)
#   harness_loop.py                   ← Python 루프 엔진 (반복 제어/에스컬레이션)
#   cli_adapters.py                   ← CLI별 fresh-process 호출 (context reset 보장)
#
# [script-first 운영 방침]
# - 권장 경로: .agents/skills/harness/harness-loop.sh → harness_loop.py
# - 이 스크립트는 Python을 사용할 수 없는 환경에서의 fallback 역할을 한다.
#
# 사용법:
#   ./.agents/skills/harness/harness-loop.sh PROMPT... [옵션]
#   ./.agents/skills/harness/harness-loop.sh --resume   # 이전 loop-state.md에서 재개
#
# Python 엔진 (권장):
#   python .agents/skills/harness/core-engine/harness_loop.py "프롬프트" --cli claude
#   python .agents/skills/harness/core-engine/harness_loop.py --resume
#
# 옵션:
#   --cli <이름>               CLI 지정 (gemini|claude|codex|auto). 기본: auto
#   --yes                      시작 확인 프롬프트 생략
#   --max-iterations <N>       최대 반복 횟수 (0 = 무제한). 기본: 30
#   --completion-promise <텍스트>  완료 신호 문구. 기본: HARNESS_COMPLETE
#   --stagnation-timeout <초>   Codex child 무진행 정체 판정 시간. 기본: 60
#   --resume                   기존 loop-state.md 파일에서 재개
#   --dry-run                  CLI를 실제로 호출하지 않고 상태 파일만 출력
#   -h, --help                 도움말 표시
#
# 완료 신호:
#   에이전트는 `<promise>HARNESS_COMPLETE</promise>` 직전에
#   검증 명령/결과, 최종 산출물 경로, 마지막 checkpoint 요약을 함께 출력해야 한다.
#
# 루프 상태 파일: .agents/traces/harness/loop-state.md

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "${SCRIPT_DIR}/../..")"
STATE_FILE="${PROJECT_ROOT}/.agents/traces/harness/loop-state.md"
CD_SCRIPT="${SCRIPT_DIR}/score-cd.sh"
HISTORY_FILE="${PROJECT_ROOT}/HISTORY.md"
LOOP_CONFIG_FILE="${PROJECT_ROOT}/.harness-loop.json"
CANONICAL_WRAPPER="${PROJECT_ROOT}/.agents/skills/harness/harness-loop.sh"

case "${1:-}" in
  status|inspect|last|watch|respond)
    exec "$CANONICAL_WRAPPER" "$@"
    ;;
esac

# ──────────────────────────────────────────────────────────────────────────────
# 기본값
# ──────────────────────────────────────────────────────────────────────────────
CLI="auto"
MAX_ITERATIONS=30
COMPLETION_PROMISE="HARNESS_COMPLETE"
RESUME=false
DRY_RUN=false
ASSUME_YES=false
STAGNATION_TIMEOUT=60
PROMPT_PARTS=()

# ──────────────────────────────────────────────────────────────────────────────
# 도움말
# ──────────────────────────────────────────────────────────────────────────────
print_help() {
  cat <<'EOF'
harness-loop.sh — 플랫폼 독립 에이전트 루프 실행기

사용법:
  .agents/skills/harness/core-engine/scripts/harness-loop.sh PROMPT [옵션]
  .agents/skills/harness/core-engine/scripts/harness-loop.sh --resume

[권장] 사용자-facing 진입점:
  ./.agents/skills/harness/harness-loop.sh "자연어 프롬프트"

옵션:
  --cli <이름>                  gemini | claude | codex | auto (기본: auto)
  --yes                         시작 확인 프롬프트 생략
  --max-iterations <N>          최대 반복 횟수 (0 = 무제한). 기본: 30
  --completion-promise <텍스트>  완료 신호 문구. 기본: HARNESS_COMPLETE
  --stagnation-timeout <초>      Codex child 무진행 정체 판정 시간. 기본: 60
  --resume                      기존 loop-state.md에서 재개
  --dry-run                     실제 CLI 호출 없이 상태 파일만 확인
  -h, --help                    이 도움말 표시

	예시:
	  ./.agents/skills/harness/harness-loop.sh "에이전트 하네스를 구축하라" --cli gemini
	  ./.agents/skills/harness/harness-loop.sh "하네스 구축" --max-iterations 20
	  ./.agents/skills/harness/harness-loop.sh --resume --cli claude

	완료 계약:
	  `<promise>HARNESS_COMPLETE</promise>` 단독 출력은 충분하지 않다.
	  completion 직전에는 검증 명령/결과, 최종 산출물 경로, 마지막 checkpoint 요약을 포함해야 한다.
EOF
}

# ──────────────────────────────────────────────────────────────────────────────
# 인자 파싱
# ──────────────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --resume)      RESUME=true;              shift ;;
    --dry-run)     DRY_RUN=true;             shift ;;
    --yes)         ASSUME_YES=true;          shift ;;
    -h|--help)     print_help;               exit 0 ;;
    --cli)         CLI="$2";                 shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2";   shift 2 ;;
    --completion-promise) COMPLETION_PROMISE="$2"; shift 2 ;;
    --stagnation-timeout) STAGNATION_TIMEOUT="$2"; shift 2 ;;
    *) PROMPT_PARTS+=("$1");                 shift ;;
  esac
done

PROMPT="${PROMPT_PARTS[*]:-}"

# ──────────────────────────────────────────────────────────────────────────────
# CLI 자동 감지
# ──────────────────────────────────────────────────────────────────────────────
detect_cli() {
  # PATH에서 CLI 탐색
  for cli_name in gemini claude codex; do
    if command -v "$cli_name" &>/dev/null; then
      echo "$cli_name"; return
    fi
  done
  echo ""
}

read_default_cli_config() {
  if [[ ! -f "$LOOP_CONFIG_FILE" ]]; then
    echo ""
    return
  fi

  grep -E '"default_cli"[[:space:]]*:' "$LOOP_CONFIG_FILE" \
    | head -1 \
    | sed -E 's/.*"default_cli"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' \
    | grep -E '^(claude|codex|gemini)$' || true
}

# ──────────────────────────────────────────────────────────────────────────────
# CLI 실행 래퍼 — 프롬프트를 파일로 받아 CLI를 호출하고 stdout을 반환
# ──────────────────────────────────────────────────────────────────────────────
invoke_cli() {
  local resolved_cli="$1"
  local prompt_file="$2"

  case "$resolved_cli" in
    gemini)
      # gemini -p "..." 또는 stdin 파이프
      if gemini --help 2>&1 | grep -qE '\-p|--prompt'; then
        gemini -p "$(cat "$prompt_file")"
      else
        cat "$prompt_file" | gemini
      fi
      ;;
    claude)
      # claude --dangerously-skip-permissions -p "..."
      if claude --help 2>&1 | grep -qE '\-p|--print'; then
        claude --dangerously-skip-permissions -p "$(cat "$prompt_file")"
      else
        cat "$prompt_file" | claude --dangerously-skip-permissions
      fi
      ;;
    codex)
      # Codex CLI can return non-zero even after producing completion output.
      # The loop engine consumes stdout for completion detection, so do not
      # hard-fail the wrapper on the exit code alone.
      cat "$prompt_file" | codex exec -s danger-full-access -c 'approval_policy="never"' - || true
      ;;
    *)
      echo "❌ 알 수 없는 CLI: $resolved_cli" >&2
      return 1
      ;;
  esac
}

# ──────────────────────────────────────────────────────────────────────────────
# 상태 파일 읽기 헬퍼
# ──────────────────────────────────────────────────────────────────────────────
read_frontmatter_field() {
  local field="$1"
  local file="$2"
  sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$file" \
    | grep "^${field}:" \
    | sed "s/${field}:[[:space:]]*//" \
    | sed 's/^"\(.*\)"$/\1/'
}

read_prompt_body() {
  local file="$1"
  awk '/^---$/{i++; next} i>=2' "$file"
}

# ──────────────────────────────────────────────────────────────────────────────
# 상태 파일 초기화
# ──────────────────────────────────────────────────────────────────────────────
init_state_file() {
  local prompt="$1"
  mkdir -p "$(dirname "$STATE_FILE")"
  cat > "$STATE_FILE" <<EOF
---
active: true
execution_locked: false
iteration: 1
max_iterations: ${MAX_ITERATIONS}
completion_promise: "${COMPLETION_PROMISE}"
cli: ${CLI}
harness_version: "1.0"
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
last_run: null
---

${prompt}
EOF
}

# ──────────────────────────────────────────────────────────────────────────────
# 상태 파일 업데이트 (iteration 증가)
# ──────────────────────────────────────────────────────────────────────────────
update_state_iteration() {
  local next_iter="$1"
  local now; now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local tmp="${STATE_FILE}.tmp.$$"
  sed \
    -e "s/^iteration: .*/iteration: ${next_iter}/" \
    -e "s/^last_run: .*/last_run: \"${now}\"/" \
    "$STATE_FILE" > "$tmp"
  mv "$tmp" "$STATE_FILE"
}

deactivate_state_file() {
  [[ -f "$STATE_FILE" ]] || return 0
  local tmp="${STATE_FILE}.tmp.$$"
  sed -e "s/^active: .*/active: false/" "$STATE_FILE" > "$tmp"
  mv "$tmp" "$STATE_FILE"
}

# ──────────────────────────────────────────────────────────────────────────────
# 완료 신호 감지
# ──────────────────────────────────────────────────────────────────────────────
detect_promise() {
  local output="$1"
  local promise="$2"
  # <promise>...</promise> 태그에서 텍스트 추출
  local found
  found=$(echo "$output" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")
  [[ "$found" == "$promise" ]]
}

confirm_cli_execution() {
  local selected_cli="$1"
  local answer
  printf "랄프 루프를 '%s' agent로 실행합니다. 계속할까요? [y/N]: " "$selected_cli"
  if ! read -r answer; then
    return 1
  fi
  answer="$(echo "$answer" | tr '[:upper:]' '[:lower:]')"
  [[ "$answer" == "y" || "$answer" == "yes" ]]
}

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

# ── 검증: 재개 또는 새 루프 ──
if [[ "$RESUME" == "true" ]]; then
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "❌ 재개할 상태 파일이 없습니다: $STATE_FILE" >&2
    echo "   --resume 없이 새 루프를 시작하세요." >&2
    exit 1
  fi
  echo "🔄 기존 루프 재개: $STATE_FILE"
  # 상태에서 값 로드
  ITERATION=$(read_frontmatter_field "iteration" "$STATE_FILE")
  MAX_ITERATIONS=$(read_frontmatter_field "max_iterations" "$STATE_FILE")
  COMPLETION_PROMISE=$(read_frontmatter_field "completion_promise" "$STATE_FILE")
  STORED_CLI=$(read_frontmatter_field "cli" "$STATE_FILE")
  [[ "$CLI" == "auto" && -n "$STORED_CLI" ]] && CLI="$STORED_CLI"
  PROMPT=$(read_prompt_body "$STATE_FILE")
else
  if [[ -z "$PROMPT" ]]; then
    echo "❌ 프롬프트가 없습니다." >&2
    echo "" >&2
    print_help >&2
    exit 1
  fi
  ITERATION=1
  init_state_file "$PROMPT"
  echo "🆕 새 루프 시작: $STATE_FILE"
fi

# ── CLI 결정 ──
if [[ "$CLI" == "auto" ]]; then
  CONFIGURED_CLI="$(read_default_cli_config)"
  if [[ -n "$CONFIGURED_CLI" ]]; then
    CLI="$CONFIGURED_CLI"
    echo "🧭 설정 파일 기본 CLI 사용: $CLI"
  fi
fi

if [[ "$CLI" == "auto" ]]; then
  CLI=$(detect_cli)
  if [[ -z "$CLI" ]]; then
    echo "❌ 사용 가능한 CLI를 찾을 수 없습니다." >&2
    echo "   gemini, claude, codex 중 하나를 설치하거나 --cli 옵션으로 지정하세요." >&2
    exit 1
  fi
  echo "🔍 자동 감지된 CLI: $CLI"
fi

if [[ "$DRY_RUN" != "true" && "$ASSUME_YES" != "true" ]]; then
  if ! confirm_cli_execution "$CLI"; then
    echo "🛑 사용자 확인으로 랄프 루프 실행을 중단했습니다."
    exit 1
  fi
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Harness Loop 시작"
echo "  CLI: $CLI"
echo "  완료 신호: <promise>$COMPLETION_PROMISE</promise>"
echo "  Codex stagnation timeout: ${STAGNATION_TIMEOUT}s"
echo "  최대 반복: $([ "$MAX_ITERATIONS" -gt 0 ] && echo "$MAX_ITERATIONS" || echo "무제한")"
echo "  상태 파일: $STATE_FILE"
echo "  (중지하려면 Ctrl+C)"
echo "═══════════════════════════════════════════════════════"
echo ""

PROMPT=$(read_prompt_body "$STATE_FILE")

# ── 루프 ──
while true; do
  echo ""
  echo "────────────────────────────────────────────────────────"
  echo "🔄 Iteration $ITERATION / $([ "$MAX_ITERATIONS" -gt 0 ] && echo "$MAX_ITERATIONS" || echo "∞")"
  echo "────────────────────────────────────────────────────────"

  # CD 스코어 확인
  if [[ -x "$CD_SCRIPT" && -f "$HISTORY_FILE" ]]; then
    CD_SCORE=$(bash "$CD_SCRIPT" "$HISTORY_FILE" 2>/dev/null | head -1 | tr -d '[:space:]' || echo "0")
    CD_SCORE="${CD_SCORE:-0}"
    # 숫자인지 검증
    if [[ "$CD_SCORE" =~ ^[0-9]+$ ]]; then
      CD_LIMIT=30
      echo "📊 CD 스코어: $CD_SCORE / $CD_LIMIT"
      if [[ "$CD_SCORE" -ge "$CD_LIMIT" ]]; then
        echo "🛑 CD 스코어 한계 도달 (${CD_SCORE} >= ${CD_LIMIT}). 루프 중지."
        deactivate_state_file
        exit 1
      fi
    fi
  fi

  # HISTORY.md 라인 수 감지 (진화 트리거 4)
  if [[ -f "$HISTORY_FILE" ]]; then
    HIST_LINES=$(wc -l < "$HISTORY_FILE" || echo "0")
    HIST_LIMIT=500
    echo "📜 HISTORY 라인: $HIST_LINES / $HIST_LIMIT"
    if [[ "$HIST_LINES" -ge "$HIST_LIMIT" ]]; then
    echo "⚡ [TRIGGER 4] 지식 압축 기준 도달 ($HIST_LINES >= $HIST_LIMIT)"
    echo "   run: python3 .agents/skills/harness/core-engine/scripts/compact_history.py --history-path HISTORY.md --archive-path docs/project/reference/history/2026-04-history-archive.md --keep-recent-lines 200"
    echo "   expected: PASS compact-history ... and HISTORY.md keeps only the recent operational window."
    fi
  fi

  # 최대 반복 확인
  if [[ "$MAX_ITERATIONS" -gt 0 && "$ITERATION" -gt "$MAX_ITERATIONS" ]]; then
    echo "🛑 최대 반복 횟수($MAX_ITERATIONS)에 도달. 루프 중지."
    deactivate_state_file
    exit 1
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    deactivate_state_file
    echo "[DRY-RUN] CLI 호출 건너뜀"
    echo "프롬프트:"
    echo "$PROMPT"
    exit 0
  fi

  # 프롬프트를 임시 파일에 저장
  PROMPT_TMP=$(mktemp)
  # 재시작 컨텍스트 주입
  cat > "$PROMPT_TMP" <<PEOF
🔄 Harness Loop iteration ${ITERATION} | 완료 시: <promise>${COMPLETION_PROMISE}</promise> 출력

${PROMPT}
PEOF

  # CLI 실행 및 출력 캡처 (터미널에도 동시 출력)
  OUTPUT_TMP=$(mktemp)
  set +e
  invoke_cli "$CLI" "$PROMPT_TMP" | tee "$OUTPUT_TMP"
  CLI_EXIT=$?
  set -e
  rm -f "$PROMPT_TMP"

  AGENT_OUTPUT=$(cat "$OUTPUT_TMP")
  rm -f "$OUTPUT_TMP"

  if [[ $CLI_EXIT -ne 0 ]]; then
    echo "⚠️  CLI 오류 (exit $CLI_EXIT). 루프 계속..."
  fi

  # 완료 감지
  if detect_promise "$AGENT_OUTPUT" "$COMPLETION_PROMISE"; then
    echo ""
    echo "✅ 완료 신호 감지: <promise>${COMPLETION_PROMISE}</promise>"
    deactivate_state_file
    rm -f "$STATE_FILE"
    echo "🎉 Harness Loop 정상 완료 (총 $ITERATION 회)"
    exit 0
  fi

  # 다음 반복 준비
  NEXT_ITERATION=$((ITERATION + 1))
  update_state_iteration "$NEXT_ITERATION"
  ITERATION=$NEXT_ITERATION
  PROMPT=$(read_prompt_body "$STATE_FILE")
done
