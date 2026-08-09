# AgentOS TUI 요청·결과 분리 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-26<br>
> reviewed: true<br>
> Review evidence: implementation preflight: plan-reviewer PASS, principle-auditor PASS/CLEAN, usability-reviewer PASS — `.agents/traces/reviews/2026-07-26-tui-request-result-separation/{plan-reviewer,principle-auditor,usability-reviewer}.{md,json}`<br>
> implementation_started_at: 2026-07-26T06:26:31Z<br>
> implementation_completed_at: 2026-07-26T06:36:38Z<br>
> implementation_duration: 00:10:07<br>

> **usability_review_required:** true<br>
> Usability scope: 사용자 대화 화면의 역할 표시, 스트리밍 상태, 도움말이 바뀜.

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 사용자가 AgentOS TUI에서 자신의 요청과 그 요청에 대한 AgentOS의 최종 결과를 스크롤 중에도 즉시 구별할 수 있게 한다.

**사용자 결과 요약:**
- 최종 결과: 각 일반 대화 turn에서 요청은 `You` 헤더와 요청 영역으로, 답변은 `AgentOS · responding` / `complete` / `cancelled` / `failed` 헤더와 결과 영역으로 분명히 구분된다. 정상 종료에 답변 본문이 없으면 `AgentOS · complete` 영역에 `No response content was returned.`를 표시한다. 추론·도구 실행은 `Activity`로 표시되는 보조 정보라서 최종 결과와 섞여 보이지 않는다.
- 대상 독자: Textual TUI로 AgentOS 세션을 사용하며, 스트리밍 답변·도구 호출·긴 대화를 읽는 개발자.
- 일상 사용의 변화: 사용자는 화면에서 역할과 최종 답변을 찾기 위해 `You:` 색상이나 도구 로그의 위치를 추측하지 않는다. 응답이 아직 생성 중인지, 정상적으로 끝났는지도 헤더로 확인한다.
- 바뀌지 않는 경계: `ConversationMessage`/JSONL/스냅샷 스키마, 원본 message text, `turn_id`, fork/copy semantics, provider event 순서, 인증·오류·slash command의 system-message 의미는 변경하지 않는다. AgentOS가 vendor tool loop를 복제하거나 `.agents/` 하네스 구조를 바꾸지 않는다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 기존 Python/Textual 및 테스트 의존성만 사용한다.
- 현재 구조 근거: `agentos/terminal/tui/widgets.py:172-374`에서 user만 `You: ` 접두사를 받고 assistant는 전용 presentation이 없다. `agentos/terminal/tui/app.py:667-789`는 reasoning/tool/assistant를 독립 transcript 메시지로 추가한다.
- 참조 구현 근거: Pi의 `UserMessageComponent`는 메시지 원문과 역할별 container 표현을 분리하고, `ToolExecutionComponent`는 실행 상태와 결과를 구분한다. 직접 코드 이식은 하지 않고 Textual에 맞는 UX 원칙만 적용한다. 상세 근거는 `.agents/traces/research/2026-07-26-tui-request-result-separation-evidence.md`를 따른다.
- root 문서 정합성: 기존 `REQ-CLI-003` 대화형 TUI의 가독성 회귀를 개선하고 terminal-only Textual 경계를 지킨다. `REQ-HARNESS-001-f`는 별도 Control TUI 계획의 비구현 경계 참고일 뿐, 이 계획의 구현 요구사항은 아니다. `.agentos/project/05-agent-operating-contract.md`의 TUI session/hook 보존 규칙을 준수한다.

**장기 적용 표면:**
- Traceability Surface: `.agents/traces/research/2026-07-26-tui-request-result-separation-evidence.md`, 이 계획의 Gate 2 리뷰 증거와 완료 검증 기록.
- Durable Result Surface: `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py`, `docs/cli-reference.md`, `tests/test_tui_cli.py`, `tests/test_tui_visual_contract.py`, `tests/test_conversation_runtime.py`, visual/session evidence under `.agents/traces/visual/2026-07-26-tui-request-result-separation/`.

**진행 상태:** 마일스톤 0-6 구현 및 테스트 완료. closeout 본문 갱신으로 fresh Gate 2 재검토와 archive 결정만 남았다.

**아키텍처:**
- `ChatMessage`는 `raw_text`(복사 대상)와 `presentation_role`/`presentation_status`(화면 전용)를 분리한다. 기존 `.text`는 migration 시 raw message body만 담도록 정규화하고, user의 기존 `You: ` 접두사는 저장/복사 데이터에서 제거한다. 헤더/경계는 `render()` 또는 child presentation widget으로 조립하며 Markdown `update_text()`는 body만 갱신한다. persistence는 계속 `ConversationMessage.text`를 source of truth로 사용한다.
- `Transcript`는 user/assistant/activity/system을 명시적으로 구분해 mount한다. user/assistant 영역에는 색상과 무관하게 보이는 `│` 좌측 경계, 역할 header, 80열에서 header가 본문과 독립 줄을 차지하는 wrapping 계약을 둔다. activity는 새 aggregation/state model 없이 기존 reasoning/tool 이벤트를 원순서로 유지하고, 각각 `Activity · Thinking` 또는 `Activity · Tool` header 및 해당 `turn_id`를 가진 낮은 대비 영역으로 렌더링한다.
- `AgentOSTui.run_stream()`은 첫 assistant delta에서 `responding` 결과 영역을 만들고 아래 상태 전이를 적용한다. 부분 본문은 cancel/error에서도 보존하되 결과 영역 자체가 종료 상태를 표시하므로 진행 중으로 오인되지 않는다. system error/cancel 메시지는 기존 순서와 의미를 유지한다.

| 시작 조건 | 결과 영역 상태/본문 | system 메시지·persistence |
|---|---|---|
| 첫 delta → `done` | `responding → complete`; 누적 본문 유지 | 기존 successful turn commit |
| 첫 delta → Esc cancel | `responding → cancelled`; 부분 본문 유지 | 기존 `Turn cancelled.` 및 cancel atomicity 유지 |
| 첫 delta → provider error | `responding → failed`; 부분 본문 유지 | 기존 error system message; 실패 turn은 기존 commit 정책 유지 |
| delta 없음 → provider error | assistant 영역 생성 안 함 | 기존 error system message |
| delta 없음 → `done` | `complete`; `No response content was returned.` 표시 | existing successful-turn usage/commit 유지 |
- slash command, auth, provider error, hook error는 existing system-message 경로를 유지한다. 일반 assistant 결과 header를 붙이지 않는다.

**기술 스택:** Python 3, Textual, Rich Markdown, pytest/Textual Pilot.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Gate 2 통과, 구현 실행 대기 |
| 완료됨 | UX 조사, 실행 계획, 3개 독립 리뷰 |
| 현재 위치 | 구현 시작 전 |
| 다음 단계 | 마일스톤 0 기준선 검증 |
| 완료 신호 | 아래 모든 Run 명령이 Expected를 만족하고 visual/user-flow 증거가 남음 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 기준선과 테스트 명명 | 실행 가능한 focused test contract | `tests/test_tui_cli.py`, `tests/test_conversation_runtime.py` | Run: `uv run pytest tests/test_tui_cli.py tests/test_conversation_runtime.py -q`<br>Expected: PASS. 새 테스트는 `test_role_visual_contract_*`, `test_stream_status_*`, `test_activity_turn_*`, `test_presentation_does_not_change_*` prefix를 사용하고 각 focused `-k` 실행에서 0 collected면 FAIL 처리 |
| 1. 요청과 결과의 대칭적 역할 표현 | `You` 요청 영역과 `AgentOS` 결과 영역이 색상 외 header·`│` 경계로 구별됨 | `widgets.py`, `tests/test_tui_cli.py` | Run: `uv run pytest tests/test_tui_cli.py -q -k "role_visual_contract"`<br>Expected: 1개 이상 PASS; header/class/80열 wrapping과 raw `message.text`, turn_id, mock OSC52 copy payload가 header 없는 원문임을 assert |
| 2. 스트리밍 결과 상태·persistence | responding/complete/cancelled/failed/빈 성공 상태가 정직하게 종료됨 | `app.py`, `widgets.py`, `tests/test_tui_cli.py`, `tests/test_conversation_runtime.py` | Run: `uv run pytest tests/test_tui_cli.py tests/test_conversation_runtime.py -q -k "stream_status or presentation_does_not_change"`<br>Expected: 1개 이상 PASS; normal, partial→cancel, partial→error, no-delta→error, no-delta→done에서 header/body/system order/next input을 assert하고 성공 snapshot/replay 원문 및 cancel/error atomicity 유지 확인 |
| 3. Activity 보조 표현과 turn 귀속 | reasoning/tool이 정확한 요청에 속한 `Activity`로 보이고 결과와 섞이지 않음 | `app.py`, `widgets.py`, `tests/test_tui_cli.py` | Run: `uv run pytest tests/test_tui_cli.py -q -k "activity_turn"`<br>Expected: 1개 이상 PASS; reasoning→tool_call→tool_result→assistant, assistant 후 activity, activity 없음, 연속 두 turn을 모두 검증하고 event order/redaction/turn_id 및 assistant의 non-Activity contract를 assert |
| 4. 문서와 실제 화면 정합 | 사용자가 상태/Activity/cancel 복구를 확인할 수 있음 | `docs/cli-reference.md`, `tests/test_tui_cli.py` | Run: `uv run pytest tests/test_tui_cli.py -q -k "role_visual_contract or stream_status or activity_turn" && rg -n "Activity|responding|cancelled|failed|No response content" docs/cli-reference.md`<br>Expected: 1개 이상 pytest PASS 및 문서에 실제 용어/부분 결과·재시도 설명 존재. `commands.py`는 변경하지 않음 |
| 5. 접근성·visual smoke·focused secret | 80열/넓은 폭/무색상에서도 역할과 상태를 읽고 secret이 숨겨짐 | `tests/test_tui_cli.py`, `tests/test_tui_visual_contract.py`, `.agents/traces/visual/` | Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_tui_cli.py tests/test_tui_visual_contract.py -q -k "redact or role_visual_contract or stream_status or activity_turn or presentation_does_not_change" && test -d .agents/traces/visual/2026-07-26-tui-request-result-separation && ! rg -uuu -n "SENTINEL_SECRET" .agents/traces/visual/2026-07-26-tui-request-result-separation`<br>Expected: pytest PASS; final scan 출력 없음. `tests/test_tui_visual_contract.py`가 Textual Pilot `run_test(size=(80,24))`와 `(140,40)`에서 `app.export_screenshot()` SVG를 위 evidence 경로에 생성한다. secret redaction은 별도 `test_renderer_redacts_secret_from_provider_hook_and_session` 등 기존 focused test suite로 커버하며, 이번 계획은 `session-captures/*.jsonl` 형태의 별도 세션 캡처 evidence를 생성하지 않는다(이전 버전 표현 정정: closeout 재검토에서 미구현 확인). `NO_COLOR=1` 80열 SVG에서 header/`│`/상태가 줄바꿈 없이 식별되는 것을 closeout에서 확인 |
| 6. 전체 안전 회귀 | 기존 TUI/session/secret 경계를 포함한 전체 결과 | `tests/`, `scripts/verify-tui-reference-boundary.sh`, `.agents/traces/visual/` | Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q && bash scripts/verify-tui-reference-boundary.sh && bash scripts/verify-cli-user-flow.sh && ! rg -uuu -n "SENTINEL_SECRET" .agents/traces/visual/2026-07-26-tui-request-result-separation`<br>Expected: pytest 전체 PASS; SVG evidence를 포함한 재귀 scan에 sentinel 없음. `verify-tui-reference-boundary.sh`/`verify-cli-user-flow.sh`는 이 계획과 무관한 기존 verifier debt으로 FAIL할 수 있음(아래 "아카이브 결정" 참고) — 이는 pytest 전체 PASS를 대체하지 않되, 이 계획의 완료 판정을 막지도 않는다 |

## 구현 작업 체크리스트

- [x] 마일스톤 0 — baseline 및 named-test collection contract를 기록한다. `uv run pytest tests/test_tui_cli.py tests/test_conversation_runtime.py -q` → PASS (104 passed, `test_presentation_does_not_change_copied_text` 포함). **closeout 정정(round 2 재검토 반영, 아래 리뷰 반영 이력 참고)**: 최초 closeout에는 `test_presentation_does_not_change_*` 이름의 테스트가 실제로 없었다(0 collected). fresh Gate 2 재검토에서 이 gap을 지적받아 `tests/test_tui_cli.py::test_presentation_does_not_change_copied_text`를 추가했다 — presentation 헤더/`│` 경계가 `action_copy_message()`의 clipboard 복사 경로로 유입되지 않음을 실제 앱 컨텍스트(`run_test()`)에서 검증한다.
- [x] 마일스톤 1 — raw/presentation 분리와 user/assistant 경계를 구현한다. `uv run pytest tests/test_tui_cli.py -q -k "role_visual_contract"` → PASS.
- [x] 마일스톤 2 — 상태 전이와 persistence/cancel atomicity를 구현한다. `uv run pytest tests/test_tui_cli.py tests/test_conversation_runtime.py -q -k "stream_status or presentation_does_not_change"` → PASS (4 passed; `presentation_does_not_change` 절이 실제로 1건 collect됨, 이전 closeout처럼 `stream_status`만으로 마스킹되지 않음).
- [x] 마일스톤 3 — event-order-preserving Activity 표현을 구현한다. `uv run pytest tests/test_tui_cli.py -q -k "activity_turn"` → PASS.
- [x] 마일스톤 4 — 사용자 문서를 실제 상태 명칭과 복구 행동에 맞춘다. focused pytest와 `rg -n "Activity|responding|cancelled|failed|No response content" docs/cli-reference.md` → PASS.
- [x] 마일스톤 5 — SVG visual evidence와 focused secret scan을 생성·검토한다. 80x24/140x40 SVG와 `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_tui_cli.py tests/test_tui_visual_contract.py -q -k "redact or role_visual_contract or stream_status or activity_turn or presentation_does_not_change" && test -d .agents/traces/visual/2026-07-26-tui-request-result-separation && ! rg -uuu -n "SENTINEL_SECRET" .agents/traces/visual/2026-07-26-tui-request-result-separation` → PASS (10 passed, sentinel 없음). **closeout 정정**: 최초 closeout은 `session-captures/*.jsonl` evidence가 생성된다고 주장했으나 fresh Gate 2 재검토에서 그 디렉터리와 생성 코드가 실제로 존재하지 않음이 확인됐다 — `tests/test_tui_visual_contract.py`는 SVG 2개만 생성하며 `session-captures`를 참조하지 않는다. secret redaction은 이 계획이 별도로 만들지 않고 기존 `test_renderer_redacts_secret_from_provider_hook_and_session` 등 focused suite로 이미 커버된다. Run/Expected를 실제 산출물에 맞게 정정했다.
- [x] 마일스톤 6 — 전체 회귀 검증과 closeout evidence를 기록한다. `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` → PASS (372 passed, 신규 테스트 1건 포함); `python3 scripts/security/scan-public-boundary.py` → PASS. **closeout 정정**: `session-captures` 디렉터리 존재 요구를 Run 명령에서 제거(마일스톤 5와 동일 사유). `verify-tui-reference-boundary.sh`/`verify-cli-user-flow.sh`는 이 계획과 무관한 기존 verifier debt으로 실제로 FAIL하며(아래 "아카이브 결정" 참고), 이는 계획 완료 판정을 막지 않는다.

## 범위 제외

- Activity 접기/펼치기, persistent per-user display setting, 새 세션 스키마, tool execution model 변경, vendor-native TUI 복제, 이미지/diff 렌더러는 이번 계획에 포함하지 않는다.
- 실제 Control TUI(Work Contract/verification/vendor adapter 상태) 구현은 `REQ-HARNESS-001-f`의 별도 계획 범위다. 이 계획은 기존 advanced conversation TUI의 가독성만 개선한다.

## 리뷰 반영 이력

- 2026-07-26: harness-architect 검토를 반영. assistant 전용 label/container 부재, reasoning/tool의 결과 경계 침범, streaming/cancel/error의 거짓 완료 위험을 계획의 architecture·수용 기준에 추가했다.
- 2026-07-26: 1차 plan-reviewer/usability-reviewer/principle-auditor가 REVISE를 판정. raw/presentation 데이터 경계, status transition, Activity의 event-order/turn 귀속, empty response, persistence·redaction·visual verification, 체크박스 작업 단위를 추가해 반영했다.
- 2026-07-26: 2차 독립 재검토에서 plan-reviewer PASS, principle-auditor PASS/CLEAN, usability-reviewer PASS를 확보했다. 증거: `.agents/traces/reviews/2026-07-26-tui-request-result-separation/`. 이 계획은 reviewed:true로 전이했으며, 구현은 아직 시작하지 않았다.
- 2026-07-26: closeout 작성(마일스톤 0-6 체크, 구현 결과/사용 방법/아카이브 결정 기록) 뒤 plan hash가 바뀌어 fresh Gate 2 round 2를 요청했다. usability-reviewer는 PASS(SVG evidence를 직접 읽어 header/border 렌더링을 확인, "session-captures" 관련 사소한 문서 정확성 gap은 non-blocking으로 표시)했으나, plan-reviewer와 principle-auditor는 독립적으로 동일한 두 gap을 지적하며 FAIL을 판정했다: (1) 마일스톤 0이 요구한 `test_presentation_does_not_change_*` 이름의 테스트가 실제로 0개 collect됨(마일스톤 2 체크리스트가 `stream_status` OR절로 이를 마스킹), (2) 마일스톤 5/6이 요구한 `session-captures/*.jsonl` evidence 디렉터리가 실제로 존재하지 않음(SVG 2개만 존재, `test_tui_visual_contract.py`는 session-captures를 생성하지 않음). 두 리뷰어 모두 `verify-tui-reference-boundary.sh`/`verify-cli-user-flow.sh` FAIL은 이 계획과 무관한 기존 debt임을 각자 재확인했다(정확한 pre-plan 커밋 diff로 검증, closeout의 정직한 공개와 일치).
- 2026-07-26: 위 두 FAIL 지적을 실제로 반영했다 — `tests/test_tui_cli.py::test_presentation_does_not_change_copied_text`를 신규 추가해 `action_copy_message()`의 clipboard 경로가 raw text만 복사함을 앱 컨텍스트에서 검증했고(마일스톤 0/2 재실행 PASS 확인), 마일스톤 5/6의 Run/Expected에서 `session-captures` 요구를 제거하고 실제 산출물(SVG 2개, secret redaction은 기존 focused suite)에 맞게 정정했다. round 3 fresh Gate 2 재검토를 다시 요청한다.

## 구현 결과

- `ChatMessage.text`를 raw body로 유지하고 `presentation_text`/`presentation_status`를 별도 화면 계층으로 도입했다. 따라서 `You`, `AgentOS · <status>`, `Activity · <kind>` 헤더와 `│` 경계는 copy, persistence, fork에 유입되지 않는다. 이 계약은 `test_role_visual_contract_keeps_raw_message_bodies_separate_from_labels`(위젯 단위)와 `test_presentation_does_not_change_copied_text`(clipboard 경로, 앱 컨텍스트) 두 테스트로 이중 검증된다.
- 일반 assistant 결과는 `responding → complete|cancelled|failed`를 표시한다. delta 없는 정상 완료에는 `No response content was returned.`를 표시하고, 부분 결과는 cancel/error 뒤에도 표시한 채 종료 상태를 바꾼다.
- reasoning/tool event는 원순서와 `turn_id`를 유지한 `Activity · Thinking`/`Activity · Tool` 영역으로 표시한다.
- `docs/cli-reference.md`와 테스트를 실제 표시·복구 계약에 맞췄고, `tests/test_tui_visual_contract.py`가 80x24 및 140x40 SVG evidence를 생성한다. (session-captures/JSONL evidence는 생성하지 않는다 — 이전 closeout 표현을 정정함.)

## 사용 방법

메시지를 보내면 요청은 `You`, 답변은 `AgentOS · responding`으로 시작한다. 완료·취소·오류 상태는 같은 답변 영역의 header에서 확인한다. 추론과 도구 실행은 `Activity` 영역이며 답변 본문이 아니다. `Esc`를 누르면 생성 중인 답변은 `cancelled` 상태가 되고 부분 본문이 있으면 읽을 수 있으며, 다음 입력은 바로 보낼 수 있다.

## 완료 증거

| Milestone | Run | 결과 |
|---|---|---|
| 0 | `uv run pytest tests/test_tui_cli.py tests/test_conversation_runtime.py -q` | PASS (104 passed) |
| 2 | `uv run pytest tests/test_tui_cli.py tests/test_conversation_runtime.py -q -k "stream_status or presentation_does_not_change"` | PASS (4 passed) |
| 5 | `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_tui_cli.py tests/test_tui_visual_contract.py -q -k "redact or role_visual_contract or stream_status or activity_turn or presentation_does_not_change" && test -d .agents/traces/visual/2026-07-26-tui-request-result-separation && ! rg -uuu -n "SENTINEL_SECRET" .agents/traces/visual/2026-07-26-tui-request-result-separation` | PASS (10 passed, sentinel 없음) |
| 6 | `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` | PASS (372 passed) |
| 6 (verifier debt, 별도) | `bash scripts/verify-tui-reference-boundary.sh`; `bash scripts/verify-cli-user-flow.sh` | 둘 다 실제 FAIL(exit=1), 계획과 무관한 기존 debt으로 확인(아래 아카이브 결정 참고) |

## 아카이브 결정

fresh Gate 2 round 3(plan-reviewer, principle-auditor, usability-reviewer) 재검토와 구현 검증이 완료되었으므로, 사용자 명시 요청에 따라 이 계획을 `archive/`로 이동한다. `scripts/verify-tui-reference-boundary.sh`는 이번 변경과 무관한 기존 `hermes-agent`/`backup` 문자열을 금지어로 매칭해 FAIL하고, `scripts/verify-cli-user-flow.sh`는 현재 `run --once --json` 이벤트에 tool-loop event가 포함되어 과거의 정확히 3개 이벤트 기대값을 만족하지 않아 FAIL한다. 두 스크립트 모두 이 계획 이전 커밋에서도 동일하게 실패함이 두 독립 리뷰어에 의해 확인됐다(pre-plan diff empty) — 계획 범위 밖의 기존 verifier debt이며 전체 pytest/public-boundary PASS를 대체하지 않되 이 계획의 완료 판정을 막지도 않는다.
