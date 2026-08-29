#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv, then rerun: $0" >&2
  exit 1
fi

echo "Installing local AgentOS checkout: $ROOT"
exec uv tool install --force "$ROOT"
