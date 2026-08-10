#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
# Test local backup/restore scenario
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
git init --bare "$tmpdir/knowledge.git" > /dev/null
mkdir -p "$tmpdir/project"
# Init with local bare remote
python3 catalog/skills/knowledge-curator/scripts/knowledge.py init \
  --remote "file://$tmpdir/knowledge.git" --branch main \
  --project "$tmpdir/project" >/dev/null
python3 catalog/skills/knowledge-curator/scripts/knowledge.py status --project "$tmpdir/project" | grep -q '"ok": true'
echo 'PASS aha-knowledge-git-workflow'
