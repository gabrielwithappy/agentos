---
name: harness-loop
description: 자연어 프롬프트로 하네스 루프를 백그라운드 실행하는 스킬
---

# harness-loop

## When to use

사용자가 다음 중 하나를 요청할 때 이 스킬을 사용하라:
- "harness-loop 실행"
- "루프 시작"
- "harness loop"
- "/harness-loop `<프롬프트>`"
- "랄프 루프로 해"
- "랄프로 실행해"
- 하네스 자율 루프를 시작하고 싶을 때

## 실행 방법

Bash 도구로 canonical 엔트리포인트 `.agents/skills/harness/harness-loop.sh`를 백그라운드 실행한다:

```bash
./.agents/skills/harness/harness-loop.sh "<프롬프트>" &
echo "PID: $!"
```

또는 필요하면 임시 파일로 출력을 캡처하는 방식:

```bash
./.agents/skills/harness/harness-loop.sh "<프롬프트>" >/tmp/harness-loop.out 2>&1 &
echo "PID: $! | 출력 캡처: /tmp/harness-loop.out"
```

### 실행 확인

백그라운드 실행 후 PID와 state/events 확인 경로를 사용자에게 안내하라.

```bash
# 루프 상태 확인
cat .agents/traces/harness/loop-state.md
```

### Operator Status Vocabulary

`status`, `inspect`, `last`, `watch --once`는 `outcome_code`, `failure_class`, `status_hint`를 표시한다. 이 diagnostic vocabulary는 diagnostic-only이며 루프의 완료, 중지, retry, escalation 동작을 바꾸지 않는다.

- `outcome_code`: `running`, `completed`, `blocked`, `retrying`, `stopped`
- `failure_class`: `none`, `completion_contract`, `escalation_pending`, `timeout`, `stagnation`, `cli_error`, `launch`, `dispatch`, `output_last_message`, `iteration_budget`, `cd_limit`, `mcp_selection`, `planning_required`, `review_required`, `interrupted`
- `status_hint`: 운영자가 현재 상태를 해석하기 위한 짧은 안내

Non-goals: No Hermes gateway, No dashboard, No scheduler, No provider transport.

## 옵션 상세

옵션 및 플래그 전체 목록은 아래를 참조하라 (내용 복제 금지):

→ `.agents/skills/harness/core-engine/commands/harness-loop.md`
