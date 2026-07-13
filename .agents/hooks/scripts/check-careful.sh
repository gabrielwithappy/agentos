#!/usr/bin/env bash
# check-careful.sh — PreToolUse Hook: 파괴적 Bash 명령 차단
#
# stdin으로 도구 입력 JSON을 수신하고, 위험 패턴 감지 시 block/deny 결정을 반환.

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
reason = (
    "careful-dangerous-command: destructive command detected: "
    f"`{command}`. Explicit human approval is required before retry."
)
print(json.dumps({
    "decision": "block",
    "reason": reason,
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    },
}, ensure_ascii=False))
PY
    exit 0
  fi
done

exit 0
