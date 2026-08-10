#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
mkdir -p "$tmpdir/skills"
cp -R catalog/skills/knowledge-curator "$tmpdir/skills/knowledge-curator"
python3 -S "$tmpdir/skills/knowledge-curator/scripts/knowledge.py" --help | grep -q 'init'
python3 -S "$tmpdir/skills/knowledge-curator/scripts/knowledge.py" --help | grep -q 'backup'
echo 'PASS aha-knowledge-standalone'
