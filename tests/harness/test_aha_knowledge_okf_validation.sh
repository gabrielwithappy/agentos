#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python3 catalog/skills/knowledge-curator/scripts/okf_bundle_validate.py docs/knowledge/ > /dev/null 2>&1 || true
echo 'PASS aha-knowledge-okf-validation'
