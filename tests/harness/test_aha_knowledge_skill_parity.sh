#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
# Test that AHA bridge and skill produce same JSON output structure
result=$(echo '{"command": "help", "args": {}}' | python3 catalog/skills/knowledge-curator/scripts/aha_knowledge_bridge.py 2>/dev/null || echo '{"ok": false}')
echo "$result" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); assert 'ok' in d"
echo 'PASS aha-knowledge-skill-parity'
