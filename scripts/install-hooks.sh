#!/usr/bin/env bash
# scripts/install-hooks.sh
# Links AgentOS unified hooks into native CLI configurations.

set -euo pipefail

PROJECT_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
HOOKS_ADAPTERS="$PROJECT_ROOT/.agents/hooks/adapters"

echo "🔗 Installing AgentOS Unified Hooks..."

# 1. Claude Code
if [ -d "$HOOKS_ADAPTERS/claude-code" ]; then
    mkdir -p "$PROJECT_ROOT/.claude"
    if [ -f "$HOOKS_ADAPTERS/claude-code/settings.json" ]; then
        cp "$HOOKS_ADAPTERS/claude-code/settings.json" "$PROJECT_ROOT/.claude/settings.json"
        echo "✅ Claude Code hooks linked."
    fi
fi

# 2. Codex
if [ -d "$HOOKS_ADAPTERS/codex" ]; then
    mkdir -p "$PROJECT_ROOT/.codex"
    if [ -f "$HOOKS_ADAPTERS/codex/hooks.json" ]; then
        cp "$HOOKS_ADAPTERS/codex/hooks.json" "$PROJECT_ROOT/.codex/hooks.json"
        echo "✅ Codex hooks linked."
    fi
fi

# 3. Antigravity (agy)
if [ -d "$HOOKS_ADAPTERS/agy" ]; then
    # 사용자 요구에 따라 프로젝트 표면에 .gemini 설정 폴더를 명시적으로 노출합니다.
    mkdir -p "$PROJECT_ROOT/.gemini/plugins/agentos-unified-hooks"
    cp -r "$HOOKS_ADAPTERS/agy/"* "$PROJECT_ROOT/.gemini/plugins/agentos-unified-hooks/"
    
    # agy는 로컬 플러그인 자동 로드를 공식 지원하지 않고 글로벌(~/.gemini) 설치를 강제합니다.
    # 프로젝트 독립성(Isolability)을 지키기 위해 글로벌 오염을 유발하는 자동 install은 수행하지 않습니다.
    # 단지 표면(Surface)에 구성을 노출하여 클론한 개발자가 명시적으로 인지할 수 있도록 합니다.
    echo "✅ Antigravity (agy) hooks mapped to .gemini/plugins/ (Global install skipped for isolation)."
fi

echo "🎉 All hooks successfully mapped to AgentOS common scripts."
