#!/usr/bin/env bash
# score-cd.sh — 하네스 전용 CD(Clarification Debt) 스코어 계산
# 메트릭: HISTORY.md의 [ESCALATION] 항목 개수
# 주의: oma-orchestrator 이벤트 기반 CD(+10/+25/+40)와 별도 스케일
# Usage: ./score-cd.sh <HISTORY.md 경로>
# Output: 정수 (ESCALATION 항목 개수)

HISTORY_FILE="${1:-HISTORY.md}"

if [[ ! -f "$HISTORY_FILE" ]]; then
  echo "0"
  exit 0
fi

count=$(grep -c "\[ESCALATION\]" "$HISTORY_FILE" 2>/dev/null) || true
count="${count:-0}"
echo "$count"
