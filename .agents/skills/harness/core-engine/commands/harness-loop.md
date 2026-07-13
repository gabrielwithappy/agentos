---
description: 하네스 자율 루프를 시작합니다. 자연어 프롬프트로 루프를 실행하며, 각 iteration은 새 CLI 프로세스(context reset 보장)로 동작합니다.
---
# /harness-loop

이 명령은 하네스 루프 엔진을 초기화하고 자율 주행 상태로 전환한다.

특정 MCP provider는 이 루프의 필수 구성요소가 아니다. 루프 코어는 `loop-state.md`, `HISTORY.md`, `events.jsonl`, 그리고 fresh-process CLI 호출만으로 동작한다.

## MCP Usage Plan

`harness loop`는 MCP-free가 기본이다. 일반 Codex profile 전환은 `.codex/profiles/config.with-mcp.toml` 전체를 `.codex/config.toml`로 교체할 수 있지만, 루프 실행은 active plan에 선언된 필요한 MCP만 Codex child argv로 렌더링한다.

선택 가능한 MCP와 목적은 아래 명령으로 확인한다.

```bash
python3 .agents/mcp/scripts/render-codex-mcp-config.py --list
```

active plan은 MCP 사용 여부를 두 곳에 남긴다.

- frontmatter-like line: `> mcp_servers: []` 또는 `> mcp_servers: [penpot]`
- section: `## MCP Usage Plan`

`## MCP Usage Plan`은 아래 항목을 포함한다.

- `Required MCPs`
- `Purpose`
- `When Used`
- `Preflight`
- `Expected Evidence`

선언이 없거나 빈 배열이면 Codex child는 `-c mcp_servers={}`로 실행된다. 선언이 있으면 registry helper가 해당 MCP만 `mcp_servers.<name>...` config override로 렌더링하고, unknown MCP는 child dispatch 전에 `mcp_selection_error`로 닫는다.

## MCP Lifecycle Verification

command MCP와 URL MCP는 lifecycle ownership이 다르다.

- command MCP
  선택된 MCP가 `mcp_servers.<name>.command`로 렌더링되면 Codex child process tree 안에서 시작된다. 하네스는 Codex child를 process group으로 띄우며 completion, timeout, interrupt, dispatch failure, stagnation closeout 뒤에 해당 process group이 남지 않는 계약을 검증한다.
- URL MCP
  `mcp_servers.<name>.url`은 이미 외부에서 실행 중인 endpoint에 attach하는 계약이다. 하네스는 URL MCP endpoint의 start/stop ownership을 갖지 않는다.
- external MCP health/preflight
  URL endpoint 가용성, token, browser, network, 외부 daemon 상태는 해당 active plan의 별도 preflight step에서 검증해야 한다. 루프 코어가 외부 MCP를 대신 기동하거나 종료하지 않는다.

Regression coverage: `.agents/skills/harness/run-all-tests/tests/test_mcp_lifecycle.py`는 fake Codex CLI와 fake command MCP process로 command MCP start/stop, Codex child timeout cleanup, MCP-free non-start 계약을 고정한다.

## Direct Execution Gate

직접 실행은 두 경로만 허용한다.

1. `docs/exec-plans/active/*.md` 경로가 프롬프트에 있고, 해당 문서에 `reviewed: true`가 존재한다.
2. 프롬프트가 strict `Execution Contract` fenced block 하나를 포함한다.

```text
[EXECUTION_CONTRACT]
Goal: ...
Scope: ...
Actions: ...
Verification: ...
Done When: ...
[/EXECUTION_CONTRACT]
```

- `Scope`는 대상 파일 또는 시스템 경계를 포함해야 한다.
- `Actions`는 실행 작업을 1개 이상 포함해야 한다.
- `Verification`은 검증 명령 또는 기대 결과를 1개 이상 포함해야 한다.
- `Done When`은 완료 조건을 1개 이상 포함해야 한다.
- long prompt는 별도 policy layer를 만들지 않는다. 필요한 경우 canonical `docs/exec-plans/active/YYYY-MM-DD-<slug>.md` active plan으로 물질화한다.

## Gate Outcomes

- `plan_normalized`
  strict `Execution Contract`는 active plan으로 정규화된다. 루프는 `review_required`로 멈추고 generated active plan path를 출력한다.
- `review_required`
  auto-normalized plan도 Rule 6 리뷰 게이트를 건너뛰지 않는다. `plan-reviewer` PASS와 `principle-auditor` CLEAN 후 `reviewed: true`가 붙기 전에는 실행 불가다.
- planning redirect
  reviewed active plan path도 없고 strict `Execution Contract`도 없으면 `planning_redirect` / `planning_required` 상태로 종료한다. 이때 child CLI는 호출되지 않고 `writing-plans` 경로를 안내한다.

## Runtime Diagnostic Vocabulary

루프는 diagnostic vocabulary를 `loop-state.md`, terminal `events.jsonl`, 그리고 `status`/`inspect`/`last`/`watch --once` operator output에 노출한다. 이 필드는 diagnostic-only다. 기존 completion promise, retry, loop stop, escalation 처리 분기는 변경하지 않는다.

- `outcome_code`
  closed values: `running`, `completed`, `blocked`, `retrying`, `stopped`
- `failure_class`
  closed values: `none`, `completion_contract`, `escalation_pending`, `timeout`, `stagnation`, `cli_error`, `launch`, `dispatch`, `output_last_message`, `iteration_budget`, `cd_limit`, `mcp_selection`, `planning_required`, `review_required`, `interrupted`
- `status_hint`
  operator가 다음 상태를 읽기 위한 짧은 human-readable hint다. 판단 소스는 기존 loop event와 stop_reason이며 새 recovery branch를 만들지 않는다.

Non-goals: No Hermes gateway, No dashboard, No scheduler, No provider transport, No external Hermes import. Hermes `runtime-core`/`operator-cli` 분석은 진단 어휘와 CLI-readable status surface로만 반영한다.

## Ralph Keep/Reject Contract

- keep
  `fresh-process iteration`, `small iteration discipline`, `feedback loop` 강조는 유지한다.
- reject
  `prd.json`, `progress.txt`, 별도 story/state artifact, dangerous direct execution, swallowed CLI failure, bare promise completion은 하네스 canonical path에 포함하지 않는다.
- direct execution note
  reviewed active plan 또는 strict `Execution Contract` 없는 자연어 direct execution은 planning redirect로 닫는다. 이 redirect는 `prd.json`/`progress.txt`/dangerous flag 기반 우회 경로를 안내하지 않는다.

## Completion Contract

완료는 `<promise>HARNESS_COMPLETE</promise>`만으로 충분하지 않다. completion 직전 응답에는 아래가 필요하다.

- 검증 명령/결과
- 최종 산출물 경로
- 마지막 checkpoint 요약

예시:

```text
검증 명령/결과: python3 -m pytest ... => passed
최종 산출물 경로: .agents/skills/harness/core-engine/harness_loop.py
마지막 checkpoint 요약: normalization gate + codex dispatch observability 반영
<promise>HARNESS_COMPLETE</promise>
```

### Harness Evolution Closeout

하네스 진화 작업(`harness-evolution` 스킬 사용, 관련 active plan path, 또는 prompt에 `harness evolution`/`harness-evolution` 문맥이 있는 경우)은 아래 evidence를 추가로 남겨야 한다.

- `strategy_artifact_path:` evolution strategy artifact 또는 관련 skill/plan 경로
- `final_conclusion_path:` intermediate checkpoint 위치와 구분되는 최종 결론 저장 위치
- `harness-architect: PASS`

예시:

```text
검증 명령/결과: python3 -m pytest ... => passed
최종 산출물 경로: .agents/skills/harness-evolution/SKILL.md, .agents/skills/harness/core-engine/harness_loop.py
마지막 checkpoint 요약: evolution strategy contract + focused regression 반영
strategy_artifact_path: .agents/skills/harness-evolution/SKILL.md
final_conclusion_path: docs/exec-plans/active/2026-04-11-harness-ralph-loop-evolution-strategy.md#final-closeout-evidence
harness-architect: PASS
<promise>HARNESS_COMPLETE</promise>
```

## Progress Reporting Contract

- child가 실행 중일 때 부모는 `loop-state.md`를 `iteration_started`에 고정하지 않는다.
- 부모 intermediate state의 SSOT는 `loop-state.md`다.
- structured progress/terminal evidence는 `events.jsonl`에 남긴다.
- `HISTORY.md`는 child가 이미 남긴 `[CHECKPOINT]`/`[HEARTBEAT]`를 감지하는 보조 surface로만 사용한다. synthetic heartbeat를 새로 기록하지 않는다.

### Trace Size Contract

- `events.jsonl`은 append-only 무한 증가 surface가 아니다.
- append 전에 active file byte size를 확인하고, limit 초과 예정이면 `events.<timestamp>.jsonl.gz`로 rotation한다.
- archive retention은 explicit `max archives` cap을 따르며, 오래된 gzip archive는 자동 삭제된다.
- `loop-state.md`의 요약 필드는 quoted single-line flatten 대신 multi-line block-safe format으로 저장해 사람이 읽기 쉬운 closeout/state inspection을 유지한다.

### Heartbeat Cadence

- child 실행 중 새 checkpoint가 없으면 부모는 약 5초 주기로 `progress_heartbeat`를 기록한다.
- heartbeat는 성공/실패 판정이 아니라 "child still running" 상태 반영이다.
- `progress_heartbeat`는 실제 stagnation과 다르다. 실제 정체 판정은 adapter가 `stagnation` 또는 timeout/dispatch failure로 surface할 때만 사용한다.
- child 진행 반영을 위해 `HISTORY.md` 전체를 매 poll 전량 재읽지 않는다. append-only delta만 읽어 incremental history reflection으로 유지한다.

### HISTORY Recent-Window Contract

- root `HISTORY.md`는 전체 raw ledger가 아니라 recent operational window다.
- older raw history는 `docs/project/reference/history/*.md` raw archive로 내려 보낸다.
- distilled intelligence는 `.agents/skills/harness/brain/lessons-learned.md`에 유지하고, raw archive와 역할을 섞지 않는다.
- Trigger 4가 발동하면 아래 deterministic compaction command를 사용한다.

```bash
python3 .agents/skills/harness/core-engine/scripts/compact_history.py \
  --history-path HISTORY.md \
  --archive-path docs/project/reference/history/2026-04-history-archive.md \
  --keep-recent-lines 200
```

### Parent Reflection Rules

- child가 `HISTORY.md`에 새 `[CHECKPOINT]`를 남기면 부모는 해당 headline을 `loop-state.md`의 `current_phase/current_task/current_step`에 즉시 반영한다.
- child checkpoint가 없더라도 부모는 heartbeat로 `current_task=Running child CLI`와 대기 중인 step을 갱신한다.
- 최종 closeout은 여전히 `loop_completed` 또는 분류 가능한 failure event로만 확정한다. progress heartbeat만으로 완료로 승격하지 않는다.

## Iteration Budget Gate

- budget SSOT는 기존 `LoopState.max_iterations` 하나만 사용한다.
- `iteration == max_iterations`이면 현재 iteration closeout은 허용하지만, closeout 뒤 다음 dispatch는 금지한다.
- `iteration > max_iterations`이면 루프는 즉시 중지하고 `loop-state.md`에 budget exhaustion을 남긴다.
- 새 budget counter, 별도 parser, 추가 telemetry 저장소는 도입하지 않는다.

## Codex Observability

Codex child failure phase는 아래 토큰으로 surface 된다.

- `launch`
- `dispatch`
- `output_last_message`
- `stagnation`
- `completion-after-quiet`

설명:

- `launch`
  child process spawn 자체가 실패한 경우
- `dispatch`
  stdin dispatch 단계에서 실패하거나 timeout이 발생한 경우
- `output_last_message`
  `--output-last-message` 파일이 비어 있거나 생성되지 않아 raw transcript fallback으로 닫힌 경우
- `stagnation`
  stdout/stderr/last-message 크기 모두 정지한 경우
- `completion-after-quiet`
  quiet/stagnation closeout 직전에 `--output-last-message`가 비어 있지 않아 마지막 assistant message를 완료 후보로 승격한 경우. raw transcript 또는 prompt echo에 포함된 completion promise만으로는 승격하지 않는다.

### Cleanup / Controlled Repro Contract

- Codex child는 기본적으로 MCP-free `--ignore-user-config --ephemeral -c mcp_servers={}` 계약으로 실행해 user config의 MCP transport를 붙이지 않는다.
- active plan의 `mcp_servers`가 비어 있지 않으면 `.agents/mcp.json` registry에서 필요한 MCP만 렌더링한다. 이 경로는 `.codex/profiles/config.with-mcp.toml` 전체를 읽지 않는다.
- Codex child는 process group으로 띄우고 timeout/dispatch failure/stagnation 시 process group termination으로 정리한다.
- interrupted-parent contract: 부모가 `SIGINT` 또는 `SIGTERM`으로 중단되면 active Codex child process group cleanup을 먼저 시도한 뒤 루프를 중지한다.
- stop evidence contract: parent interrupt cleanup은 `loop-state.md`의 `stop_reason`/`loop_stopped` evidence를 약화시키지 않는다. `SIGINT`는 `interrupted`, `SIGTERM`은 `signal:SIGTERM`으로 surface한다.
- `codex-last-message-*` 같은 temp file은 closeout 시 즉시 unlink 하며, persistent tmp trace를 남기는 대신 output에 cleanup evidence를 남긴다.
- quiet watchdog은 긴 초기 추론을 허용하도록 짧은 5초가 아니라 장시간 무진행 기준으로만 `stagnation`을 surface한다.
- controlled repro가 필요하면 전역 `/tmp` 대신 project-owned `TMPDIR`를 써서 tmp trace / last-message residue를 runtime-owned scope로 한정한다.
- cleanup evidence는 `completion-after-quiet`, `dispatch`, `stagnation` surface와 함께 읽는다. 남은 temp file 수가 아니라 owned tmp root의 delta를 우선 본다.

운영 확인:

- parent stop 후 orphan codex 확인: `ps -o pid=,pgid=,command= -C codex`
- loop state 확인: `grep -nE "stop_reason|last_event" .agents/traces/harness/loop-state.md`
- signal repro는 child가 active인 동안에만 수행하고, unrelated process는 같은 process group에 넣지 않는다.

주의:

- quoted `[ESCALATION]` 문자열은 단순 로그/붙여넣기일 수 있으므로 line-start marker만 escalation으로 취급한다.
- timeout은 만능 안전장치가 아니다. plan을 더 작게 쪼개 smaller iteration으로 유지하는 것이 우선이다.
- 장시간 작업이 예상되면 preflight check, intermediate checkpoint, smaller iteration으로 재계획하라.
- Codex child no-progress stagnation timeout은 `--stagnation-timeout <seconds>`로 명시적으로 조정한다. default is 60 seconds이며 전체 child CLI timeout 300초와 별개다.
- 권장 profile: standard code/doc iteration은 `--stagnation-timeout 60`, external dependency preflight는 `--stagnation-timeout 180`, image generation 또는 provider work는 `--stagnation-timeout 300`.

## 사용법

```
/harness-loop "자연어 프롬프트"
```

또는 CLI에서 직접:

```bash
./.agents/skills/harness/harness-loop.sh "자연어 프롬프트"
./.agents/skills/harness/harness-loop.sh "에이전트 하네스를 구축하라" --cli claude
./.agents/skills/harness/harness-loop.sh --resume
```

## 자연어 프롬프트 예시

```bash
./.agents/skills/harness/harness-loop.sh "docs/exec-plans/active/plan.md 계획을 단계별로 구현하라"
./.agents/skills/harness/harness-loop.sh "버그를 찾아서 수정하고 테스트까지 통과시켜라" --cli gemini
./.agents/skills/harness/harness-loop.sh "리팩터링 계획을 실행하고 HARNESS_COMPLETE 를 출력하라" --max-iterations 10
./.agents/skills/harness/harness-loop.sh "외부 의존성 preflight를 실행하라" --cli codex --stagnation-timeout 180
./.agents/skills/harness/harness-loop.sh --resume --cli claude
```

## 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--cli <이름>` | auto | gemini \| claude \| codex \| auto |
| `--max-iterations <N>` | 30 | 최대 반복 횟수 (0 = 무제한) |
| `--completion-promise <텍스트>` | HARNESS_COMPLETE | 완료 신호 문구 |
| `--stagnation-timeout <초>` | 60 | Codex child no-progress stagnation 판정 시간. must be > 0 |
| `--resume` | — | 기존 loop-state.md에서 재개 |
| `--dry-run` | — | CLI 호출 없이 loop-state.md만 초기화 |

## 완료 신호

에이전트가 아래를 출력하면 루프 종료:
```
<promise>HARNESS_COMPLETE</promise>
```

## 내부 구조

| 역할 | 파일 |
|------|------|
| canonical CLI wrapper | `.agents/skills/harness/harness-loop.sh` |
| 반복 제어 / 에스컬레이션 | `.agents/skills/harness/core-engine/harness_loop.py` |
| CLI별 fresh-process 호출 | `.agents/skills/harness/core-engine/cli_adapters.py` |
| 루프 상태 파일 | `.agents/traces/harness/loop-state.md` |

MCP/Serena는 선택적 보조 계층이며, 루프 자체의 성공 조건에는 포함되지 않는다.
