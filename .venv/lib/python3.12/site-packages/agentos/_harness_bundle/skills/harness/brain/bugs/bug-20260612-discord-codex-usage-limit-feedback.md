# Bug: Discord bridge hid Codex usage-limit failures

**Date Reported**: 2026-06-12
**Date Fixed**: 2026-06-12
**Reporter**: User via Codex session
**Assignee**: Codex
**Severity**: Medium
**Status**: Fixed

## Problem

Discord requests failed with the generic message:

```text
요청 <request_id> 처리에 실패했습니다. 로그를 확인해주세요.
```

The request transcript showed the real cause:

```text
ERROR: You've hit your usage limit. Upgrade to Plus to continue using Codex, or try again later.
```

The user could not tell that the action needed was to wait for the Codex usage limit reset.

## Reproduction

1. Send a Discord request through AHA while Codex CLI is usage-limited.
2. Let the bridge retry resume/fresh execution.
3. Observe that the request ends as `failed` with `failure_reason=unknown_exit`.
4. Observe that the final Discord reply does not mention usage limits.

## Root Cause

The bridge already classified context-limit and transient Codex failures, but it did not classify Codex usage-limit text. The supervisor and `run-request.sh` therefore recorded `unknown_exit`, and `discord-bot.ts` rendered the generic log-check message.

## Fix

Added `codex_usage_limit` as a first-class failure reason in:

- `.agents/plugins/discord-codex-bridge/codex-bridge/server.ts`
- `.agents/plugins/discord-codex-bridge/codex-bridge/supervisor.ts`
- `.agents/plugins/discord-codex-bridge/codex-bridge/run-request.sh`
- `.agents/plugins/discord-codex-bridge/codex-bridge/discord-bot.ts`

The final Discord reply now tells the user that Codex usage limit was reached and that they should retry after the limit resets.

## Verification

```bash
bun test ./tests/discord_bridge/test_discord_bot.ts --test-name-pattern "codex failure reasons|gateway failure classification"
bun test ./tests/discord_bridge/test_access_gate.ts --test-name-pattern "supervisor classifies codex usage limit"
bash -n .agents/plugins/discord-codex-bridge/codex-bridge/run-request.sh
.agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex
.agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check
git diff --check
```

All checks passed.

## Prevention

When adding or observing a new Codex CLI terminal error, add both:

- a stable `RequestFailureReason`
- a user-facing `renderFailure` message

Do not leave user-actionable failures as `unknown_exit`.
