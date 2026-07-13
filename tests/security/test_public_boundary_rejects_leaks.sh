#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
cp -a "$ROOT"/. "$TMP/repo"
prefix=$(printf 'gh%s' 'p_')
printf '%s\n' "token=${prefix}not-a-real-token" >"$TMP/repo/leak.txt"
if python3 "$ROOT/scripts/security/scan-public-boundary.py" --root "$TMP/repo" --worktree >"$TMP/out" 2>&1; then
  echo 'FAIL leak-fixture-accepted' >&2; exit 1
fi
! grep -q 'not-a-real-token' "$TMP/out"
case "${1:-}" in --entrypoint) [[ "${2:-}" == hook || "${2:-}" == ci ]] || exit 2;; '') ;; *) exit 2;; esac
if [[ "${2:-}" == hook ]]; then echo 'PASS hook-rejects-redacted-leak-fixtures'; else echo 'PASS ci-entrypoint-rejects-redacted-leak-fixtures'; fi
