# AgentOS TUI 메시지 배경색 블록 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-26<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-26T07:32:00Z<br>
> implementation_completed_at: 2026-07-26T07:37:00Z<br>
> implementation_duration: 5m<br>

> **usability_review_required:** true<br>
> Usability scope: 사용자 대화 화면에서 user 메시지의 배경이 바뀌고, 넓은/좁은 터미널·무색상 환경에서의 가독성이 바뀐다.

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 선행 계획 `2026-07-26-tui-request-result-separation`(상태: 완료, reviewed: true, 여전히 `exec-plans/active/`에 위치 — `You`/`AgentOS · <status>` 헤더 + 좌측 `│` 경계 구현 완료)이 이미 갖춘 role 구분 위에, pi/hermes-agent 조사 근거(`.agents/traces/research/2026-07-26-tui-message-box-format-pi-hermes-evidence.md`)를 적용해 **user 메시지에 전체폭 배경색 블록**을 추가함으로써 스크롤 중 시각적 구분을 더 강화한다.

**사용자 결과 요약:**
- 최종 결과: 사용자가 보낸 메시지(`You` 헤더 영역)는 터미널 폭 전체에 걸친 배경색 블록으로 렌더링되어, 색상만으로도 스크롤 중 즉시 자신의 입력 위치를 찾을 수 있다. `AgentOS · <status>` 답변과 `Activity · <kind>` 영역은 기존처럼 배경 없는 평문 + 좌측 `│` 경계를 유지한다. `ChatMessage.tool`의 기존 `border: round $warning` 테두리는 그대로 유지된다(hermes의 "테두리는 tool 결과류에만" 관례와 일치).
- 대상 독자: AgentOS Textual TUI로 세션을 사용하는 개발자.
- 일상 사용의 변화: 헤더 텍스트를 읽지 않아도 배경색 대비만으로 자신의 입력과 AgentOS 답변을 구분할 수 있다. `NO_COLOR=1` 등 무색상 환경에서는 기존 헤더/`│` 경계가 유일한 구분 수단으로 남는다(배경색은 무색상 환경에서 표시되지 않을 수 있음을 문서에 명시).
- 바뀌지 않는 경계: `ChatMessage.text`(raw body), `presentation_status`, 헤더 텍스트, `│` 좌측 경계, Activity 표현, 상태 전이(responding→complete/cancelled/failed) 계약은 이번 계획으로 변경하지 않는다 — 이번 계획은 오직 `ChatMessage.user`의 CSS `background` 속성 추가와 그에 따른 padding/wrapping 조정만 다룬다. `ConversationMessage`/JSONL/스냅샷 스키마, copy(OSC52)/persistence 경로, 새 팔레트·테마 시스템 도입은 포함하지 않는다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 기존 Python/Textual 및 테스트 의존성만 사용한다.
- 현재 구조 근거: `agentos/terminal/tui/widgets.py:174-209`(`ChatMessage.DEFAULT_CSS`) — `ChatMessage.user`는 현재 `color: $success;`만 가지며 `background`가 없다. `ChatMessage.tool`은 이미 `border: round $warning;`을 갖고 있다(변경 대상 아님). `ChatMessage.assistant`는 빈 규칙이며 이번 계획에서도 배경을 추가하지 않는다.
- 참조 구현 근거: `.agents/traces/research/2026-07-26-tui-message-box-format-pi-hermes-evidence.md` — pi의 `Box(paddingX, paddingY=1, bgFn)`가 라인 전체를 배경색으로 채우는 패턴(`packages/tui/src/components/box.ts:74-136`, `packages/coding-agent/.../user-message.ts:29-45`)을 근거로 삼되, 코드를 직접 이식하지 않고 Textual CSS `background` 속성으로 동등한 결과를 낸다. hermes의 "진짜 테두리는 tool 결과류에만"(`messageLine.tsx:103-121`) 관례에 따라 tool 영역의 기존 테두리는 그대로 둔다.
- root 문서 정합성: `REQ-CLI-003`의 대화형 TUI 가독성 개선에 속한다. `REQ-HARNESS-001-f`(Control TUI)는 이번 계획의 범위가 아니다. `.agentos/project/05-agent-operating-contract.md`의 TUI session/hook 보존 규칙을 준수한다.

**장기 적용 표면:**
- Traceability Surface: `.agents/traces/research/2026-07-26-tui-message-box-format-pi-hermes-evidence.md`, 이 계획의 Gate 2 리뷰 증거와 완료 검증 기록.
- Durable Result Surface: `agentos/terminal/tui/widgets.py`(`ChatMessage.DEFAULT_CSS`), `docs/cli-reference.md`, `tests/test_tui_cli.py`, `tests/test_tui_visual_contract.py`, visual evidence under `.agents/traces/visual/2026-07-26-tui-message-box-format/`.

**진행 상태:** 구현 및 검증 완료. closeout은 Gate 2 승인 당시의 실행 범위에 대한 사후 기록이다.

**아키텍처:**
- `ChatMessage.user` CSS 규칙에 `background: $boost;`(Textual 내장 theme 변수, 새 팔레트 도입 없음)를 추가한다. 배경색이 라인 전체 폭에 적용되도록 기존 `width: 100%`를 유지하고, 헤더(`You`)와 본문 사이 가독성을 위해 `padding: 0 1;`을 `ChatMessage.user`에만 추가한다(다른 role에는 적용하지 않음 — 좌측 `│` 경계 정렬이 깨지지 않도록 `presentation_text`의 `│` 문자 위치는 변경하지 않는다).
- `ChatMessage.assistant`/`ChatMessage.reasoning`/`ChatMessage.tool`/`ChatMessage.system`은 배경을 추가하지 않는다 — 이번 계획은 user 메시지 블록화만 다룬다(hermes의 "assistant는 무배경 평문" 관례와 일치, 범위 최소화).
- `ChatMessage:focus`의 기존 `background: $boost;`(포커스 시 강조)와 `ChatMessage.user`의 상시 배경이 겹칠 경우, focus 상태에서도 시각적으로 구분 가능한지 확인한다 — 필요 시 `ChatMessage.user:focus`에 별도 강조 규칙(예: `border: round $accent;` 유지)을 추가한다.
- `NO_COLOR=1` 환경에서는 Textual이 배경색 렌더링을 생략할 수 있으므로, 이 경우에도 기존 헤더 텍스트(`You`)와 `│` 경계만으로 역할 구분이 유지됨을 접근성 검증에서 확인한다(회귀 없음 재확인, 신규 로직 추가 아님).

**기술 스택:** Python 3, Textual, Rich Markdown, pytest/Textual Pilot.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | user 전용 배경색 블록, 포커스 대비, 무색상 SVG 계약, 문서와 전체 회귀 검증 완료 |
| 완료됨 | Gate 2 3역할 PASS, 기준선 372 passed, 구현·테스트·문서 갱신, 최종 375 passed |
| 현재 위치 | 완료 — 아카이브 또는 PR 준비 시 이 closeout을 사용 |
| 다음 단계 | 사용자 요청 시 archive/commit/PR 준비 |
| 완료 신호 | 충족 — 아래 모든 Run/Expected 결과가 PASS이고 CLI 문서에 동작/무색상 대체 구분을 기록함 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 기준선 확인 | 기존 role/status 표현 회귀 없이 시작 | `tests/test_tui_cli.py`, `tests/test_conversation_runtime.py` | `Run:` `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` / `Expected:` 372 passed(현재 베이스라인), 회귀 없음 |
| 1. user 메시지 배경색 블록 | 사용자가 보낸 메시지가 터미널 폭 전체 배경색 블록으로 표시됨 | `agentos/terminal/tui/widgets.py`(`ChatMessage.DEFAULT_CSS`) | `Run:` `uv run pytest tests/test_tui_cli.py -q -k "user_message_background"` / `Expected:` PASS — `ChatMessage("user", ...)`가 mount된 뒤 렌더된 스타일에서 `background`가 설정되어 있고, `assistant`/`reasoning`/`tool`/`system` role은 배경이 추가되지 않았음을 assert |
| 2. focus 상태 시각 구분 유지 | 포커스된 user 메시지도 여전히 다른 상태와 구분됨 | `agentos/terminal/tui/widgets.py` | `Run:` `uv run pytest tests/test_tui_cli.py -q -k "user_message_focus_contrast"` / `Expected:` PASS — user 메시지에 포커스했을 때 기존 `ChatMessage:focus` 규칙과 충돌 없이 렌더됨을 assert |
| 3. 무색상 환경 회귀 없음 | `NO_COLOR=1`에서도 헤더/`│` 경계로 역할 구분 가능 | `tests/test_tui_visual_contract.py`, `.agents/traces/visual/` | `Run:` `NO_COLOR=1 uv run pytest tests/test_tui_visual_contract.py -q -k "role_visual_contract"` / `Expected:` PASS — 기존 접근성 계약(선행 계획에서 검증됨) 회귀 없음 재확인 |
| 4. 문서 정합 | 사용자가 배경색 블록 표현을 문서에서 확인 가능 | `docs/cli-reference.md` | `Run:` `rg -n "배경색|background block" docs/cli-reference.md` / `Expected:` 관련 설명 줄 출력 |
| 5. 전체 안전 회귀 | 기존 TUI/session/secret 경계를 포함한 전체 결과 | `tests/` | `Run:` `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` / `Expected:` 372보다 많거나 같은 PASS, 회귀 없음 |

## 범위 제외

- pi의 JSON 테마 파일·hot-reload, hermes의 skin overlay·light/dark 자동 감지 시스템 도입 — AgentOS는 Textual 내장 `App.theme`을 그대로 사용한다(단순성 원칙, `.agents/traces/research/2026-07-26-tui-message-box-format-pi-hermes-evidence.md` 참고).
- assistant/reasoning/tool/system 메시지의 배경색 추가 — 이번 계획은 user 메시지 블록화만 다룬다.
- hermes의 ASCII 트리(`├─`/`└─`) tool-call 표현, subagent heat-color gradient 이식 — 범위 밖.
- Ink 스타일 "테두리에 라벨 임베드" 기능, OSC 133 shell-integration 마커 이식 — 범위 밖.
- `ChatMessage.text`/`presentation_status`/헤더 텍스트/`│` 경계/상태 전이 계약 변경 — 선행 계획(`2026-07-26-tui-request-result-separation`, 완료, 여전히 `exec-plans/active/`에 위치)의 범위이며 이번 계획은 그 위에 배경색만 추가한다.

## 리뷰 반영 이력

- 초안 작성 — 2026-07-26. pi/hermes-agent Explore 조사 결과를 durable trace로 저장(`.agents/traces/research/2026-07-26-tui-message-box-format-pi-hermes-evidence.md`)하고, 선행 role/status 계획 위에 배경색 블록만 추가하는 최소 범위로 계획을 작성했다.

## 구현 결과

- `ChatMessage.user`에만 `background: $boost`와 `padding: 0 1`을 추가했다. 기존 `width: 100%`를 유지해 user 요청이 transcript 폭을 채우는 배경색 블록으로 보인다.
- assistant/reasoning/tool/system은 배경색을 추가하지 않았고, tool의 경고 테두리와 role/status/원문 메시지 계약은 변경하지 않았다.
- 기존 `ChatMessage:focus`의 accent round border가 user의 상시 배경 위에서도 적용됨을 Pilot 테스트로 확인했다.
- `NO_COLOR=1`의 narrow/wide SVG 증적을 `.agents/traces/visual/2026-07-26-tui-message-box-format/`에 생성해 색상 없이도 `You`/`AgentOS · complete`/`│` 경계가 남음을 확인했다.

## 사용 방법

일반 `agentos` TUI에서 메시지를 보내면 `You` 요청 영역이 은은한 전체폭 배경 블록으로 표시된다. 답변과 Activity 영역은 기존 평문 배경을 유지한다. `NO_COLOR=1` 또는 배경색을 생략하는 터미널에서는 `You`/`AgentOS` 헤더와 `│` 좌측 경계로 역할을 구분한다.

## 완료 증거

- PASS 기준선: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` → `372 passed`.
- PASS user 배경/포커스: `uv run pytest tests/test_tui_cli.py -q -k 'user_message_background or user_message_focus_contrast'` → `2 passed`.
- PASS 무색상 시각 계약: `NO_COLOR=1 uv run pytest tests/test_tui_visual_contract.py -q -k 'role_visual_contract or user_background_block'` → `2 passed`; 80×24/140×40 SVG 증적 생성.
- PASS 문서: `rg -n 'background block|배경색' docs/cli-reference.md` → 관련 설명 출력.
- PASS 최종 회귀: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` → `375 passed`.
- 참고: `bash scripts/verify-tui-reference-boundary.sh`는 이번 변경과 무관한 기존 `hermes-agent`/`backup` 문자열을 탐지해 exit 1을 반환한다. 이 계획의 변경 경로에는 해당 참조를 추가하지 않았고, 테스트·문서·SVG 검증은 모두 PASS다.

## 아카이브 결정

구현과 검증은 완료되었으며, 사용자 명시 요청에 따라 다른 완료된 TUI 계획과 함께 `archive/`로 이동한다. Gate 2 증적은 구현 전 승인 당시의 plan hash를 기준으로 유효하며, 이 closeout 본문은 사후 결과 기록이다.

## 사후 수정: user/assistant `│` 좌측 경계 제거 (2026-07-26)

사용자가 새 세션에서 실제로 배경색 블록을 확인하는 과정에서, 좁은 터미널에서 입력 첫 글자가 `You\n│ ` 접두사 때문에 다음 줄로 밀리는 현상을 발견했다. `│`는 이번 계획이 아니라 선행 계획(`2026-07-26-tui-request-result-separation`)이 만든 표현이었으나, user 메시지가 이제 배경색 블록으로 구분되고 assistant는 헤더 텍스트만으로 구분되므로 `│`가 더 이상 필요하지 않다고 판단해 제거했다. Activity(reasoning/tool) 영역은 여러 활동 항목을 구분하는 데 `│`가 여전히 유용해 그대로 유지했다.

- 변경: `agentos/terminal/tui/widgets.py`의 `presentation_text`/`_render_presentation`에 `_uses_left_border()` 헬퍼를 추가해 role별로 `│` 사용 여부를 분기(`reasoning`/`tool`만 `│` 유지, `user`/`assistant`는 헤더 다음 줄에 본문을 바로 표시).
- 테스트 갱신: `tests/test_tui_cli.py`의 user/assistant presentation assertion 8건을 `You\n│ ...`/`AgentOS · ...\n│ ...`에서 `│` 없는 형태로 수정. `tests/test_tui_visual_contract.py::test_user_background_block_preserves_no_color_role_contract`의 `assert "│" in svg`를 제거(더 이상 해당 SVG에 `│`가 나타나지 않음).
- 문서 갱신: `docs/cli-reference.md`에서 "Both regions use a visible `│` left boundary" 문장을 제거하고, `Activity` 항목만 `│` 좌측 경계를 유지한다는 설명으로 정정.
- 검증: `uv run pytest tests/test_tui_cli.py -q` → 94 passed; `uv run pytest tests/test_tui_visual_contract.py -q` → 2 passed; `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/ -q` → 375 passed(회귀 없음). role별 실제 출력을 직접 확인: `user`/`assistant`는 `"You\nhello"`/`"AgentOS · responding\nDone."`(│ 없음), `reasoning`/`tool`은 `"Activity · Thinking\n│ planning"`/`"Activity · Tool\n│ read file"`(│ 유지).
- 리뷰: 사용자 요청에 따라 간소화된 사후 단일 리뷰로 처리(3인 Gate 2 재검토 생략) — 변경 범위가 이미 승인된 계획의 표현 하나(구분 문자 제거)에 한정되고, 전체 테스트 회귀가 통과했음을 근거로 한다.
