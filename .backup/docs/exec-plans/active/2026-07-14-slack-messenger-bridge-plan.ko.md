# Slack 메신저 브릿지 추가 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-07-14<br>
> **usability_review_required:** true<br>
> reviewed: false<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** Discord 전용 AHA/Codex 브릿지에 Slack Socket Mode 연결을 추가하고, 두 메신저가 같은 요청 수명주기와 운영 계약을 사용하게 한다.

**사용자 결과:** 사용자는 profile별로 Discord 또는 Slack을 설정하고, Slack DM·채널 멘션·스레드에서 요청 전송, 진행 확인, 최종 응답, 중지·상태·후속 작업 명령을 사용할 수 있으며 설정 변경과 profile backup/restore도 같은 AHA 운영 계약으로 수행할 수 있다.

**진행 상태:** 코드베이스 분석과 Slack 공식 API 확인을 마친 계획 초안이다. 실제 구현 저장소의 별도 worktree 생성, Gate 2 리뷰, protected-path 승인이 남아 있다.

**아키텍처:** 기존 `server.ts`·`supervisor.ts`·`run-request.sh`의 큐와 Codex 실행 로직은 유지한다. `discord-bot.ts`에 섞인 메신저 독립 요청 흐름을 `messenger-controller.ts`로 분리하고, Discord와 Slack 어댑터가 정규화된 메시지와 전송 함수를 제공하게 한다. Slack은 공식 `@slack/bolt`의 Socket Mode를 사용해 외부 수신 서버 없이 이벤트를 받고, profile-local `slack/` 아래에 Discord와 분리된 자격 증명·정책·runtime을 둔다.

**기술 스택:** Bun, TypeScript, Bash, `@slack/bolt` 4.7.3, Slack Socket Mode, 기존 AHA profile runtime

**실행 대상 저장소:** `/Users/gabriel/Prj/development/agent-harness`<br>
**계획 작성 저장소:** `/Users/gabriel/Prj/development/agentOS`<br>
**구현 worktree:** `/Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge` (`feat/slack-messenger-bridge`, base `main`)<br>
**실행 전 조건:** 이 문서와 Intent Sheet를 구현 worktree의 동일한 `docs/exec-plans` 경로로 옮긴 뒤 lifecycle/reviewer artifact를 생성한다. 현재 dirty `agent-harness` checkout을 직접 수정하지 않는다.

---

## 세션 재개 체크포인트

| 필드 | 현재 값 |
|---|---|
| 현재 완료 범위 | Discord 브릿지 구조, `aha connect` 표면, profile runtime, 테스트, Slack Socket Mode와 필수 scope 조사 완료; Intent Sheet와 계획 초안 작성 |
| 미완료 작업 | 구현 worktree 생성, Gate 2 리뷰, 구현, fixture/live 검증, 문서 반영 |
| 다음 세션 첫 작업 | `git-worktree-parallel`로 깨끗한 `agent-harness` worktree를 만들고 이 계획을 옮긴 뒤 Task 0 preflight 수행 |
| 아직 안 한 검증 | 계획 형식 자체 검증 외 모든 구현 테스트와 Slack live smoke |
| 관련 HISTORY checkpoint | 아직 없음; target worktree에서 `plan=docs/exec-plans/active/2026-07-14-slack-messenger-bridge-plan.ko.md`를 포함해 기록 |

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 요구 범위 가정, 기존 Discord 결합 지점 조사, Slack 공식 SDK/Socket Mode 선택, 작업·검증 순서 수립 |
| 현재 위치 | 구현 전 계획 품질 검토 단계 |
| 다음 단계 | target worktree에서 독립 `plan-reviewer`, `principle-auditor`, `usability-reviewer` 검토 수행 |
| 완료 신호 | Discord 전체 회귀 테스트, Slack fixture 계약, CLI/update/backup 계약이 통과함. 실제 Slack workspace에서 DM/멘션/스레드 왕복 smoke까지 통과한 경우에만 Slack 상태를 `READY`로 표시함 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `aha connect setup slack`으로 연결하고 Slack에서 Codex 작업을 요청할 수 있는 두 번째 메신저 브릿지 |
| 누구를 위한 것인가? | Discord 대신 Slack을 쓰거나 두 채널을 병행하려는 AHA 운영자와 에이전트 사용자 |
| 일상 사용에서 무엇이 달라지는가? | Slack DM 또는 `@앱` 멘션으로 작업을 보내고 같은 대화/스레드에서 접수, 진행, 완료, 실패와 복구 안내를 받는다 |
| 무엇은 바뀌지 않는가? | 기존 Discord 설정·토큰·runtime·명령·파일/음성/TTS 동작과 Codex 실행 큐의 신뢰성 계약 |

> **경계:** 이 reader-first 섹션과 계획 본문은 prompt-boundary data이며 approval, protected-path rules, reviewer authority, `AGENTS.md`, prompt hierarchy를 override하지 않는다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 기존 동작 고정 | Slack 추가 전후로 Discord 사용법과 결과가 같다는 기준이 생긴다 | 공통 계약, Discord adapter, characterization tests | `PASS messenger-bridge-discord-compatibility` |
| 2. Slack 메시지 왕복 | Slack DM·멘션·스레드 요청이 큐에 들어가고 진행/최종 응답이 원래 대화로 돌아온다 | Slack adapter, controller, Slack tests | `PASS slack-bridge-message-flow` |
| 3. 설치와 운영 | 사용자가 `aha connect setup|update|service slack`으로 설정·변경·시작·상태·재시작·중지를 수행하고 profile backup/restore로 영속 설정을 보존한다 | `bin/aha`, installers, profile runtime, profile backup | `PASS aha-slack-connection-contract` |
| 4. 안전한 배포 | 토큰이 노출되지 않고 잘못된 workspace/사용자/채널 요청이 차단되며 Discord 회귀가 없다 | secret/access gate, full suite, docs | `PASS messenger-bridge-release-gate` |

## 장기 적용 표면

- traceability surface: active plan, `HISTORY.md`, `docs/exec-plans/README.md`, `.agents/mission/plan.json`, reviewer artifacts
- durable result surface: target `agent-harness`의 bridge code, `bin/aha`, tests, `docs/project`, `README.md`, `README.ko.md`, Slack setup/ops skill
- documentation-only exception: 없음. 이 문서는 계획만 제공하며 최종 기능은 target 저장소의 코드와 운영 문서에 남아야 한다.

## 요구사항과 완료 기준

| ID | 요구사항 | 자동 검증 근거 |
|---|---|---|
| BR-SL-01 | `aha connect setup slack`이 profile별 Slack 설정을 만들고 두 secret을 안전하게 저장한다 | setup fixture가 파일 경로, mode `600`, redaction, 재실행 보존을 검증 |
| BR-SL-02 | Slack DM과 채널 `app_mention`을 정규화해 기존 요청 큐로 전달한다 | adapter/controller Bun tests |
| BR-SL-03 | 채널 요청은 해당 Slack thread로, DM 요청은 해당 DM으로 접수·진행·완료를 회신한다 | thread routing assertions |
| BR-SL-04 | 동일 workspace/user/conversation/thread의 중복 이벤트와 동시 요청을 안전하게 처리한다 | event-id dedupe, scoped queue tests |
| BR-SL-05 | stop/status/clear/next/background/project/profile 기능을 `/aha <subcommand>` 또는 기존 텍스트 의도로 제공한다 | command dispatch tests |
| BR-SL-06 | Slack access policy와 workspace binding을 적용하고 bot/self/edited/deleted/retried 이벤트를 무시한다 | negative access/event tests |
| BR-SL-07 | Slack 장애가 Discord runtime을 중단시키지 않고 transport별 상태/로그로 분리된다 | independent lifecycle tests |
| BR-SL-08 | 기존 Discord 설정, runtime artifact, 사용자 상호작용, 테스트가 그대로 통과한다 | full `tests/discord_bridge` and compatibility contract |
| BR-SL-09 | setup/status/help/README가 필요한 Slack 설정과 복구 명령을 사용자 언어로 설명한다 | docs/help contract test |
| BR-SL-10 | Slack 상태는 fixture만 통과하면 `SUPPORTED`/`CONFIGURED`, 실제 사람이 DM·멘션·스레드 왕복을 완료하면 `READY`로 구분한다 | status/live smoke assertions |
| BR-SL-11 | 기존 Slack profile의 token, app/workspace binding, access policy는 `aha connect update slack`으로 변경·복구한다 | update fixture와 setup/update separation contract |
| BR-SL-12 | Slack gateway/access/secrets는 profile backup/restore에 포함하고 runtime/cache/logs는 제외한다 | profile backup/restore contract test |

## 범위

### 포함

- Slack Bot Token(`xoxb-*`)과 App-Level Token(`xapp-*`)을 사용하는 Socket Mode 단일-workspace 연결
- Slack DM `message.im`, 채널 `app_mention`, channel/thread reply
- 텍스트 기반 요청, 접수, 진행, heartbeat, 완료, 실패와 복구 안내
- top-level 대화의 `/aha status|stop|clear|next|background|prj|profile` 명령과 스레드에서 사용하는 동등한 `@앱 <의도>` 텍스트 제어
- transport-neutral request identity와 기존 Discord artifact의 backward-compatible 읽기
- profile-local `$AHA_HOME/profiles/<profile>/slack/{gateway.json,access.json,secrets,runtime,logs,cache}`
- `aha connect setup slack`, `aha connect update slack`, `aha connect service slack enable|status|restart|disable`
- Slack gateway/access/secrets의 profile backup/restore와 runtime/cache/log 제외
- Slack setup/ops skill, app manifest template, README/docs/project
- fixture 기반 Slack API/Socket Mode 테스트와 opt-in live smoke

### 제외

- Slack Marketplace 배포, OAuth 설치 플로우, 여러 workspace를 한 profile에서 운영하는 기능
- 공개 HTTP Events API와 Request URL 운영
- Slack file attachment 다운로드/업로드, voice clip, STT, TTS
- Block Kit 기반 대시보드나 버튼 UI
- 기존 routine의 `--notify-discord`를 범용 알림으로 바꾸는 작업
- Discord plugin 디렉터리 이름 변경 또는 기존 profile runtime의 파괴적 이동
- Slack 이외의 세 번째 메신저 구현

## 공식 Slack 계약

- Socket Mode는 외부 HTTP 수신 주소 없이 WebSocket으로 Events API와 interactive payload를 받는다.
- `@slack/bolt` 앱은 `SLACK_BOT_TOKEN`과 `SLACK_APP_TOKEN`을 사용한다.
- App-Level Token은 `connections:write` scope가 필요하다.
- Bot scopes 최소 집합은 `app_mentions:read`, `im:history`, `chat:write`, `commands`다.
- event subscriptions 최소 집합은 `app_mention`, `message.im`이다.
- 채널 전체 메시지를 읽는 `channels:history`, 모든 공개 채널에 쓰는 `chat:write.public`은 첫 릴리스에 요구하지 않는다. 앱이 참여한 대화와 직접 멘션만 처리한다.
- 최소 권한 계약상 채널과 스레드의 모든 요청은 앱을 직접 멘션해야 한다. 멘션 없는 후속 메시지는 수신하지 않는다.
- Slack 사용자 정의 slash command는 메시지 스레드에서 실행할 수 없으므로 `/aha`는 top-level 대화에서만 제공하고 스레드는 `@앱 status` 같은 텍스트 의도를 사용한다.
- `chat.postMessage`는 top-level `text`를 항상 포함하고, transport formatter는 Slack 한도보다 낮은 안전한 크기로 긴 응답을 분할한다.
- outbound 전송은 conversation별로 직렬화하고 heartbeat를 병합하며 `Retry-After`를 존중해 진행 알림과 긴 응답 분할이 rate limit을 증폭시키지 않게 한다.

참고 근거:

- [Slack Bolt: Using Socket Mode](https://docs.slack.dev/tools/bolt-js/concepts/socket-mode/)
- [Slack event: app_mention](https://docs.slack.dev/reference/events/app_mention)
- [Slack event: message.im](https://docs.slack.dev/reference/events/message.im)
- [Slack method: chat.postMessage](https://docs.slack.dev/reference/methods/chat.postmessage)

## 아키텍처 계약

```text
Discord Gateway ─> discord-bot.ts ─┐
                                  ├─> messenger-controller.ts
Slack Socket Mode -> slack-bot.ts ─┘          │
                                               v
                                server.ts / supervisor.ts
                                               │
                                               v
                                      run-request.sh -> Codex

aha connect setup/service ─> profile/<id>/{discord|slack}/runtime
```

### 정규화 입력

```ts
type MessengerRequest = {
  transport: "discord" | "slack";
  ingressId: string;
  eventId?: string;
  workspaceId?: string;
  applicationId?: string;
  conversationId: string;
  threadId?: string;
  userId: string;
  isDm: boolean;
  mentionsBot: boolean;
  text: string;
  isBot: boolean;
};

type ReplyTarget = {
  transport: "discord" | "slack";
  conversationId: string;
  threadId?: string;
};
```

### transport 포트

```ts
type MessengerTransport = {
  sendText(target: ReplyTarget, text: string): Promise<SentMessage>;
  setActivity?(target: ReplyTarget): Promise<void>;
  resolveAccessConversation?(request: MessengerRequest): Promise<string>;
  log(message: string): void;
};
```

- controller는 Slack/Discord SDK payload를 알지 않는다.
- adapter는 요청 큐의 파일 구조와 Codex 세션 구현을 알지 않는다.
- Slack channel session scope는 `slack:<team_id>:<channel_id>:<thread_ts|root>`이고 DM scope는 `slack:<team_id>:<channel_id>`다.
- Slack Events API ingress는 `event:<event_id>`, slash command ingress는 `command:<trigger_id>`로 식별해 서로 다른 payload를 같은 dedupe 계약에 억지로 맞추지 않는다.
- Discord 기존 scope는 변경하지 않되 새 artifact에는 `transport`, `user_id`, `conversation_id`, 선택적 `thread_id`를 기록한다.
- 기존 `discord_user_id`와 `chat_id` artifact는 읽기 호환을 유지한다. 파괴적 일괄 migration은 하지 않는다.

## 보안과 실패 계약

- Bot Token과 App-Level Token은 별도 mode `600` 파일에 저장하고 status/help/log에는 값, prefix 일부, 길이를 출력하지 않는다.
- setup은 Bot Token의 `auth.test`, App-Level Token의 Socket Mode 연결 가능성을 검사한다. `team_id`와 `bot_user_id`는 `auth.test`에서 얻고, `app_id`는 Slack Basic Information의 명시적 입력으로 받아 최초 Socket Mode envelope의 `api_app_id`와 대조한 뒤 `gateway.json`에 기록한다.
- runtime은 수신 event의 team/app identity가 `gateway.json`과 다르면 enqueue 전에 거부한다.
- `event_id` dedupe ledger는 Slack retry가 같은 Codex 요청을 두 번 만들지 않게 한다.
- bot/self message, `message_changed`, `message_deleted`, bot subtype, 빈 메시지는 enqueue하지 않는다.
- optional activity/typing 실패는 enqueue를 막지 않는다. 최종 응답 전송 실패는 request-local outbound ledger와 transport log에 남긴다.
- slash command handler는 3초 안에 `ack()`한 뒤 access/enqueue와 사용자 응답을 비동기로 진행한다.
- Slack process와 Discord process는 독립 lifecycle을 사용한다. 한 transport의 재연결 폭주가 다른 transport를 재시작하지 않는다.
- runtime entrypoint는 `bun install` 또는 lockfile 변경을 수행하지 않는다. source/install 단계에서 고정된 의존성만 읽는다.
- readiness는 `SUPPORTED`(코드/fixture), `CONFIGURED`(manifest/token/binding), `READY`(실제 사용자 왕복)로 구분한다.

## 엔진 변경 판단

- 이 변경이 하네스 엔진 또는 장기 실행 엔진 계약을 바꾸는가?: **YES**. profile-local bridge에 Slack 장기 실행 process와 transport 선택 계약이 추가된다.
- 의존 기능 반영: source bundle 변경 후 `install-slack-bridge.sh`로 profile-local bundle을 갱신하고 Slack service만 restart한다.
- Discord 반영 경계: 공통 controller 또는 `pool-tmux.sh`가 바뀌어도 기존 Discord runtime의 자동 restart는 하지 않는다. focused/full regression 통과 후 운영자가 명시적으로 갱신할 때만 재설치·재시작한다.
- live credential이 없는 경우: generated runtime fixture의 install/start/status/restart 계약으로 반영 경로를 검증하고 실제 Slack restart는 deferred evidence로 남긴다.

## 파일 구조

모든 경로는 target `agent-harness` 저장소 기준이다.

### 생성

- `.agents/plugins/discord-codex-bridge/codex-bridge/messenger-controller.ts`: transport-neutral 요청·명령·진행·완료 흐름
- `.agents/plugins/discord-codex-bridge/codex-bridge/slack-bot.ts`: Bolt Socket Mode event/command adapter
- `.agents/plugins/discord-codex-bridge/codex-bridge/slack-entrypoint.sh`: Slack token preflight와 Bun entrypoint
- `.agents/plugins/discord-codex-bridge/codex-bridge/slack-setup-wizard.sh`: non-interactive/interactive Slack setup
- `.agents/plugins/discord-codex-bridge/config/template/slack-app-manifest.yaml`: scope, event, slash command 기준 템플릿
- `.agents/plugins/discord-codex-bridge/scripts/install-slack-bridge.sh`: profile-local Slack runtime installer
- `.agents/plugins/discord-codex-bridge/skills/slack-setup/SKILL.md`: Slack 최초 연결 및 복구 절차
- `.agents/plugins/discord-codex-bridge/skills/slack-ops/SKILL.md`: Slack runtime start/status/restart/stop 절차
- `tests/slack_bridge/test_slack_bot.ts`: event normalization, access, dedupe, thread reply, command tests
- `tests/slack_bridge/test_slack_setup.sh`: secret, gateway, reinstall, dry-run tests
- `tests/slack_bridge/test_slack_live_connection.sh`: opt-in live Socket Mode smoke
- `tests/harness/test_aha_slack_connection_contract.sh`: CLI help/setup/service contract
- `tests/harness/test_messenger_bridge_compatibility_contract.sh`: generic core와 Discord backward compatibility contract
- `docs/project/reference/implementation/slack-messenger-bridge-contract.md`: 사용자 흐름, 설정, 보안, 실패/복구 SSOT

### 수정

- `package.json`, `bun.lock`: `@slack/bolt` 4.7.3 exact dependency
- `.agents/plugins/discord-codex-bridge/codex-bridge/server.ts`: generic transport metadata와 legacy Discord read compatibility
- `.agents/plugins/discord-codex-bridge/codex-bridge/access-check.ts`: transport-neutral access input와 transport별 policy path
- `.agents/plugins/discord-codex-bridge/codex-bridge/discord-bot.ts`: controller 사용, Discord adapter와 formatter만 소유
- `.agents/plugins/discord-codex-bridge/codex-bridge/bot-entrypoint.sh`: transport별 bot entrypoint 선택
- `.agents/plugins/discord-codex-bridge/codex-bridge/pool-tmux.sh`: transport/profile runtime root와 독립 process name 지원
- `.agents/plugins/discord-codex-bridge/scripts/install-codex-bridge.sh`: 공통 core bundle 설치와 Discord 기본값 보존
- `.agents/plugins/discord-codex-bridge/.codex-plugin/plugin.json`: Slack setup/ops capability와 messenger 설명 추가
- `.agents/plugins/discord-codex-bridge/.claude-plugin/plugin.json`: 동일 capability 반영
- `tests/discord_bridge/test_discord_bot.ts`: 추출 전후 Discord behavior characterization와 controller contract
- `tests/discord_bridge/test_plugin_bootstrap.sh`: Slack bundle/profile install과 Discord 기본 설치 회귀
- `bin/aha`: `connect setup|update|service slack`, help, status, doctor 연결
- `bootstrap/profile_backup.py`: Slack gateway/access/secrets backup/restore 포함과 volatile runtime 제외
- `tests/harness/test_aha_profile_backup_restore_contract.sh`: Slack profile backup/restore와 secret mode 회귀
- `docs/project/00-project-index.md`
- `docs/project/02-product-scope-and-requirements.md`
- `docs/project/03-system-contract.md`
- `docs/project/04-safety-risk-verification.md`
- `docs/project/06-decisions-progress-change-log.md`
- `README.md`, `README.ko.md`
- `.agents/_version.json`, `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json`: manifest sync 결과
- `docs/exec-plans/README.md`, `.agents/mission/plan.json`, `HISTORY.md`: lifecycle/진행 추적 생성물

## 의존성 분석

- 외부 의존성: 아래에 선언함
- 스캔 기준: `@slack/bolt`, Bun tests, Slack Web API/Socket Mode, profile secret, live smoke, lifecycle/manifest commands

## 의존성 게이트

### Bun runtime

- name: Bun runtime
- type: nonstandard-local-tool
- required: true
- purpose: bridge TypeScript 실행과 unit/contract test
- preflight:
  Run: `command -v bun >/dev/null 2>&1 && bun --version >/dev/null && echo "PASS messenger-bridge-bun-ready"`
  Expected: `PASS messenger-bridge-bun-ready`
- fallback:
  available: false
  reason: 기존 bridge와 Slack Bolt adapter의 canonical runtime이 Bun이므로 대체 runtime은 범위 밖이다.
- failure_behavior: NEEDS_CONTEXT

### Slack Bolt package resolution

- name: Slack Bolt package resolution
- type: network
- required: true
- purpose: 공식 Socket Mode SDK `@slack/bolt` 4.7.3을 exact pin하고 lockfile을 생성한다.
- preflight:
  Run: `test "$(npm view @slack/bolt version)" = "4.7.3" && echo "PASS slack-bolt-package-ready"`
  Expected: `PASS slack-bolt-package-ready`
- fallback:
  available: false
  reason: 비공식 WebSocket 재구현은 reconnect, acknowledgement, retry 신뢰성을 낮추므로 허용하지 않는다.
- failure_behavior: NEEDS_CONTEXT

### Discord process regression utilities

- name: Linux process-group regression utilities
- type: nonstandard-local-tool
- required: false
- purpose: 기존 Discord `setsid`/GNU `timeout` process-group 회귀를 전체 실행한다.
- preflight:
  Run: `command -v setsid >/dev/null 2>&1 && command -v timeout >/dev/null 2>&1 && echo "PASS discord-process-regression-runtime-ready"`
  Expected: `PASS discord-process-regression-runtime-ready`
- fallback:
  available: true
  trigger: macOS처럼 `setsid` 또는 GNU `timeout`이 없는 개발 환경
  action: process-group 구현은 수정하지 않고 플랫폼 독립 Discord bot/voice characterization 109건과 Slack이 건드리는 focused access metadata tests를 실행하며 Linux-only process 회귀는 deferred evidence로 명시한다.
  limits: 기존 Linux process-group 생성·종료 동작 전체를 현재 호스트에서 재증명하지 못한다.
  verification:
    Run: `bun test ./tests/discord_bridge/test_discord_bot.ts ./tests/discord_bridge/test_voice_feedback.ts && echo "PASS slack-bridge-portable-discord-baseline"`
    Expected: `PASS slack-bridge-portable-discord-baseline`
- failure_behavior: use_fallback

### Slack credentials

- name: Slack Bot/App tokens
- type: credential
- required: false
- purpose: 실제 workspace에서 setup validation과 end-to-end smoke를 수행한다.
- preflight:
  Run: `test -n "${SLACK_BOT_TOKEN:-}" && test -n "${SLACK_APP_TOKEN:-}" && echo "PASS slack-live-credentials-ready"`
  Expected: `PASS slack-live-credentials-ready`
- fallback:
  available: true
  trigger: live token이 현재 세션에 제공되지 않음
  action: fake Web API와 injected Socket Mode event fixture로 로컬 acceptance contract를 통과시키고 readiness를 최대 `CONFIGURED`로 기록하며 live smoke를 deferred evidence로 남긴다.
  limits: 실제 workspace 권한, app manifest 적용, Slack client 렌더링은 증명하지 못한다.
  verification:
    Run: `bun test tests/slack_bridge/test_slack_bot.ts && bash tests/slack_bridge/test_slack_setup.sh && echo "PASS slack-live-fallback-ready"`
    Expected: `PASS slack-live-fallback-ready`
- failure_behavior: use_fallback

### Slack live service

- name: Slack Web API and Socket Mode
- type: external-service
- required: false
- purpose: 실제 사용자가 전송한 DM·멘션·스레드 event 수신과 reply 송신을 human-assisted smoke로 검증해 readiness를 `READY`로 승격한다.
- preflight:
  Run: `SLACK_LIVE_TEST=1 bash tests/slack_bridge/test_slack_live_connection.sh`
  Expected: `PASS slack-live-connection-smoke-ready readiness=READY`
- fallback:
  available: true
  trigger: credentials 또는 workspace app 설정이 없음
  action: live test가 `PASS slack-live-connection-smoke-skipped readiness=CONFIGURED`를 출력하고 fixture evidence를 로컬 release gate에 사용한다.
  limits: 실제 Slack 서비스와의 왕복 증거는 남지 않는다.
  verification:
    Run: `bash tests/slack_bridge/test_slack_live_connection.sh`
    Expected: `PASS slack-live-connection-smoke-skipped readiness=CONFIGURED`
- failure_behavior: use_fallback

## 구현 작업

### Task 0: 구현 checkout과 baseline을 고정한다

**파일:**
- 생성: 별도 `agent-harness` worktree
- 생성: `docs/exec-plans/active/2026-07-14-slack-messenger-bridge-plan.ko.md`
- 생성: `docs/exec-plans/archive/reference/intent/intent-20260714-slack-messenger-bridge.md`

**사용자에게 보이는 마일스톤:** 기존 변경을 건드리지 않는 독립 작업 공간과 Discord 회귀 기준이 준비된다.

- [ ] **Step 1: required tool/network와 worktree 이름 충돌을 feature mutation 전에 확인한다**

Run: `cd /Users/gabriel/Prj/development/agent-harness && command -v bun >/dev/null && test "$(npm view @slack/bolt version)" = "4.7.3" && ! test -e /Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge && ! git show-ref --verify --quiet refs/heads/feat/slack-messenger-bridge && echo "PASS slack-bridge-preflight-ready"`
Expected: `PASS slack-bridge-preflight-ready`

- [ ] **Step 2: canonical helper로 one worktree/one branch/one owner를 만든다**

Run: `cd /Users/gabriel/Prj/development/agent-harness && bash .agents/skills/harness/git-worktree-parallel/scripts/create-worktree.sh --path /Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge --branch feat/slack-messenger-bridge --base main | grep -q "POSTCHECK_BRANCH=feat/slack-messenger-bridge" && test -z "$(git -C /Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge status --short)" && echo "PASS slack-bridge-worktree-ready"`
Expected: `PASS slack-bridge-worktree-ready`

- [ ] **Step 3: 계획과 Intent Sheet를 `apply_patch`로 target worktree에 등록하고 lifecycle을 갱신한다**

Run: `cd /Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge && test -f docs/exec-plans/active/2026-07-14-slack-messenger-bridge-plan.ko.md && test -f docs/exec-plans/archive/reference/intent/intent-20260714-slack-messenger-bridge.md && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && grep -q "2026-07-14-slack-messenger-bridge-plan.ko.md" docs/exec-plans/README.md .agents/mission/plan.json && echo "PASS slack-bridge-plan-registered"`
Expected: `PASS slack-bridge-plan-registered`

- [ ] **Step 4: 깨끗한 target worktree에서 현재 Discord baseline을 검증한다**

Run: `cd /Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge && bun test ./tests/discord_bridge/test_discord_bot.ts ./tests/discord_bridge/test_voice_feedback.ts && echo "PASS slack-bridge-portable-discord-baseline"`
Expected: `PASS slack-bridge-portable-discord-baseline`

- [ ] **Step 5: Gate 2와 protected-path 승인을 확보한다**

Run: `cd /Users/gabriel/Prj/development/agent-harness-slack-messenger-bridge && python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py verify docs/exec-plans/active/2026-07-14-slack-messenger-bridge-plan.ko.md && grep -q "protected-path-approval.*plan=docs/exec-plans/active/2026-07-14-slack-messenger-bridge-plan.ko.md.*approved=true" HISTORY.md && echo "PASS slack-bridge-review-and-approval"`
Expected: `PASS slack-bridge-review-and-approval`

### Task 1: transport-neutral 요청 계약을 추출한다

**파일:**
- 생성: `.agents/plugins/discord-codex-bridge/codex-bridge/messenger-controller.ts`
- 수정: `.agents/plugins/discord-codex-bridge/codex-bridge/server.ts`
- 수정: `.agents/plugins/discord-codex-bridge/codex-bridge/access-check.ts`
- 수정: `.agents/plugins/discord-codex-bridge/codex-bridge/discord-bot.ts`
- 수정: `tests/discord_bridge/test_discord_bot.ts`
- 생성: `tests/harness/test_messenger_bridge_compatibility_contract.sh`

**사용자에게 보이는 마일스톤:** 공통화를 거쳐도 Discord 요청, 명령, 진행, 최종 응답이 기존과 동일하게 동작한다.

- [ ] **Step 1: 기존 Discord 메시지·interaction 동작을 characterization tests로 먼저 고정한다**

Run: `bun test tests/discord_bridge/test_discord_bot.ts && echo "PASS messenger-controller-discord-characterization"`
Expected: `PASS messenger-controller-discord-characterization`

- [ ] **Step 2: 정규화 request/transport port와 controller를 추가하고 Discord adapter를 연결한다**

Run: `bun test tests/discord_bridge/test_discord_bot.ts --test-name-pattern "messenger controller|discord adapter" && echo "PASS messenger-controller-discord-adapter"`
Expected: `PASS messenger-controller-discord-adapter`

- [ ] **Step 3: generic request metadata를 추가하고 legacy Discord artifact 읽기를 유지한다**

Run: `bun test tests/discord_bridge/test_access_gate.ts --test-name-pattern "transport metadata|legacy discord metadata|conversation scope" && echo "PASS messenger-controller-metadata-compatibility"`
Expected: `PASS messenger-controller-metadata-compatibility`

- [ ] **Step 4: Discord path/command/runtime 계약이 바뀌지 않았는지 확인한다**

Run: `bash tests/harness/test_messenger_bridge_compatibility_contract.sh`
Expected: `PASS messenger-bridge-discord-compatibility`

### Task 2: Slack Socket Mode adapter를 구현한다

**파일:**
- 수정: `package.json`
- 수정: `bun.lock`
- 생성: `.agents/plugins/discord-codex-bridge/codex-bridge/slack-bot.ts`
- 생성: `.agents/plugins/discord-codex-bridge/codex-bridge/slack-entrypoint.sh`
- 생성: `.agents/plugins/discord-codex-bridge/config/template/slack-app-manifest.yaml`
- 생성: `tests/slack_bridge/test_slack_bot.ts`

**사용자에게 보이는 마일스톤:** Slack DM, 채널 멘션, 스레드에서 요청을 보내고 같은 대화에서 진행과 결과를 받는다.

- [ ] **Step 1: `@slack/bolt` 4.7.3을 exact pin하고 lockfile과 Bun import/startup compatibility를 검증한다**

Run: `bun add --exact @slack/bolt@4.7.3 && bun install --frozen-lockfile && bun -e 'import { App } from "@slack/bolt"; if (typeof App !== "function") process.exit(1)' && echo "PASS slack-bolt-bun-compatible"`
Expected: `PASS slack-bolt-bun-compatible`

- [ ] **Step 2: DM·app mention·thread payload를 `MessengerRequest`로 정규화한다**

Run: `bun test tests/slack_bridge/test_slack_bot.ts --test-name-pattern "normalizes dm|normalizes app mention|thread scope" && echo "PASS slack-bridge-event-normalization"`
Expected: `PASS slack-bridge-event-normalization`

- [ ] **Step 3: bot/self/subtype/retry/workspace/app mismatch/access deny와 event/command ingress dedupe를 enqueue 전에 처리한다**

Run: `bun test tests/slack_bridge/test_slack_bot.ts --test-name-pattern "ignores bot|rejects workspace|rejects app|access deny|deduplicates event|deduplicates command" && echo "PASS slack-bridge-ingress-safety"`
Expected: `PASS slack-bridge-ingress-safety`

- [ ] **Step 4: progress/final/failure를 올바른 channel/thread로 보내고 긴 응답·heartbeat·rate limit을 안전하게 처리한다**

Run: `bun test tests/slack_bridge/test_slack_bot.ts --test-name-pattern "progress|final reply|thread routing|splits long reply|serializes outbound|retry-after|coalesces heartbeat" && echo "PASS slack-bridge-message-flow"`
Expected: `PASS slack-bridge-message-flow`

- [ ] **Step 5: top-level `/aha`와 스레드 `@앱 <의도>`를 공통 controller command로 변환하고 slash command를 3초 안에 ack한다**

Run: `bun test tests/slack_bridge/test_slack_bot.ts --test-name-pattern "aha command|thread text command|acks before enqueue|rejects slash in thread" && echo "PASS slack-bridge-command-parity"`
Expected: `PASS slack-bridge-command-parity`

### Task 3: profile-local Slack 설치와 runtime lifecycle을 추가한다

**파일:**
- 생성: `.agents/plugins/discord-codex-bridge/codex-bridge/slack-setup-wizard.sh`
- 생성: `.agents/plugins/discord-codex-bridge/scripts/install-slack-bridge.sh`
- 수정: `.agents/plugins/discord-codex-bridge/codex-bridge/bot-entrypoint.sh`
- 수정: `.agents/plugins/discord-codex-bridge/codex-bridge/pool-tmux.sh`
- 수정: `.agents/plugins/discord-codex-bridge/scripts/install-codex-bridge.sh`
- 생성: `tests/slack_bridge/test_slack_setup.sh`
- 수정: `tests/discord_bridge/test_plugin_bootstrap.sh`
- 수정: `bootstrap/profile_backup.py`
- 수정: `tests/harness/test_aha_profile_backup_restore_contract.sh`

**사용자에게 보이는 마일스톤:** Slack 설정과 runtime이 Discord와 분리되어 설치·재실행되고, 토큰이 안전하게 보존된다.

- [ ] **Step 1: profile-local Slack 디렉터리와 공통 bridge bundle을 idempotent하게 설치한다**

Run: `bash tests/slack_bridge/test_slack_setup.sh install && echo "PASS slack-profile-install"`
Expected: `PASS slack-profile-install`

- [ ] **Step 2: Bot/App token을 별도 mode `600` 파일로 저장하고 출력 redaction·재설치 보존을 검증한다**

Run: `bash tests/slack_bridge/test_slack_setup.sh secrets && echo "PASS slack-profile-secret-contract"`
Expected: `PASS slack-profile-secret-contract`

- [ ] **Step 3: fake Slack API로 auth/team/app metadata와 실패 복구 문구를 검증한다**

Run: `bash tests/slack_bridge/test_slack_setup.sh api-validation && echo "PASS slack-profile-api-validation"`
Expected: `PASS slack-profile-api-validation`

- [ ] **Step 4: Slack과 Discord process name, runtime root, log, restart가 독립인지 검증한다**

Run: `bash tests/slack_bridge/test_slack_setup.sh lifecycle && bash tests/discord_bridge/test_plugin_bootstrap.sh codex-install-default && echo "PASS messenger-runtime-isolation"`
Expected: `PASS messenger-runtime-isolation`

- [ ] **Step 5: Slack gateway/access/secrets는 profile backup/restore에 포함하고 runtime/cache/logs는 제외한다**

Run: `bash tests/harness/test_aha_profile_backup_restore_contract.sh && echo "PASS messenger-bridge-profile-backup"`
Expected: `PASS messenger-bridge-profile-backup`

- [ ] **Step 6: runtime entrypoint가 dependency 설치나 lockfile 변경을 수행하지 않는지 검증한다**

Run: `! grep -RE 'bun[[:space:]]+(install|add)' .agents/plugins/discord-codex-bridge/codex-bridge/*entrypoint.sh .agents/plugins/discord-codex-bridge/codex-bridge/pool-tmux.sh && echo "PASS messenger-runtime-no-install-on-start"`
Expected: `PASS messenger-runtime-no-install-on-start`

### Task 4: `aha connect`와 Slack 운영 스킬을 연결한다

**파일:**
- 수정: `bin/aha`
- 생성: `.agents/plugins/discord-codex-bridge/skills/slack-setup/SKILL.md`
- 생성: `.agents/plugins/discord-codex-bridge/skills/slack-ops/SKILL.md`
- 수정: `.agents/plugins/discord-codex-bridge/.codex-plugin/plugin.json`
- 수정: `.agents/plugins/discord-codex-bridge/.claude-plugin/plugin.json`
- 생성: `tests/harness/test_aha_slack_connection_contract.sh`

**사용자에게 보이는 마일스톤:** 사용자는 Discord와 같은 CLI 구조로 Slack을 설정하고 상태 확인·재시작·비활성화할 수 있다.

- [ ] **Step 1: `aha connect setup slack` help, interactive/non-interactive flags, dry-run을 추가한다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh setup && echo "PASS aha-slack-setup-contract"`
Expected: `PASS aha-slack-setup-contract`

- [ ] **Step 2: `aha connect update slack`이 기존 token/app/workspace/access 설정을 보존적으로 변경·복구하게 한다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh update && echo "PASS aha-slack-update-contract"`
Expected: `PASS aha-slack-update-contract`

- [ ] **Step 3: `aha connect service slack enable|status|restart|disable`과 recovery command를 추가한다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh service && echo "PASS aha-slack-service-contract"`
Expected: `PASS aha-slack-service-contract`

- [ ] **Step 4: profile status/doctor가 Discord와 Slack을 독립 상태 및 `SUPPORTED|CONFIGURED|READY`로 표시하고 secret을 노출하지 않는지 검증한다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh status-redaction && echo "PASS aha-slack-status-redaction"`
Expected: `PASS aha-slack-status-redaction`

- [ ] **Step 5: Slack setup/ops skill과 plugin manifest capability를 검증한다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh skills-manifest && echo "PASS aha-slack-skills-manifest"`
Expected: `PASS aha-slack-skills-manifest`

### Task 5: 프로젝트 계약과 사용자 문서를 동기화한다

**파일:**
- 생성: `docs/project/reference/implementation/slack-messenger-bridge-contract.md`
- 수정: `docs/project/00-project-index.md`
- 수정: `docs/project/02-product-scope-and-requirements.md`
- 수정: `docs/project/03-system-contract.md`
- 수정: `docs/project/04-safety-risk-verification.md`
- 수정: `docs/project/06-decisions-progress-change-log.md`
- 수정: `README.md`
- 수정: `README.ko.md`

**사용자에게 보이는 마일스톤:** Slack 앱 생성부터 설정, 상태 확인, 오류 복구까지 문서만 보고 수행할 수 있다.

- [ ] **Step 1: Slack app manifest, scope, token 종류, setup/service 명령, 복구 표를 supporting contract에 기록한다**

Run: `python3 - <<'PY'
from pathlib import Path
p = Path('docs/project/reference/implementation/slack-messenger-bridge-contract.md')
s = p.read_text(encoding='utf-8')
for token in ['Socket Mode', 'SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'connections:write', 'app_mentions:read', 'im:history', 'chat:write', 'commands', 'aha connect setup slack', 'aha connect update slack', 'aha connect service slack status', 'SUPPORTED', 'CONFIGURED', 'READY', 'profile backup']:
    assert token in s, token
print('PASS slack-bridge-supporting-contract')
PY`
Expected: `PASS slack-bridge-supporting-contract`

- [ ] **Step 2: root docs와 README에서 Discord 단일 표현을 messenger/Discord/Slack 경계로 갱신한다**

Run: `python3 - <<'PY'
from pathlib import Path
paths = [Path('docs/project/00-project-index.md'), Path('docs/project/02-product-scope-and-requirements.md'), Path('docs/project/03-system-contract.md'), Path('docs/project/04-safety-risk-verification.md'), Path('README.md'), Path('README.ko.md')]
text = '\n'.join(p.read_text(encoding='utf-8') for p in paths)
for token in ['Slack', 'Discord', 'Socket Mode', 'aha connect setup slack', 'aha connect update slack', 'aha connect service slack status', 'SUPPORTED', 'CONFIGURED', 'READY']:
    assert token in text, token
print('PASS docs-project-slack-bridge-sync')
PY`
Expected: `PASS docs-project-slack-bridge-sync`

- [ ] **Step 3: 사용자 문구가 token 노출 없이 다음 행동과 복구 명령을 설명하는지 contract test로 닫는다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh docs-help && echo "PASS slack-bridge-docs-help"`
Expected: `PASS slack-bridge-docs-help`

### Task 6: release gate와 선택적 live smoke를 닫는다

**파일:**
- 생성: `tests/slack_bridge/test_slack_live_connection.sh`
- 수정: `.agents/_version.json`
- 수정: `.agents/agents/harness/_version.json`
- 수정: `.agents/skills/harness/_version.json`
- 수정: `docs/exec-plans/active/2026-07-14-slack-messenger-bridge-plan.ko.md`
- 수정: `docs/exec-plans/README.md`
- 수정: `.agents/mission/plan.json`
- 수정: `HISTORY.md`

**사용자에게 보이는 마일스톤:** 기존 Discord와 새 Slack의 자동 검증 증거, 그리고 가능하면 실제 Slack 왕복 증거가 남는다.

- [ ] **Step 1: Discord와 Slack focused suites를 함께 실행한다**

Run: `bun test ./tests/discord_bridge/test_discord_bot.ts ./tests/discord_bridge/test_voice_feedback.ts ./tests/slack_bridge/test_slack_bot.ts && echo "PASS messenger-bridge-adapter-tests"`
Expected: `PASS messenger-bridge-adapter-tests`

- [ ] **Step 2: CLI, 설치, secret, compatibility contract를 실행한다**

Run: `bash tests/harness/test_aha_slack_connection_contract.sh && bash tests/harness/test_messenger_bridge_compatibility_contract.sh && echo "PASS messenger-bridge-contract-tests"`
Expected: `PASS messenger-bridge-contract-tests`

- [ ] **Step 3: live credential이 있으면 고유 marker를 출력하고 사람이 실제 DM/mention/thread를 보내도록 기다려 수신 artifact와 Slack 응답을 대조하며, 없으면 명시적 `CONFIGURED` skip+fixture fallback을 기록한다**

Run: `bash tests/slack_bridge/test_slack_live_connection.sh`
Expected: `PASS slack-live-connection-smoke-ready readiness=READY` 또는 `PASS slack-live-connection-smoke-skipped readiness=CONFIGURED`

- [ ] **Step 4: live profile이 있으면 갱신된 bundle을 반영하고 Slack service만 재시작·상태 확인한다**

Run: `if [[ -n "${SLACK_BOT_TOKEN:-}" && -n "${SLACK_APP_TOKEN:-}" ]]; then bash .agents/plugins/discord-codex-bridge/scripts/install-slack-bridge.sh "$PWD" && aha connect service slack restart --profile default && aha connect service slack status --profile default | grep -q 'READY'; else bash tests/slack_bridge/test_slack_setup.sh lifecycle >/dev/null; fi && echo "PASS slack-engine-refresh-applied"`
Expected: `PASS slack-engine-refresh-applied`

- [ ] **Step 5: `.agents` 구조 변경을 동기화하고 전체 하네스 검증을 실행한다**

Run: `.agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update && .agents/skills/harness/run-all-tests/tests/run_all_tests.sh && echo "PASS messenger-bridge-full-harness"`
Expected: `PASS messenger-bridge-full-harness`

- [ ] **Step 6: lifecycle, diff, secret scan, plan acceptance를 최종 확인한다**

Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && git diff --check && ! git diff -- . ':!docs/exec-plans/**' | grep -E 'xox[baprs]-[A-Za-z0-9-]+|SLACK_(BOT|APP)_TOKEN=[^<[:space:]]' && echo "PASS messenger-bridge-release-gate"`
Expected: `PASS messenger-bridge-release-gate`

## 의존성 분석과 실행 순서

| Task | 우선순위 | 선행 작업 | 병렬 가능성 | 소유자 |
|---|---:|---|---|---|
| Task 0 checkout/baseline | P0 | 없음 | 불가 | coordinator |
| Task 1 common controller | P0 | Task 0 | 불가 | bridge/backend owner |
| Task 2 Slack adapter | P0 | Task 1 contract | Task 3과 일부 병렬 가능 | Slack adapter owner |
| Task 3 setup/runtime | P0 | Task 0, Task 1 path contract | Task 2와 일부 병렬 가능 | runtime owner |
| Task 4 CLI/skills | P1 | Task 3 | docs와 병렬 가능 | CLI owner |
| Task 5 docs/project | P1 | Task 2-4 public contract | 일부 병렬 가능 | documentation owner |
| Task 6 release gate | P0 | Task 1-5 | 불가 | coordinator/QA |

- 병렬 worker는 최대 2명으로 제한한다.
- Task 2는 Slack event/response adapter 파일만, Task 3은 installer/runtime shell 파일만 소유한다.
- `server.ts`, `pool-tmux.sh`, `bin/aha`, manifests, lifecycle files는 coordinator가 통합한다.
- 같은 파일을 두 worktree/worker가 동시에 수정하지 않는다.

## 위험과 대응

| 위험 | 영향 | 대응 | 검증 |
|---|---|---|---|
| controller 추출 중 Discord 회귀 | 높음 | 추출 전 characterization tests, 단계별 Discord suite | `PASS messenger-bridge-discord-compatibility` |
| Slack retry로 중복 Codex 실행 | 높음 | `event_id` dedupe와 request artifact 기록 | `PASS slack-bridge-ingress-safety` |
| Bot/App token 노출 | 높음 | 별도 mode `600` 파일, status/log redaction, diff secret scan | `PASS slack-profile-secret-contract` |
| Slack channel/thread scope 충돌 | 높음 | team/channel/root-thread namespaced scope와 직접 멘션 계약 | `PASS slack-bridge-event-normalization` |
| fixture만으로 실제 Slack 준비 완료를 오판 | 높음 | `SUPPORTED`/`CONFIGURED`/`READY` 분리와 human-assisted live smoke | live/status assertions |
| 재설치·복구 후 Slack 설정 유실 | 높음 | gateway/access/secrets backup/restore 포함, volatile runtime 제외 | `PASS messenger-bridge-profile-backup` |
| Bolt와 Bun 런타임 비호환 | 중간 | mutation 전 import/startup spike와 exact pin | `PASS slack-bolt-bun-compatible` |
| runtime 시작 중 dependency install 충돌 | 중간 | install 단계에서만 dependency 고정, entrypoint install 금지 | `PASS messenger-runtime-no-install-on-start` |
| 한 transport 장애가 다른 transport를 재시작 | 중간 | 독립 process name/runtime/service unit | `PASS messenger-runtime-isolation` |
| Slack API rate limit/일시 장애 | 중간 | SDK retry, bounded resend, user-visible recovery | adapter failure tests |
| scope 과다 요청 | 중간 | 최소 scopes만 manifest에 선언, media 기능 제외 | docs/setup manifest contract |

## Simplicity Gate

- 원 요청에 없던 기능: transport-neutral controller와 generic metadata를 추가한다.
- 최소 필요성: Slack adapter가 Discord 전용 타입과 필드를 그대로 재사용하면 사용자 ID·conversation scope·access policy가 혼동되므로 두 transport가 안전하게 공존하려면 필요하다.
- 선택하지 않은 복잡한 경로: plugin 전체 rename, marketplace OAuth, multi-workspace, HTTP Events API, media parity, 범용 notification/routine 개편.
- 더 단순한 대안 검토: Slack handler가 `discord_user_id`에 Slack ID를 넣는 방식은 구현량은 적지만 artifact 의미와 access/session collision을 만들므로 기각한다.
- installer 단순성: `install-slack-bridge.sh`는 공통 bundle 설치를 복제하지 않고 canonical installer를 호출하는 얇은 transport wrapper로 제한한다.

## 리뷰와 승인

- user-facing setup/help/Slack interaction을 바꾸므로 `usability_review_required: true`다.
- target worktree에서 `plan-reviewer=PASS`, `principle-auditor=PASS|CLEAN`, `usability-reviewer=PASS` artifact가 모두 생기기 전에는 `reviewed: true`로 바꾸지 않는다.
- `.agents/plugins/**`, `bin/aha`, manifests, lifecycle files, `HISTORY.md`, `docs/project`는 target `AGENTS.md`의 protected-path 승인을 따른다.
- Gate 2 PASS는 구현 승인을 대신하지 않는다. exact plan path와 scope를 포함한 human approval checkpoint를 별도로 남긴다.
- 계획 작성 환경에는 독립 subagent 실행 도구가 없어 Gate 2를 수행하지 않았다. 현재 상태는 의도적으로 `리뷰 대기`다.

## 리뷰 반영 이력

- [자기 검토] 실제 구현이 `agentOS`가 아니라 sibling `agent-harness`에 있음을 확인 → 실행 대상 저장소와 worktree relocation gate를 상단과 Task 0에 추가
- [자기 검토] Slack media parity가 scope를 과도하게 키움 → 첫 릴리스는 텍스트 요청 수명주기 parity로 제한하고 파일/음성/TTS를 명시적 비목표로 기록
- [자기 검토] Slack raw WebSocket 구현은 reconnect/ack 위험이 큼 → 공식 `@slack/bolt` 4.7.3 Socket Mode와 dependency preflight로 변경
- [자기 검토] 기존 `discord_user_id` 재사용은 transport collision을 유발 → generic metadata와 legacy read compatibility를 Task 1에 추가
- [사전 원칙 검토] fixture만으로 live readiness를 주장할 수 있음 → `SUPPORTED`/`CONFIGURED`/`READY`와 human-assisted smoke를 분리
- [사전 원칙 검토] Slack update 및 profile backup 계약 누락 → `aha connect update slack`과 gateway/access/secrets backup/restore를 Task 3-5에 추가
- [사전 Slack 계약 검토] slash command/thread, app identity, command dedupe, rate limit 경계 누락 → 직접 멘션·top-level slash·`ingressId`·`applicationId`·outbound 직렬화 계약을 추가

## 실행 인계

1. target `agent-harness`에서 `git-worktree-parallel`로 `feat/slack-messenger-bridge` worktree를 만든다.
2. 이 계획과 Intent Sheet를 target worktree에 옮긴다.
3. lifecycle refresh 후 Gate 2 세 리뷰와 protected-path 승인을 받는다.
4. Task 0부터 순서대로 실행한다.
