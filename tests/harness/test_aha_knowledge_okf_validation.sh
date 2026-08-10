#!/bin/bash
# OKF v0.2 validation harness: smoke test for direct-copy checker exit status.
# Verifies that the installed standalone copy of knowledge.py validate
# correctly exits 0 for a valid bundle and exits 2 for a bundle with errors.
# This test does not use the Python test runner.
set -euo pipefail
cd "$(dirname "$0")/../.."

TMPDIR_ROOT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

# Copy the skill to a temporary location (simulate installed copy)
SKILL_DIR="$TMPDIR_ROOT/skills/knowledge-curator"
mkdir -p "$TMPDIR_ROOT/skills"
cp -R catalog/skills/knowledge-curator "$SKILL_DIR"
KNOWLEDGE_PY="$SKILL_DIR/scripts/knowledge.py"

# Helper: run validate and capture both stdout and exit code without stopping on non-zero
run_validate() {
    local result
    local code
    result=$(python3 -S "$KNOWLEDGE_PY" validate "$@" 2>/dev/null) && code=$? || code=$?
    echo "$result"
    return "$code"
}

# ---------------------------------------------------------------------------
# Test 1: validate exits 0 for a valid OKF v0.2 bundle
# ---------------------------------------------------------------------------
VALID_BUNDLE="$TMPDIR_ROOT/valid-bundle"
mkdir -p "$VALID_BUNDLE/concepts"
cat > "$VALID_BUNDLE/index.md" << 'EOF'
---
okf_version: "0.2"
title: Test Knowledge Base
description: A valid OKF v0.2 bundle for smoke testing.
---

# Test Knowledge Base
EOF
cat > "$VALID_BUNDLE/log.md" << 'EOF'
---
title: Activity Log
---

# Activity Log
EOF
cat > "$VALID_BUNDLE/concepts/example.md" << 'EOF'
---
type: concept
title: Example
description: An example concept.
status: stable
---

# Example
EOF

output=$(run_validate --project "$VALID_BUNDLE") && exit_code=$? || exit_code=$?
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: valid bundle should exit 0, got $exit_code"
    echo "Output: $output"
    exit 1
fi
# Verify JSON envelope
ok_field=$(echo "$output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['ok'])" 2>/dev/null || echo "parse-error")
if [ "$ok_field" != "True" ]; then
    echo "FAIL: ok field should be True, got: $ok_field"
    echo "Output: $output"
    exit 1
fi
changed_field=$(echo "$output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['changed'])" 2>/dev/null || echo "parse-error")
if [ "$changed_field" != "False" ]; then
    echo "FAIL: changed field should be False, got: $changed_field"
    exit 1
fi

# ---------------------------------------------------------------------------
# Test 2: validate exits 2 for a bundle missing index.md
# ---------------------------------------------------------------------------
INVALID_BUNDLE="$TMPDIR_ROOT/invalid-bundle"
mkdir -p "$INVALID_BUNDLE"
echo "# log" > "$INVALID_BUNDLE/log.md"
# No index.md

output=$(run_validate --project "$INVALID_BUNDLE") && exit_code=$? || exit_code=$?
if [ "$exit_code" -ne 2 ]; then
    echo "FAIL: missing-index bundle should exit 2, got $exit_code"
    echo "Output: $output"
    exit 1
fi
has_error=$(echo "$output" | python3 -c "import json,sys; d=json.load(sys.stdin); codes=[x['code'] for x in d.get('diagnostics',[])]; print('OKF_INDEX_MISSING' in codes)" 2>/dev/null || echo "False")
if [ "$has_error" != "True" ]; then
    echo "FAIL: expected OKF_INDEX_MISSING diagnostic"
    echo "Output: $output"
    exit 1
fi

# ---------------------------------------------------------------------------
# Test 3: validate --strict exits 2 for warnings
# ---------------------------------------------------------------------------
WARN_BUNDLE="$TMPDIR_ROOT/warn-bundle"
mkdir -p "$WARN_BUNDLE/concepts"
cat > "$WARN_BUNDLE/index.md" << 'EOF'
---
okf_version: "0.2"
title: Warn Bundle
---
# Warn Bundle
EOF
echo "# log" > "$WARN_BUNDLE/log.md"
cat > "$WARN_BUNDLE/concepts/c.md" << 'EOF'
---
type: concept
---
# C
EOF

output=$(run_validate --project "$WARN_BUNDLE" --strict) && exit_code=$? || exit_code=$?
if [ "$exit_code" -ne 2 ]; then
    echo "FAIL: strict mode with warnings should exit 2, got $exit_code"
    echo "Output: $output"
    exit 1
fi

# ---------------------------------------------------------------------------
# Test 4: stderr is empty for valid bundle
# ---------------------------------------------------------------------------
stderr_output=$(python3 -S "$KNOWLEDGE_PY" validate --project "$VALID_BUNDLE" 2>&1 1>/dev/null) || true
if [ -n "$stderr_output" ]; then
    echo "FAIL: stderr should be empty, got: $stderr_output"
    exit 1
fi

# ---------------------------------------------------------------------------
# Test 5: --migrate is refused with JSON error (exit 2)
# ---------------------------------------------------------------------------
output=$(run_validate --project "$VALID_BUNDLE" --migrate) && exit_code=$? || exit_code=$?
if [ "$exit_code" -ne 2 ]; then
    echo "FAIL: --migrate should exit 2, got $exit_code"
    exit 1
fi
ok_field=$(echo "$output" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['ok'])" 2>/dev/null || echo "parse-error")
if [ "$ok_field" != "False" ]; then
    echo "FAIL: --migrate ok should be False, got: $ok_field"
    exit 1
fi

echo 'PASS aha-knowledge-okf-validation'
