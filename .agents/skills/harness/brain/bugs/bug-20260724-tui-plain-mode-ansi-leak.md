# Bug: `AGENTOS_TUI_TEST_PLAIN=1` transcript still contains ANSI markup around "/"

**Date Reported**: 2026-07-24
**Date Fixed**: 2026-07-24 (fixed during `2026-07-24-agentos-pi-session-runtime-tui-architecture` Task 7 Step 5 closeout — blocked that plan's own `bash scripts/verify-cli-isolated-install.sh` verification requirement)
**Reporter**: Claude (session work on native Codex auth/transport plan)
**Assignee**: unassigned
**Severity**: Low
**Status**: Fixed

## Problem Description

`scripts/verify-cli-isolated-install.sh` fails at the installed TUI pseudo-TTY
smoke step. `tests/helpers/pty_cli_driver.py::_assert_installed_tui` asserts
the exact substring `"Type a message or / for commands"` is present in the
transcript, but the rendered line contains Rich ANSI markup around the `/`
character (`Type a message or [35m/[0m for commands`), so the plain
substring never matches.

## Reproduction Steps

1. Build an isolated venv install of `agentos` (see `scripts/verify-cli-isolated-install.sh`).
2. Run the installed `agentos` binary under a pseudo-TTY with
   `AGENTOS_TUI_TEST_PLAIN=1` set.
3. Observe the transcript line is `AgentOS\nType a message or \x1b[35m/\x1b[0m for commands\n...`
   instead of a plain, uncolored string.

## Root Cause (confirmed)

`agentos/terminal/tui/app.py::run_plain_tui_transcript` constructs a plain
`Console()`, which leaves Rich's default content **highlighter** enabled.
The highlighter pattern-matches path-like tokens (anything containing `/`)
in printed text and wraps them in ANSI color codes automatically — this is
independent of Rich markup syntax (`[bold]...[/]`); it fires on the literal
character even with zero markup in the call sites. This is why `no_color`
alone was suspected but the real fix is `highlight=False`.

## Verification that this is pre-existing, not a regression

- `git diff HEAD -- agentos/terminal/tui/app.py` is empty for the commit
  that introduced native Codex auth/transport (`923d35e`); that work never
  touched this file.
- `scripts/verify-cli-isolated-install.sh` and `tests/helpers/pty_cli_driver.py`
  were already modified (uncommitted) before this session started, from
  unrelated prior work (`2026-07-23-agentos-llm-invocation-runtime-architecture`
  per `HISTORY.md`).
- Reproduced independently outside a git worktree with a fresh isolated
  venv install; failure is identical regardless of the native auth/transport
  change.

## Fix Applied

`agentos/terminal/tui/app.py::run_plain_tui_transcript` now constructs
`Console(highlight=False)`. Verified: `bash scripts/verify-cli-isolated-install.sh`
now prints `PASS installed-tui-smoke` and `PASS agentos-cli-isolated-install`;
full `uv run pytest tests/ -q` (293 passed, no regressions).

## Impact (resolved)

`bash scripts/verify-cli-isolated-install.sh` previously failed at the
`installed-tui-pseudo-tty` step. All other checks in that script and the
full test suite were unaffected even before this fix.
