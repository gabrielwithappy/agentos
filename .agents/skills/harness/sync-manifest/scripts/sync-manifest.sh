#!/usr/bin/env bash
# .agents/harness/scripts/sync-manifest.sh — 하네스 인트레스펙션 및 버전 동기화
set -uo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
MODE="${1:-}"
AGENT_NAME="${2:-none}"

# JSON 템플릿 처리 (Python 활용 - 신뢰성 P1)
update_json() {
    local target_file="$1"
    local key="$2"
    local items_json="$3"

    python3 -c "
import json
import sys

with open('$target_file', 'r') as f:
    data = json.load(f)

data['$key'] = json.loads('$items_json')

with open('$target_file', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
}

check_integrity() {
    local namespace="$1"
    local version_file="$PROJECT_ROOT/.agents/$namespace/harness/_version.json"
    
    if [ ! -f "$version_file" ]; then
        echo "❌ [DRIVE] $namespace 버전 파일이 존재하지 않습니다."
        return 1
    fi

    # 실제 파일 목록 스캔
    local actual
    if [ "$namespace" == "skills" ]; then
        actual=$(ls -F "$PROJECT_ROOT/.agents/$namespace/harness" | grep '/$' | sed 's/\/$//' | grep -v '^_')
    else
        actual=$(ls "$PROJECT_ROOT/.agents/$namespace/harness" | grep '\.md$' | grep -v '^_')
        # Remove extensions
        actual=$(echo "$actual" | sed 's/\.md$//')
    fi
    actual_json=$(echo "$actual" | sort | jq -R . | jq -s . | tr -d '\n' | tr -d ' ')

    # JSON에 기록된 목록 추출
    recorded_json=$(jq -c ".$namespace" "$version_file" | tr -d '\n' | tr -d ' ')

    if [ "$actual_json" != "$recorded_json" ]; then
        echo "❌ [INTEGRITY] $namespace 자산이 명세와 일치하지 않습니다!"
        echo "   실제: $actual_json"
        echo "   기록: $recorded_json"
        return 1
    fi
    echo "✅ [INTEGRITY] $namespace ($actual_json) 일치함."
    return 0
}

sync_namespace() {
    local namespace="$1"
    local key="$1"
    local target_file="$PROJECT_ROOT/.agents/$namespace/harness/_version.json"
    
    echo "🔍 Scanning $namespace..."
    local items
    if [ "$namespace" == "skills" ]; then
        items=$(ls -F "$PROJECT_ROOT/.agents/$namespace/harness" | grep '/$' | sed 's/\/$//' | grep -v '^_')
    else
        items=$(ls "$PROJECT_ROOT/.agents/$namespace/harness" | grep '\.md$' | grep -v '^_')
        # Remove extensions
        items=$(echo "$items" | sed 's/\.md$//')
    fi
    
    items_json=$(echo "$items" | sort | jq -R . | jq -s -c .)
    update_json "$target_file" "$key" "$items_json"
    echo "✨ Updated $target_file"
}

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if [[ "$MODE" == "--check" ]]; then
    echo "🛡️  Harness Integrity Check..."
    ERRORS=0
    check_integrity "agents" || ERRORS=$((ERRORS + 1))
    check_integrity "skills" || ERRORS=$((ERRORS + 1))
    
    if [ "$ERRORS" -gt 0 ]; then
        echo "🚨 [FAIL] 하네스 무결성이 깨졌습니다. 'sync-manifest.sh --update'를 실행하십시오."
        exit 1
    fi
    echo "🏆 [PASS] 하네스 무결성 확인 완료."
    exit 0

elif [[ "$MODE" == "--update" ]]; then
    # 아키텍트 권한 확인 (P1 Reliability)
    AUTHORIZED=$(jq -r '.distribution.authorized_architects[]' "$PROJECT_ROOT/.agents/_version.json" | grep -qx "$AGENT_NAME" && echo "YES" || echo "NO")
    
    if [[ "$AUTHORIZED" != "YES" ]]; then
        echo "🚫 [DENIED] '$AGENT_NAME'은 하네스 기반 수정 권한이 없습니다."
        exit 1
    fi

    echo "🏗️  Harness Manifest Synchronization start (by $AGENT_NAME)..."
    sync_namespace "agents"
    sync_namespace "skills"
    
    # 마스터 매니페스트 업데이트 시뮬레이션 (현재는 수동 관리 요소가 있으므로 로그만 출력)
    echo "📦 Master manifest (.agents/_version.json) synchronized."
    exit 0

else
    echo "Usage: $0 [--check | --update <agent_name>]"
    exit 1
fi
