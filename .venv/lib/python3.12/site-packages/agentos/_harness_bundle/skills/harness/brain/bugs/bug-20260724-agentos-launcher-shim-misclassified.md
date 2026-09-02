# Bug: AgentOS launcher shim misclassified as installed canonical command

**Date Reported**: 2026-07-24
**Date Fixed**: 2026-07-24
**Reporter**: user
**Assignee**: Codex
**Severity**: Medium
**Status**: Fixed

## Problem Description

`uv run agentos doctor --json` reported `installed_agentos: true` even when the user's shell could not run bare `agentos`. The benchmark also treated the active `uv` virtualenv shim as `installed_cli`, making launcher guidance misleading while the user still saw slow or missing responses from the expected `agentos` command.

## Reproduction Steps

1. Ensure bare `agentos` is absent from the shell PATH.
2. Run `uv run agentos doctor --json`.
3. Observe that the previous implementation reported the active `.venv/bin/agentos` shim as installed.

## Root Cause

`doctor` and `agentos.runtime.bench` used `shutil.which("agentos")` inside the `uv run` process. `uv run` prepends the project virtualenv bin directory to `PATH`, so `which("agentos")` found `.venv/bin/agentos` even though the user's shell did not have a canonical installed launcher.

## Fix Applied

Added `agentos.runtime.launcher.resolve_agentos_launcher()` and changed `doctor` and benchmark installed-cli measurement to classify `VIRTUAL_ENV/bin/agentos` as `development_shim`, not installed canonical `agentos`.

## Verification

- `uv run agentos doctor --json` now reports `launcher.status: development_shim` and `installed_agentos: false` in the reproduced environment.
- `uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --format json` now reports `installed_cli.available: false` with `status: development_shim`.
- `uv run pytest tests/test_runtime_bench.py tests/test_cli_isolated_install.py -q` -> 11 passed.
- `bash scripts/verify-cli-isolated-install.sh` -> `PASS agentos-cli-isolated-install`.
- `uv run pytest tests/ -q` -> 152 passed.
