---
name: agent-token-info
description: >
  Use when the user wants to check agent token readiness, API usage quotas, or usage limits without exposing raw secrets. 
  Typical prompts: "토큰정보 확인", "토큰 상태 봐줘", "token ready?", "현재 루틴의 token info 확인", "실행 usage 확인", "주간 리셋시간 알려줘".
---

# agent-token-info — 에이전트 토큰 및 한도 정보 확인

## Goal

Confirm the current agent token surface, live API usage-reporting path, and reset timestamp (if applicable) without printing raw token material.

## What to check

Use the smallest verification that answers the request.
For transport/gateway token readiness (e.g. Discord bot connection):

```bash
aha connect setup discord --profile default --yes
aha connect service discord status --profile default
```

If the question is specifically about API execution usage, limits, or weekly/5-hour reset timing (like Codex limits), run the dedicated status report script:
```bash
./bin/codex-status-report
```
This script will output the exact usage percentage, reset times, and model information. You can also fall back to running `codex exec --json "echo 'ping'"` if the report script fails.

## Interpretation

- `supported`: the repository/runtime has a documented contract for this token surface
- `configured`: the current profile docs and config describe the token flow
- `ready`: the live runtime and preflight evidence confirm it now
- `usage-visible`: a fresh execution run returned usage information in the current turn
- If the user is asking about resuming work after a limit reset, treat the reset timestamp as evidence only and also surface the next safe action from the active plan checkpoint or `HISTORY.md next_action=`.

Do not claim `ready` unless you ran a fresh verification in the current turn.

## Response shape

Reply briefly with:

1. The exact `Codex 상태 브리핑` block outputted by the report script, so the user can see all limits, model info, and streaks.
2. The current transport state (e.g. `Discord bridge: configured/ready`)
3. Next action only if limits are hit or recovery is needed.
4. If a limit reset is the reason for the question, include the next session's first task when the active plan checkpoint already recorded it.

## Safety

- Never print raw tokens, refresh tokens, secret file contents, or full secret env values
- Prefer focused status commands over broad output
- If token recovery looks needed, say so explicitly and stop at a short confirmation question if the recovery path is ambiguous
