#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEST=${AGENTOS_HOME:-"$HOME/.agentos"}
mkdir -p "$DEST"
mkdir -p "$DEST/core"
cp -R "$ROOT/.agents" "$DEST/core/.agents"
printf '%s\n' '{"managed_by":"agentOS","selection":"agentcore-only"}' > "$DEST/manifest.json"
echo "PASS agentos-setup destination=$DEST selection=agentcore-only"
