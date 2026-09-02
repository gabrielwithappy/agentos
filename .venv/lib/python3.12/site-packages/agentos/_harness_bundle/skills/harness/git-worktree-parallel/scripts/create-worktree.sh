#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: create-worktree.sh --branch BRANCH [--base REF] [--path PATH] [--repo REPO]

Safely create a new git worktree for parallel work.

Options:
  --path PATH      Optional target path. If omitted, uses
                   <repo>/.agentos/worktrees/<branch-slug>.
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

die_collision() {
  printf 'ERROR: %s\n' "$1" >&2
  printf "Next: run 'git worktree list' to inspect it; choose a new --branch/--path or explicitly reuse the existing worktree.\n" >&2
  exit 1
}

die_default_path() {
  printf 'ERROR: %s\n' "$1" >&2
  printf 'Next: choose a path inside <repo>/.agentos/worktrees or pass a valid explicit --path.\n' >&2
  exit 1
}

canonical_path() {
  python3 - "$1" <<'PY'
import os
import sys
print(os.path.realpath(os.path.abspath(sys.argv[1])))
PY
}

repo="."
path=""
path_was_supplied=false
branch=""
base=""

while (($# > 0)); do
  case "$1" in
    --path)
      path="${2:-}"
      path_was_supplied=true
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

[[ -n "$branch" ]] || die "--branch is required"
if [[ "$path_was_supplied" == true && -z "$path" ]]; then
  die "--path must not be empty"
fi
if [[ "$path_was_supplied" == true && ( "$path" == *'$('* || "$path" == *'`'* || "$path" == *$'\n'* ) ]]; then
  die "invalid --path: shell-like characters are not allowed"
fi

repo_root="$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)" || die "not a git repository: $repo"
repo_root="$(canonical_path "$repo_root")"
current_branch="$(git -C "$repo_root" branch --show-current)"
[[ -n "$current_branch" ]] || die "could not determine current branch"

git check-ref-format --branch "$branch" >/dev/null 2>&1 || die "invalid branch name: $branch"
if [[ "$branch" == *'$('* || "$branch" == *'`'* || "$branch" == *$'\n'* ]]; then
  die "invalid branch name: shell-like characters are not allowed"
fi

if [[ -z "$base" ]]; then
  base="$current_branch"
fi

git -C "$repo_root" rev-parse --verify "$base^{commit}" >/dev/null 2>&1 || die "base ref does not exist: $base"

if [[ -z "$path" ]]; then
  slug="$(printf '%s' "$branch" | sed -E 's/[^A-Za-z0-9.-]+/-/g; s/^-+//; s/-+$//')"
  [[ -n "$slug" && "$slug" != "." && "$slug" != ".." ]] || die_default_path "invalid default path slug for branch: $branch"
  default_root="$repo_root/.agentos/worktrees"
  [[ ! -L "$default_root" ]] || die_default_path "default worktree root is a symlink: $default_root"
  if [[ -e "$default_root" ]]; then
    [[ -d "$default_root" ]] || die_default_path "default worktree root is not a directory: $default_root"
  fi
  path="$default_root/$slug"
  canonical_default_root="$(canonical_path "$default_root")"
  canonical_path_candidate="$(canonical_path "$path")"
  [[ "$canonical_default_root" == "$default_root" ]] || die_default_path "default worktree root escapes repository: $default_root"
  [[ "$canonical_path_candidate" == "$canonical_default_root"/* ]] || die_default_path "default target escapes worktree root: $path"
else
  path="$(canonical_path "$path")"
fi

if [[ -e "$path" || -L "$path" ]]; then
  die_collision "target path already exists: $path"
fi

if git -C "$repo_root" show-ref --verify --quiet "refs/heads/$branch"; then
  die_collision "branch already exists: $branch"
fi

if git -C "$repo_root" worktree list --porcelain | grep -F "branch refs/heads/$branch" >/dev/null 2>&1; then
  die_collision "branch is already attached to an existing worktree: $branch"
fi

if [[ "$path_was_supplied" == false ]]; then
  mkdir -p "$default_root"
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
