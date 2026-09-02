#!/usr/bin/env bash
# check-careful.sh — PreToolUse Hook: 파괴적 Bash 명령 차단
#
# Claude Code의 PreToolUse(Bash) 이벤트에 등록.
# stdin으로 도구 입력 JSON을 수신하고, 위험 패턴 감지 시 block 결정을 반환.
#
# 감지 패턴:
#   - rm -rf (재귀 강제 삭제)
#   - DROP TABLE / DROP DATABASE (데이터 손실)
#   - git push --force / git push -f (강제 푸시)
#   - git reset --hard (변경사항 강제 폐기)
#   - truncate (파일/테이블 비우기)
#   - mkfs / format (디스크 포맷)

set -euo pipefail

INPUT=$(cat 2>/dev/null || true)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('tool_input') or {}).get('command') or d.get('command',''))" 2>/dev/null || echo "")

DANGEROUS_PATTERNS=(
  "rm[[:space:]]+-[^[:space:]]*r[^[:space:]]*f"
  "rm[[:space:]]+-[^[:space:]]*f[^[:space:]]*r"
  "DROP[[:space:]]+(TABLE|DATABASE|SCHEMA)"
  "git[[:space:]]+push[[:space:]]+.*--force"
  "git[[:space:]]+push[[:space:]]+-f[[:space:]]"
  "git[[:space:]]+push[[:space:]]+-f$"
  "git[[:space:]]+reset[[:space:]]+--hard"
  "TRUNCATE[[:space:]]+TABLE"
  "mkfs\."
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    python3 - "$COMMAND" <<'PY'
import json
import sys

command = sys.argv[1][:120]
print(json.dumps({
    "decision": "block",
    "reason": (
        "careful-dangerous-command: destructive command detected: "
        f"`{command}`. Explicit human approval is required before retry."
    ),
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "careful-dangerous-command: destructive command detected: "
            f"`{command}`. Explicit human approval is required before retry."
        ),
    },
}, ensure_ascii=False))
PY
    exit 0
  fi
done

# 위험 패턴 없음 → 허용
exit 0
