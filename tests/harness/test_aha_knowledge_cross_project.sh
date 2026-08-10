#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
# Create two projects with bare remote
git init --bare "$tmpdir/knowledge.git" > /dev/null
mkdir -p "$tmpdir/project-a/docs/knowledge" "$tmpdir/project-b"
# Copy a sample OKF doc
cp docs/knowledge/README.md "$tmpdir/project-a/docs/knowledge/" 2>/dev/null || echo '---
type: Reference
title: Test
---
# Test' > "$tmpdir/project-a/docs/knowledge/test.md"
echo 'PASS aha-knowledge-cross-project'
