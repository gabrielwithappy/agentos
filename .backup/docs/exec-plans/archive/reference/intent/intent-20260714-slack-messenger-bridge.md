# Intent Sheet: Slack 메신저 브릿지 추가

**날짜:** 2026-07-14<br>
**요청자 의도 요약:** Discord만 지원하는 AHA/Codex 메신저 브릿지에 Slack을 동등한 연결 선택지로 추가한다.

## 가설

> 메신저별 이벤트와 응답 처리를 공통 요청 수명주기에서 분리하고 Slack Socket Mode 어댑터를 추가하면, 기존 Discord 동작을 깨뜨리지 않으면서 사용자가 Slack에서도 동일한 텍스트 기반 에이전트 작업 흐름을 사용할 수 있을 것이다.

## 사용자 응답 부재 시 적용한 가정

- 주 목적은 Discord를 대체하는 것이 아니라 Discord와 Slack을 동등한 연결 선택지로 제공하는 것이다.
- 공통화 대상은 접근 통제, 요청 큐, 세션, 진행 알림, 최종 응답, 중지/상태/후속 작업 명령이다.
- 첫 Slack 릴리스는 텍스트, DM, 채널 멘션, 스레드 응답, 운영 명령을 지원한다.
- 채널과 스레드 요청은 최소 권한을 유지하기 위해 매 요청마다 앱을 직접 멘션한다. 사용자 정의 `/aha` slash command는 Slack 제약상 top-level 대화에서만 사용하고, 스레드 제어는 `@앱 status` 같은 텍스트 의도를 사용한다.
- Slack 파일 첨부, 음성 입력, TTS 출력은 첫 릴리스의 비목표다. Discord의 기존 파일/음성/TTS 기능은 유지한다.
- Slack은 외부 HTTP 수신 주소가 필요 없는 Socket Mode를 사용한다.
- fixture 검증은 `SUPPORTED`/`CONFIGURED`를 증명하고, 실제 workspace에서 사람이 DM·멘션을 전송한 왕복 smoke만 `READY`를 증명한다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?

- [ ] Run: `bun test ./tests/discord_bridge/test_discord_bot.ts ./tests/discord_bridge/test_voice_feedback.ts ./tests/slack_bridge/test_slack_bot.ts && echo "PASS messenger-bridge-adapter-tests"` Expected: `PASS messenger-bridge-adapter-tests`
- [ ] Run: `bash tests/harness/test_aha_slack_connection_contract.sh && echo "PASS aha-slack-connection-contract"` Expected: `PASS aha-slack-connection-contract`
- [ ] Run: `bash tests/harness/test_messenger_bridge_compatibility_contract.sh && echo "PASS messenger-bridge-discord-compatibility"` Expected: `PASS messenger-bridge-discord-compatibility`
- [ ] Run: `bash tests/harness/test_aha_profile_backup_restore_contract.sh && echo "PASS messenger-bridge-profile-backup"` Expected: `PASS messenger-bridge-profile-backup`
- [ ] Run: `bash tests/slack_bridge/test_slack_live_connection.sh` Expected: credential 부재 시 `PASS slack-live-connection-smoke-skipped readiness=CONFIGURED`, 실제 사람이 DM·멘션·스레드 왕복을 완료하면 `PASS slack-live-connection-smoke-ready readiness=READY`
- [ ] Run: `.agents/skills/harness/run-all-tests/tests/run_all_tests.sh && echo "PASS messenger-bridge-full-harness"` Expected: `PASS messenger-bridge-full-harness`
- [ ] Run: `git diff --check && echo "PASS messenger-bridge-diff-check"` Expected: `PASS messenger-bridge-diff-check`

*판단자가 누구든 동일한 결과를 내야 한다. 자격 증명 부재는 로컬 계약 검증 실패가 아니지만 `READY` 증거도 아니다. 완료 보고는 자동 검증 결과와 실제 workspace readiness를 구분한다.*

## 범위 제약 (Scope Fence)

- 포함: `agent-harness`의 메신저 브릿지 공통 요청 계약, Slack Socket Mode 어댑터, profile-local Slack 설정/secret/runtime, `aha connect setup|update|service slack`, Slack profile backup/restore, Slack 운영 스킬, 테스트와 운영 문서
- 제외: `agentOS` 공개 배포 코드 변경, Discord 기능 제거, Slack OAuth 다중 워크스페이스 배포, 공개 HTTP Events API, 파일/음성/TTS, Slack Block Kit UI, 기존 routine의 Discord 알림을 Slack으로 일반화하는 작업

## 기술 스택 제약

- 기존 Bun/TypeScript/Bash 구조와 profile-local `$AHA_HOME` 경계를 유지한다.
- Slack 공식 JavaScript 프레임워크 `@slack/bolt` 4.7.3을 exact pin하고 Socket Mode를 사용한다.
- Slack Bot Token과 App-Level Token은 로그/상태/계획 문서에 출력하지 않고 각각 mode `600` secret 파일로 저장한다.
- 기존 Discord request artifact와 설정은 파괴적으로 마이그레이션하지 않는다.
- runtime 시작 경로는 `bun install`을 실행하지 않는다. 의존성 설치와 lockfile 고정은 source/install 단계에서 한 번만 수행한다.

## Worktree Decision

- 필요 여부: 필요
- 이유: 실제 구현 저장소 `/Users/gabriel/Prj/development/agent-harness`의 현재 checkout에 기존 미완료 변경이 있으므로 격리된 worktree에서 구현해야 한다.
- ownership: `git-worktree-parallel` 사용, one worktree = one branch = one owner, 예시 branch `feat/slack-messenger-bridge`

## 우선순위

- 프로덕션 수준의 안정성과 기존 Discord 회귀 방지 우선
- Slack 텍스트 기반 핵심 흐름을 먼저 완성하고 미디어 기능은 별도 계획으로 남긴다.

## 근거 위치

- 실제 구현 소유 저장소: `/Users/gabriel/Prj/development/agent-harness`
- 현재 Discord transport: `.agents/plugins/discord-codex-bridge/codex-bridge/discord-bot.ts`
- 공통 요청 런타임: `.agents/plugins/discord-codex-bridge/codex-bridge/server.ts`, `supervisor.ts`, `run-request.sh`
- CLI 연결 표면: `bin/aha`
- 회귀 테스트: `tests/discord_bridge/`
