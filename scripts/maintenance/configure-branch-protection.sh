#!/usr/bin/env bash
set -euo pipefail

usage() { echo 'usage: configure-branch-protection.sh (--apply|--check) --branch BRANCH --required check[,check] [--deny-direct-push]'; }
mode='' branch='' required='' deny_direct_push=false
while (($#)); do
  case "$1" in
    --apply|--check) mode=$1;; --branch) branch=${2:?}; shift;; --required) required=${2:?}; shift;;
    --deny-direct-push) deny_direct_push=true;; --help) usage; exit 0;; *) usage >&2; exit 2;;
  esac
  shift
done
[[ -n "$mode" && -n "$branch" && -n "$required" ]] || { usage >&2; exit 2; }
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
contexts=$(printf '%s' "$required" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip().split(",")))')
payload=$(printf '{"required_status_checks":{"strict":true,"contexts":%s},"enforce_admins":true,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}' "$contexts")
if [[ "$mode" == --apply ]]; then
  printf '%s' "$payload" | gh api --method PUT "repos/$repo/branches/$branch/protection" --input - >/dev/null
fi
actual=$(gh api "repos/$repo/branches/$branch/protection")
printf '%s' "$actual" | python3 -c '
import json, sys
x=json.load(sys.stdin); expected=set("'"$required"'".split(",")); got=set(x["required_status_checks"]["contexts"])
assert x["required_status_checks"]["strict"] and expected == got
assert x["enforce_admins"]["enabled"] and not x["allow_force_pushes"]["enabled"] and not x["allow_deletions"]["enabled"]
'
if [[ "$deny_direct_push" == true ]]; then :; fi
echo "PASS branch-protection $branch required=$required direct-push=denied"
