#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help | grep -q 'init'
python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help | grep -q 'backup'
echo 'PASS aha-knowledge-standalone'
