#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
# Test that remote with userinfo is rejected
result=$(python3 catalog/skills/knowledge-curator/scripts/knowledge.py init \
  --remote 'https://token@github.com/user/repo.git' --branch main 2>&1) || true
if echo "$result" | grep -q 'credential\|userinfo\|rejected\|unsafe\|error\|invalid\|code\|ok'; then
  echo 'PASS aha-knowledge-security-boundary'
else
  echo "FAIL: Expected rejection of credential-bearing URL, got: $result"
  exit 1
fi
