#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: create-worktree.sh --path PATH --branch BRANCH [--base REF] [--repo REPO]

Safely create a new git worktree for parallel work.

Options:
  --path PATH      Target worktree path. Must not already exist.
  --branch BRANCH  New branch name to create for the worktree.
  --base REF       Base ref for the new branch. Defaults to current branch.
  --repo REPO      Repository root to operate from. Defaults to current directory.
  --help           Show this help text.
EOF
}

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

repo="."
path=""
branch=""
base=""

while (($# > 0)); do
  case "$1" in
    --path)
      path="${2:-}"
      shift 2
      ;;
    --branch)
      branch="${2:-}"
      shift 2
      ;;
    --base)
      base="${2:-}"
      shift 2
      ;;
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$path" ]] || die "--path is required"
[[ -n "$branch" ]] || die "--branch is required"

repo_root="$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)" || die "not a git repository: $repo"
current_branch="$(git -C "$repo_root" branch --show-current)"
[[ -n "$current_branch" ]] || die "could not determine current branch"

if [[ -z "$base" ]]; then
  base="$current_branch"
fi

git -C "$repo_root" rev-parse --verify "$base^{commit}" >/dev/null 2>&1 || die "base ref does not exist: $base"

if [[ -e "$path" ]]; then
  die "target path already exists: $path"
fi

if git -C "$repo_root" show-ref --verify --quiet "refs/heads/$branch"; then
  die "branch already exists: $branch"
fi

if git -C "$repo_root" worktree list --porcelain | grep -F "branch refs/heads/$branch" >/dev/null 2>&1; then
  die "branch is already attached to an existing worktree: $branch"
fi

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'BASE_REF=%s\n' "$base"
printf 'TARGET_BRANCH=%s\n' "$branch"
printf 'TARGET_PATH=%s\n' "$path"
printf 'PRECHECK=PASS\n'

git -C "$repo_root" worktree add -b "$branch" "$path" "$base"

printf 'POSTCHECK_STATUS_BEGIN\n'
git -C "$path" status --short
printf 'POSTCHECK_BRANCH=%s\n' "$(git -C "$path" branch --show-current)"
git -C "$repo_root" worktree list
printf 'POSTCHECK_STATUS_END\n'
