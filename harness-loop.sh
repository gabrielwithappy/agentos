#!/usr/bin/env bash
# harness-loop.sh — compatibility shim
#
# canonical 진입점은 .agents/skills/harness/harness-loop.sh 로 이동했다.
# 기존 루트 경로는 하위 호환을 위해 내부 canonical 경로로 위임한다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="${SCRIPT_DIR}/.agents/skills/harness/harness-loop.sh"

if [[ ! -f "$CANONICAL_SCRIPT" ]]; then
  echo "❌ canonical harness loop script를 찾을 수 없습니다: $CANONICAL_SCRIPT" >&2
  exit 1
fi

exec "$CANONICAL_SCRIPT" "$@"
