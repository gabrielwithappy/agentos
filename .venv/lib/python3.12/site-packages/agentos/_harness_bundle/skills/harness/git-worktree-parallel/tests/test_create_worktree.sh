#!/usr/bin/env bash
set -euo pipefail

case_name="${2:-all}"
if [[ "${1:-}" == "--case" ]]; then
  case_name="${2:-all}"
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
helper="$script_dir/scripts/create-worktree.sh"
temp_root="$(mktemp -d)"
repo="$temp_root/repo"
outside="$temp_root/outside"
case "$temp_root" in
  /tmp/tmp.*) ;;
  *) echo "unsafe temporary root: $temp_root" >&2; exit 1 ;;
esac

cleanup() {
  local canonical_root worktree_count
  canonical_root="$(python3 - "$temp_root" <<'PY'
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
)"
  if [[ "$canonical_root" != "$temp_root" ]]; then
    echo "refusing non-canonical temporary cleanup root: $temp_root" >&2
    return 1
  fi
  worktree_count="$(git -C "$repo" worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true)"
  if [[ "$worktree_count" -ne 1 ]]; then
    echo "refusing temporary cleanup with registered worktrees: $temp_root" >&2
    return 1
  fi
  rm -rf -- "$temp_root"
}
trap cleanup EXIT

mkdir -p "$repo" "$outside"
git -C "$repo" init -q
git -C "$repo" config user.email test@example.invalid
git -C "$repo" config user.name test
touch "$repo/initial"
git -C "$repo" add initial
git -C "$repo" commit -qm initial

cleanup_worktree() {
  local target="$1" branch="$2"
  test -d "$target"
  test -z "$(git -C "$target" status --short)"
  git -C "$repo" worktree remove "$target"
  git -C "$repo" branch -d "$branch" >/dev/null
}

snapshot() {
  git -C "$repo" worktree list --porcelain
  git -C "$repo" status --short
  git -C "$repo" show-ref --heads
  test -e "$repo/.agentos/worktrees" && python3 -c 'import os; print(os.path.realpath("'$repo'/.agentos/worktrees"))' || true
}

expect_rejection() {
  local output="$1" target="$2" sentinel="$3"; shift 3
  local before after
  before="$(snapshot); if test -e "$target"; then echo target-present; else echo target-absent; fi; if test -e "$sentinel"; then echo sentinel-present; else echo sentinel-absent; fi"
  if bash "$helper" --repo "$repo" "$@" >"$output" 2>&1; then exit 1; fi
  after="$(snapshot); if test -e "$target"; then echo target-present; else echo target-absent; fi; if test -e "$sentinel"; then echo sentinel-present; else echo sentinel-absent; fi"
  test "$before" = "$after"
}

run_default() {
  local target="$repo/.agentos/worktrees/feature-example"
  output="$(bash "$helper" --repo "$repo" --branch feature/example --base HEAD)"
  grep -Fq 'PRECHECK=PASS' <<<"$output"
  grep -Fq "TARGET_PATH=$target" <<<"$output"
  grep -Fq 'POSTCHECK_BRANCH=feature/example' <<<"$output"
  test -f "$target/.git"
  test -z "$(git -C "$target" status --short)"
  cleanup_worktree "$target" feature/example
}

run_branch_collision_without_default_root() {
  test ! -e "$repo/.agentos/worktrees"
  git -C "$repo" branch feature/already HEAD
  expect_rejection "$temp_root/branch-out" "$repo/.agentos/worktrees/feature-already" "$outside/sentinel" --branch feature/already --base HEAD
  test ! -e "$repo/.agentos/worktrees"
  grep -Fq 'ERROR: branch already exists:' "$temp_root/branch-out"
  git -C "$repo" branch -d feature/already >/dev/null
}

run_ancestor_symlink_rejection() {
  ln -s "$outside" "$repo/.agentos"
  expect_rejection "$temp_root/ancestor-out" "$outside/worktrees/feature-ancestor-link" "$outside/sentinel" --branch feature/ancestor-link --base HEAD
  grep -Fq 'ERROR: default worktree root escapes repository:' "$temp_root/ancestor-out"
  test ! -e "$outside/worktrees"
  unlink "$repo/.agentos"
}

run_explicit() {
  local target="$outside/explicit"
  output="$(bash "$helper" --repo "$repo" --branch feature/explicit --path "$target" --base HEAD)"
  grep -Fq "TARGET_PATH=$target" <<<"$output"
  test -d "$target"
  cleanup_worktree "$target" feature/explicit
}

run_rejection() {
  local target="$repo/.agentos/worktrees/feature-existing"
  mkdir -p "$target"
  expect_rejection "$temp_root/out" "$target" "$outside/sentinel" --branch feature/existing --base HEAD
  grep -Fq 'ERROR: target path already exists:' "$temp_root/out"
  grep -Fq "Next: run 'git worktree list'" "$temp_root/out"
  test ! -e "$repo/.git/refs/heads/feature/existing"
}

run_symlink_rejection() {
  rmdir "$repo/.agentos/worktrees"
  ln -s "$outside" "$repo/.agentos/worktrees"
  expect_rejection "$temp_root/symlink-out" "$outside/feature-symlink" "$outside/sentinel" --branch feature/symlink --base HEAD
  grep -Fq 'ERROR: default worktree root is a symlink:' "$temp_root/symlink-out"
  grep -Fq 'Next: choose a path inside' "$temp_root/symlink-out"
  test ! -e "$repo/.git/refs/heads/feature/symlink"
  unlink "$repo/.agentos/worktrees"
}

run_slug_collision() {
  local target="$repo/.agentos/worktrees/feature-a"
  bash "$helper" --repo "$repo" --branch feature/a --base HEAD >/dev/null
  expect_rejection "$temp_root/slug-out" "$target" "$outside/sentinel" --branch feature-a --base HEAD
  grep -Fq 'ERROR: target path already exists:' "$temp_root/slug-out"
  test ! -e "$repo/.git/refs/heads/feature-a"
  cleanup_worktree "$target" feature/a
}

run_explicit_rejections() {
  local target="$outside/existing" before after
  mkdir -p "$target"
  expect_rejection "$temp_root/explicit-out" "$target" "$outside/sentinel" --branch feature/explicit-existing --path "$target" --base HEAD
  grep -Fq 'ERROR: target path already exists:' "$temp_root/explicit-out"
  expect_rejection "$temp_root/empty-out" "$repo/.agentos/worktrees/feature-empty" "$outside/sentinel" --branch feature/empty --path '' --base HEAD
  grep -Fq 'ERROR: --path must not be empty' "$temp_root/empty-out"
}

run_invalid_inputs() {
  local sentinel="$outside/sentinel" hostile=$'feature/line\nbreak' backtick_literal='`should-not-run`'
  expect_rejection "$temp_root/newline-out" "$repo/.agentos/worktrees/feature-line-break" "$sentinel" --branch "$hostile" --base HEAD
  expect_rejection "$temp_root/hostile-out" "$repo/.agentos/worktrees/hostile" "$sentinel" --branch "feature/\$(touch $sentinel)" --base HEAD
  expect_rejection "$temp_root/hostile-path-out" "$repo/\$(touch $sentinel)" "$sentinel" --branch feature/hostile-path --path "\$(touch $sentinel)" --base HEAD
  expect_rejection "$temp_root/backtick-out" "$repo/.agentos/worktrees/backtick" "$sentinel" --branch 'feature/`should-not-run`' --base HEAD
  expect_rejection "$temp_root/backtick-path-out" "$repo/$backtick_literal" "$sentinel" --branch feature/backtick-path --path "$backtick_literal" --base HEAD
  expect_rejection "$temp_root/option-out" "$repo/.agentos/worktrees/bad" "$sentinel" --branch '-bad' --base HEAD
  test ! -e "$sentinel"
  test ! -e "$repo/.git/refs/heads/feature/line"
}

case "$case_name" in
  all) run_branch_collision_without_default_root; run_ancestor_symlink_rejection; run_default; run_explicit; run_symlink_rejection; run_rejection; run_slug_collision; run_explicit_rejections; run_invalid_inputs ;;
  default-create) run_default ;;
  rejection) run_default; run_symlink_rejection; run_rejection ;;
  residue)
    test "$(git -C "$repo" worktree list --porcelain | grep -c '^worktree ')" -eq 1
    ;;
  *) echo "unknown case: $case_name" >&2; exit 2 ;;
esac

echo "PASS test_create_worktree:$case_name"
