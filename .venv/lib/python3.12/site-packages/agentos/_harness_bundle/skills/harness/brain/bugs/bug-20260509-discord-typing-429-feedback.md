# Bug: Discord message feedback lost after typing API 429

**Date Reported**: 2026-05-09
**Date Fixed**: 2026-05-09
**Reporter**: User
**Assignee**: Codex debug session
**Severity**: MEDIUM
**Status**: FIXED

## Problem Description

Discord commands/messages reached the bot process, but the user received no feedback.

Expected behavior: a request should still be queued and acknowledged even if Discord's optional typing indicator API fails.

## Evidence

Recent `.discord/logs/codex-discord-bot.log` contained:

```text
message handler error=Error: discord_http_429:{"message": "Service resource is being rate limited.", "retry_after": 3, "global": false, "code": 40062}
```

No new request directory was created after the latest failure, which showed the crash happened before `enqueueRequest`.

## Root Cause

`handleMessageWithDeps` awaited `deps.createTyping(message.channel_id)` directly. If Discord returned a 429 for the typing endpoint, the exception escaped the message handler and skipped request enqueue, acknowledgement, progress relay, and final reply.

## Fix Applied

Added `safeCreateTyping`, making typing indicator failures best-effort. The handler now logs typing failures and continues to enqueue and acknowledge the request.

Files changed:

- `.discord/codex-bridge/discord-bot.ts`
- `.agents/plugins/discord-agent-pool/codex-bridge/discord-bot.ts`
- `tests/discord_bridge/test_discord_bot.ts`

## Verification

```bash
bun test ./tests/discord_bridge/test_discord_bot.ts
```

Result: 58 pass, 0 fail.

Runtime was restarted with:

```bash
.discord/codex-bridge/pool-tmux.sh restart
.discord/codex-bridge/pool-tmux.sh status
```

Result: bridge and discord-bot ONLINE/READY with new Bun PIDs.

## Prevention

Optional Discord UX endpoints such as typing indicators must not gate request enqueue or acknowledgement. Any future pre-enqueue Discord API call should be wrapped with a non-fatal helper and covered by a regression test.
