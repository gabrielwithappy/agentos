#!/usr/bin/env bash
set -euo pipefail

sha='' timeout=1200 cached=false
declare -a workflows=()
while (($#)); do
  case "$1" in
    --sha) sha=${2:?}; shift;; --workflow) workflows+=("${2:?}"); shift;; --timeout) timeout=${2:?}; shift;;
    --cached-success-only) cached=true;; --help) echo 'usage: verify-pushed-ci.sh --sha SHA --workflow FILE [--workflow FILE] [--timeout seconds] [--cached-success-only]'; exit 0;; *) exit 2;;
  esac
  shift
done
[[ -n "$sha" && ${#workflows[@]} -gt 0 ]] || exit 2
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
deadline=$(( $(date +%s) + timeout ))
for workflow in "${workflows[@]}"; do
  while :; do
    status=$(gh run list --repo "$repo" --workflow "$workflow" --commit "$sha" --limit 1 --json status,conclusion --jq 'if length == 0 then "missing" else .[0].status + ":" + (. [0].conclusion // "") end')
    [[ "$status" == completed:success ]] && break
    [[ "$cached" == true || $(date +%s) -ge $deadline ]] && { echo "FAIL pushed-ci workflow=$workflow status=$status" >&2; exit 1; }
    sleep 10
  done
done
echo "PASS pushed-ci sha=$sha workflows=${workflows[*]}"
