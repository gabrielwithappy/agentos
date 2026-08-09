# AgentOS TUI — pi/hermes TUI 클론 (Phase 4: 메시지 포커스 이동 및 클립보드 복사) 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-22<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-22T22:13:46Z<br>
> implementation_completed_at: 2026-07-22T22:22:06Z<br>
> implementation_duration: 약 8분 20초<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 사용자가 Composer 입력 텍스트뿐 아니라 대화 이력의 개별 메시지도 선택해 시스템 클립보드로 복사할 수 있게 한다 (pi/hermes TUI의 "클립보드 읽기/쓰기" 패턴 이식).
- 이 과정에서 Phase 3에서 도입된 `f`(분기 생성) 키가 실제 사용자 경로(포커스 이동)로는 한 번도 동작한 적이 없던 미구현 상태를 함께 해소해, `f`와 신규 `c`(복사) 키가 모두 실사용 가능하도록 만든다. (Phase 3 당시 테스트가 앱 핸들러를 직접 호출하는 방식이라 통과했을 뿐, `ChatMessage`가 애초에 포커스 불가능한 위젯이어서 실제 Tab 입력으로는 도달할 수 없었다 — 새로 생긴 회귀가 아니라 처음부터 있던 갭이다.)

**사용자 결과 요약:**
- 최종 결과: 사용자는 `Tab`/`Shift+Tab`으로 대화 이력의 메시지를 순회하며 포커스를 옮기고, 포커스된 메시지에서 `c`를 누르면 해당 메시지 전문이 시스템 클립보드(OSC 52)로 복사된다. `f`(분기 생성)도 동일한 포커스 경로로 실제 동작한다. Composer 입력창에서는 기존 Textual 기본 `Ctrl+C`/`Ctrl+V`가 이미 시스템 클립보드와 연동됨을 회귀 테스트로 보장한다.
- 대상 독자: AgentOS TUI를 터미널에서 사용하는 개발자/운영자.
- 일상 사용의 변화: 어시스턴트 응답이나 과거 입력을 마우스 드래그 없이 키보드만으로 시스템 클립보드에 복사해 다른 앱에 붙여넣을 수 있다.
- 바뀌지 않는 경계: 세션 파일 포맷(JSONL), `sanitize()` secret redaction 경로, 기존 슬래시 커맨드 동작은 변경하지 않는다. 클립보드 복사는 OSC 52를 지원하지 않는 터미널(macOS Terminal.app 등)에서는 동작하지 않을 수 있으며, 이는 Textual 자체의 알려진 제약으로 별도 폴백을 구현하지 않는다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. `App.copy_to_clipboard()` / `App.clipboard`는 Textual 0.57.0부터 제공되는 내장 API(OSC 52 escape sequence 기반)이며, 현재 `pyproject.toml`의 `textual>=6.0.0` 하한이 이미 이를 충족한다 (설치된 버전 8.2.8에서 직접 확인). `pyperclip` 등 신규 패키지나 `xclip`/`wl-clipboard` 같은 시스템 유틸리티는 필요하지 않다.
- 검증 근거: `python3 -c "from textual.app import App; print(App.copy_to_clipboard)"` 및 웹 검색으로 도입 버전(0.57.0) 확인 완료.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거.
- Durable Result Surface: `agentos/terminal/tui/widgets.py` (ChatMessage, Transcript), `agentos/terminal/tui/app.py` (_HOTKEYS_TABLE, `AgentOSTui.on_key` 포커스 링 핸들러), `docs/cli-reference.md`, `tests/test_tui_cli.py`. 인벤토리 문서(`2026-07-22-pi-hermes-tui-feature-inventory.md`)의 "§2.4 텍스트 입력 고급 기능" 항목은 이번 Phase 4 완료로 클립보드 복사/붙여넣기 하위 항목이 해소됨을 반영해 갱신한다.

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:**
- `ChatMessage(Static)`가 현재 `can_focus`를 설정하지 않아 (`Static.can_focus == False` 기본값) 실제 Tab 포커스 경로로 도달할 수 없다. 이번 계획에서 `can_focus=True`로 전환하고 `:focus` CSS로 시각 구분을 추가한다.
- **Tab/Shift+Tab 순회 로직의 위치는 `Transcript.on_key`가 아니라 `AgentOSTui`의 `action_focus_next`/`action_focus_previous` 오버라이드여야 한다** (Gate 2 리뷰 이후 구현 중 실측으로 확정 — 아래 "구현 결과" 참조). 설치된 Textual(8.2.8) 소스를 직접 확인한 결과: (1) `Screen.BINDINGS`(`textual/screen.py:270-271`)에 `Binding("tab", "app.focus_next")`, `Binding("shift+tab", "app.focus_previous")`가 이미 기본 등록되어 있고, (2) `Composer`(TextArea)는 기본값 `tab_behavior="focus"`이므로 `TextArea._on_key`가 Tab 키를 텍스트 삽입으로 소비하지 않고 이벤트를 그대로 흘려보낸다(단, 입력값이 `/`로 시작할 때만 `Composer.on_key`가 커맨드 팔레트 용도로 Tab을 직접 가로챈다 — `agentos/terminal/tui/widgets.py:468`). (3) 그러나 흘려보내진 Key 이벤트가 `App._on_key`(Textual `app.py:4341-4343`)에 도달하면, `App._on_key`는 `_check_bindings()`로 포커스된 위젯부터 위로 올라가며 바인딩 체인(Screen의 `tab`/`shift+tab` 바인딩 포함)을 먼저 매칭·실행하고, 매칭되면 `dispatch_key()`(이것이 `App.on_key`를 호출하는 경로)를 아예 건너뛴다. 즉 `on_key`를 오버라이드해도 Tab/Shift+Tab에는 절대 도달하지 않는다 — 반드시 바인딩이 실제로 호출하는 액션(`action_focus_next`/`action_focus_previous`) 자체를 오버라이드해야 한다.
- Textual 기본 `focus_next`/`focus_previous`(즉 `self.screen.focus_next()`/`focus_previous()`)에 그대로 의존하지도 않는다. 기본 동작은 DOM 마운트 순서(오래된 메시지 → 최신 메시지 → Composer)를 따르므로, Composer에서 Tab을 누르면 다음 위젯이 없어 wrap-around로 가장 **오래된** 메시지로 이동해버려 "최신 메시지부터 순회"라는 사용자 결과를 만족하지 못한다. 대신 `AgentOSTui.action_focus_next`/`action_focus_previous`에서 명시적 포커스 링 `[Composer, 최신 메시지, ..., 가장 오래된 메시지]`을 구성해 Tab은 다음 인덱스로, Shift+Tab은 이전 인덱스로 이동시키고 양 끝에서 서로 순환하도록 구현한다. 이 개입은 `self.focused`가 `Composer` 또는 `Transcript` 소속 `ChatMessage`일 때만 발동하며, 그 외(예: `SessionPicker`가 포커스를 가진 경우)에는 `super().action_focus_next()`/`super().action_focus_previous()`로 기본 동작에 위임한다.
- 포커스된 `ChatMessage`에서 `c` 키 입력 시 `self.app.copy_to_clipboard(self.text)` 호출. 기존 `f`(분기) 핸들러와 동일한 `on_key` 디스패치 패턴을 재사용한다 — 이 부분은 포커스가 이미 확보된 이후 로컬 위젯에서 처리되므로 버블링 이슈가 없다. 단, OSC 52는 터미널의 실제 반영 여부를 알려주는 ACK가 없는 fire-and-forget 프로토콜이므로, 복사 확인 알림 문구는 "복사됨"이 아니라 "복사 시도됨" 계열로 표현해 OSC 52 미지원 터미널(예: macOS Terminal.app)에서 거짓 성공 신호를 주지 않는다.
- Composer(TextArea)의 `Ctrl+C`/`Ctrl+V`는 이미 Textual 기본 `action_copy`/`action_paste`가 처리하며 Composer의 `on_key`가 이 키들을 가로채지 않음을 확인했다. 이번 계획에서는 회귀 테스트만 추가하고 로직은 변경하지 않는다.

**기술 스택:**
- Python, Textual (TextArea, Static, VerticalScroll, Pilot 테스트 하네스), pytest.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 완료 |
| 완료됨 | Gate 2 2라운드 리뷰 통과(전원 PASS), 마일스톤 1-6 구현 및 전체 검증 통과 |
| 현재 위치 | 구현 완료, 사용자 요청 시 archive/commit/PR 대기 |
| 다음 단계 | 사용자 요청 시 `git add`/commit, 계획 문서 archive 이동 |
| 완료 신호 | 아래 마일스톤의 `Run:`/`Expected:` 검증이 모두 통과하고 `docs/cli-reference.md` 및 `_HOTKEYS_TABLE`이 신규 단축키를 반영함 — 전체 충족(구현 결과 참조) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. ChatMessage 포커스 가능화 + Tab/Shift+Tab 순회 | `Tab`을 누르면 Composer 밖으로 포커스가 이동해 가장 최근 메시지부터 시작해 과거 메시지 방향으로 순회 가능하고, `Shift+Tab`은 반대 방향으로 순회하며 양 끝(가장 오래된 메시지 ↔ Composer)에서 서로 순환한다. 포커스된 메시지는 테두리/배경으로 시각 구분됨 | `agentos/terminal/tui/widgets.py` (`ChatMessage.can_focus`, CSS `:focus` 스타일), `agentos/terminal/tui/app.py` (`AgentOSTui.action_focus_next`/`action_focus_previous` 오버라이드 — Composer/ChatMessage 간 포커스 링 이동; `Transcript.on_key`도, 순수 `on_key`도 아님, 아키텍처 절 참조) | `Run:` `uv run pytest tests/test_tui_cli.py -k "focus_cycle" -q` / `Expected:` PASS — `pilot.press("tab")` 후 `pilot.app.focused`가 가장 최근 `ChatMessage` 인스턴스이고 `pilot.app.focused.has_pseudo_class("focus")`가 True임을 assert; 메시지 개수만큼 `pilot.press("tab")`을 반복한 뒤 포커스가 다시 Composer로 돌아옴을 assert |
| 2. `f`(분기) 키 실사용 경로 수정 (Phase 3부터 실키 입력으로는 동작한 적 없던 갭 해소) | 포커스된 메시지에서 `f`를 누르면 실제로 분기가 생성됨 (기존엔 이벤트 직접 호출로만 테스트되어 실사용 경로가 검증된 적이 없었음) | `agentos/terminal/tui/widgets.py` (`ChatMessage.on_key` — 마일스톤 1 의존), `agentos/terminal/tui/app.py` (`run_stream`의 `add_assistant_message()` — 구현 중 발견: `turn_id`를 전달하지 않아 assistant 메시지의 `turn_id`가 항상 `None`이었던 실제 버그, 포커스 도달 여부와 무관하게 `f`가 동작하지 않던 두 번째 원인. 아래 "구현 결과" 참조), `tests/test_tui_cli.py` (기존 가짜 이벤트 직접 호출 테스트를 `pilot.press("tab")` + `pilot.press("f")` 방식으로 교체) | `Run:` `uv run pytest tests/test_tui_cli.py -k "fork" -q` / `Expected:` PASS — 실제 키 입력 시퀀스로 `Transcript.ForkRequested`가 발생함을 assert |
| 3. 메시지 복사 `c` 키 | 포커스된 메시지에서 `c`를 누르면 해당 메시지 전문이 `app.clipboard`(OSC 52)로 복사 시도되고, 상태 표시줄/알림 배너에 "복사 시도됨" 계열 문구가 표시됨 (OSC 52는 터미널의 실제 반영 여부를 확인할 수 없는 fire-and-forget 프로토콜이므로 "복사됨" 대신 "시도"로 표현해 미지원 터미널에서 거짓 성공을 주장하지 않음) | `agentos/terminal/tui/widgets.py` (`ChatMessage.action_copy_message`, `on_key`) | `Run:` `uv run pytest tests/test_tui_cli.py -k "copy_message" -q` / `Expected:` PASS — `pilot.press("tab")` 후 `pilot.press("c")`, `pilot.app.clipboard == <메시지 텍스트>` assert; 알림/상태 문구에 "복사됨"이 아닌 "시도" 계열 단어가 포함됨을 assert |
| 4. Composer 클립보드 복사/붙여넣기 회귀 테스트 | Composer 입력 텍스트를 `Ctrl+C`로 복사, 다른 위치에 `Ctrl+V`로 붙여넣기 가능함이 테스트로 보장됨 (기능 자체는 Textual 기본 제공, 신규 구현 없음) | `tests/test_tui_cli.py` | `Run:` `uv run pytest tests/test_tui_cli.py -k "composer_clipboard" -q` / `Expected:` PASS — `pilot.press("ctrl+c")` 후 `pilot.app.clipboard`에 선택 텍스트가 담김을 assert |
| 5. 단축키 문서 동기화 | `/hotkeys`, `/help`, non-TTY 안내문, `docs/cli-reference.md`에 `Tab`/`Shift+Tab` 포커스 이동과 `c` 복사 단축키, 그리고 OSC 52를 지원하지 않는 터미널(예: macOS Terminal.app)에서는 복사가 실제로 반영되지 않을 수 있다는 안내가 함께 반영됨 | `agentos/terminal/tui/app.py` (`_HOTKEYS_TABLE`), `docs/cli-reference.md` | `Run:` `grep -n "Tab" agentos/terminal/tui/app.py \| grep -i focus && grep -n "복사\|clipboard" docs/cli-reference.md && grep -n "OSC 52\|지원하지 않는 터미널\|반영되지 않을 수" docs/cli-reference.md` / `Expected:` 각 grep이 신규 단축키 설명과 OSC 52 미지원 캐비엇을 모두 출력함 |
| 6. 전체 회귀 검증 | 기존 기능(테마, 분기, 스트리밍 등)이 깨지지 않음 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` 기존 통과 건수(114) 이상 PASS, 신규 실패 없음. `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` / `Expected:` PASS (secret redaction 회귀 없음) |

## 이번 범위에 포함하지 않는 것 (명시적 제외)

참조: `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md` §2.4 텍스트 입력 고급 기능

- **음성 입력 토글키** — 별도의 음성 인식(STT) 하위 시스템 도입이 선행되어야 하며, 이번 계획의 "선행 조건 없는 항목만" 범위를 벗어남.
- **Grapheme 단위 커서 이동 전면 재작업** — Textual `TextArea`의 커서 이동은 코드포인트 기준이며, 이모지/결합 문자(ZWJ 시퀀스 등)의 완전한 grapheme-cluster 인식 재작업은 범위가 크고 별도 조사가 필요해 이번 Phase에서 제외한다. 이번 계획으로 발생하는 신규 회귀는 없다 (기존 동작 그대로 유지).
- **Diff 렌더러 / 이미지 프로토콜 / 설정 관리 UI / 세션 압축 인디케이터 / 서브에이전트 트리 시각화** — 인벤토리 문서에 이미 "선행 시스템 필요"로 명시되어 있으며 이번 Phase 4 범위에서 제외 (사용자 확인 완료).

## 리뷰 반영 이력
- 초안 작성 — 2026-07-22, Gate 2 리뷰 대기 중.
- 1차 Gate 2 독립 서브에이전트 리뷰 (2026-07-23, `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase4/{plan-reviewer,principle-auditor,usability-reviewer}.{md,json}`):
  - `plan-reviewer`: FAIL — Milestone 1 아키텍처가 구현 불가능했다. `Composer`와 `Transcript`는 형제 위젯이라 `Transcript.on_key`는 Composer가 포커스를 가진 상태의 Tab 이벤트를 받을 수 없고(키 이벤트는 조상 체인으로만 버블링), Textual `Screen.BINDINGS`에 이미 `tab→focus_next`/`shift+tab→focus_previous`가 기본 등록되어 있으며 Composer의 기본 `tab_behavior="focus"`가 이를 그대로 통과시킨다는 사실을 계획이 반영하지 못했다. 또한 기본 `focus_next` wrap-around는 가장 오래된 메시지로 가지 "최신 메시지부터"라는 요구를 만족하지 못한다. → 아키텍처 절을 `AgentOSTui.on_key`(app.py) 기반 명시적 포커스 링 방식으로 전면 재설계하고, Milestone 1/2의 구현 소유 surface를 갱신해 반영함.
  - `principle-auditor`: REVISE — (1) 인벤토리 문서 섹션 번호가 "1.2"/"1.6"로 잘못 인용됨(실제는 §2.4) → 전부 §2.4로 수정. (2) `f` 키 문제를 "회귀"로 표현한 것이 부정확함(Phase 3에서 한 번도 실키 입력 경로로 동작한 적이 없던 미구현 갭이며, 새로 생긴 회귀가 아님) → 제목/목표/마일스톤 2 문구에서 "회귀" 프레이밍을 제거하고 정확한 설명으로 교체함.
  - `usability-reviewer`: FAIL — (1) OSC 52는 ACK 없는 fire-and-forget이라 미지원 터미널에서도 "복사됨" 알림이 뜨면 거짓 성공 신호가 됨 → Milestone 3 알림 문구를 "복사 시도됨" 계열로 교체하고 검증에 문구 assert 추가. (2) OSC 52 미지원 터미널 캐비엇이 계획 문서 내부에만 있고 최종 사용자 문서(`docs/cli-reference.md`)에는 반영되지 않음 → Milestone 5 범위와 grep 검증에 캐비엇 반영 확인을 추가함.
- 2차 Gate 2 독립 서브에이전트 재검증 (2026-07-23, `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase4/{plan-reviewer,principle-auditor,usability-reviewer}.{md,json}`, plan sha256 `7eb399c2fda5310261b1e8b5b119b7ffce4cdb86b9c5c1de89baaef4853f1f0f`): `plan-reviewer` PASS, `principle-auditor` PASS/APPROVE, `usability-reviewer` PASS — 3개 리뷰어 모두 설치된 Textual 8.2.8 소스(`screen.py`, `_text_area.py`)와 실제 코드(`widgets.py`, `app.py`)를 직접 대조해 새 아키텍처(포커스 링)와 텍스트 수정 사항을 독립 검증함. 블로킹 이슈 없음. `reviewed: true`로 전환.
- 구현 중 발견(2026-07-22, Gate 2 승인 이후): Gate 2에서 PASS된 `AgentOSTui.on_key` 기반 설계를 그대로 구현하고 `test_focus_cycle`을 먼저 작성해 실행한 결과, `pilot.press("tab")` 후에도 포커스가 Composer에 그대로 남아 실패함(정적 분석만으로는 드러나지 않은 결과). 원인 추적 결과 Textual `App._on_key`(`app.py:4341-4343`)가 `_check_bindings()`로 Screen의 `tab`/`shift+tab` 바인딩을 먼저 실행하고, 매칭되면 `App.on_key`를 호출하는 `dispatch_key()`를 건너뛰는 것을 확인함 — 3개 독립 리뷰어가 각자 확인한 개별 사실(바인딩 존재, TextArea가 이벤트를 막지 않음, Composer/Transcript가 형제 위젯)은 모두 정확했으나, 이 세 사실을 결합했을 때 `on_key`가 실제로 호출되는지 여부까지는 추적하지 못했음. 해결: Tab/Shift+Tab 바인딩이 실제로 호출하는 액션인 `action_focus_next`/`action_focus_previous` 자체를 오버라이드하는 방식으로 전환. 아키텍처 절과 마일스톤 1/2 표를 실제 구현에 맞춰 갱신함. 사용자에게 보이는 동작(순회 방향, 시작점, 시각 표시)과 마일스톤 검증 명령은 원안과 동일 — 내부 구현 메커니즘만 교정됨.
- 구현 중 발견 2 (2026-07-22): `run_stream`의 `add_assistant_message()`가 `turn_id`를 전달하지 않아 스트리밍 완료 후 assistant `ChatMessage.turn_id`가 항상 `None`으로 남는 기존 버그를 발견함(Phase 3부터 존재 — Phase 3 테스트가 앱 핸들러를 직접 호출해 이 경로를 거치지 않았기 때문에 드러나지 않았음). 포커스가 정상적으로 도달해도 `turn_id`가 없으면 `f` 키가 아무 동작도 하지 않으므로, Milestone 2의 실제 완결을 위해 `agentos/terminal/tui/app.py`에서 `add_assistant_message()`가 `turn_id`를 전달하도록 한 줄 수정함.

## 구현 결과
마일스톤 1-6을 모두 구현하고 검증했다.

1. **메시지 포커스 이동 (Milestone 1)** — `ChatMessage.can_focus = True` + `:focus` CSS(`agentos/terminal/tui/widgets.py`), `AgentOSTui.action_focus_next`/`action_focus_previous` 오버라이드로 Composer/메시지 포커스 링 구현(`agentos/terminal/tui/app.py`, `_focus_ring`/`_cycle_transcript_focus` 헬퍼). Gate 2 승인 설계(`Transcript.on_key`/`AgentOSTui.on_key`)는 구현 중 실측으로 작동하지 않음이 드러나 액션 오버라이드 방식으로 교정(위 "리뷰 반영 이력" 참조).
2. **`f`(분기) 키 실사용 경로 수정 (Milestone 2)** — 마일스톤 1로 포커스 도달이 가능해졌고, 추가로 발견한 `add_assistant_message()`의 `turn_id` 누락 버그를 수정해 실제로 `f`가 동작하도록 완결함. 기존 가짜 이벤트 직접 호출 테스트를 `pilot.press("tab")` + `pilot.press("f")` 실키 입력 시퀀스로 교체.
3. **메시지 복사 `c` 키 (Milestone 3)** — `ChatMessage.action_copy_message()`가 `self.app.copy_to_clipboard(self.text)` 호출 후 "복사 시도됨" 알림(OSC 52 fire-and-forget 특성 반영, 거짓 성공 신호 회피).
4. **Composer 클립보드 회귀 테스트 (Milestone 4)** — `test_composer_clipboard`로 Textual 기본 `Ctrl+C`/`Ctrl+V`(`action_copy`/`action_paste`) 동작을 보장. 로직 변경 없음.
5. **단축키 문서 동기화 (Milestone 5)** — `_HOTKEYS_TABLE`(`/hotkeys`, `/help`→`/hotkeys` 안내, non-TTY 안내문이 공유)에 Tab/Shift+Tab/c/f 항목 추가, `docs/cli-reference.md`에 포커스 이동·복사·OSC 52 미지원 터미널 캐비엇 반영. 인벤토리 문서 §2.4도 완료 반영으로 갱신.
6. **전체 회귀 검증 (Milestone 6)** — 전체 스위트 117 passed(기존 114 + 신규 3, `test_branch_fork_creates_parent_turn_id`는 실키 입력 방식으로 교체되어 순증 아님), secret redaction 8 passed 회귀 없음.

## 사용 방법
AgentOS TUI에서 대화 이력의 메시지를 클립보드로 복사하거나 분기를 만들려면:
1. `Tab`을 눌러 Composer에서 포커스를 빼면 가장 최근 메시지가 포커스된다(테두리로 표시됨).
2. 다시 `Tab`/`Shift+Tab`으로 과거/최근 메시지 사이를 이동한다. 가장 오래된 메시지에서 `Tab`을 누르거나 Composer에서 `Shift+Tab`을 누르면 서로 순환한다.
3. 포커스된 메시지에서 `c`를 누르면 해당 메시지 전문이 시스템 클립보드로 복사 시도되고 상태 알림이 뜬다. 터미널이 OSC 52를 지원해야 실제로 반영된다(macOS Terminal.app 등 일부 터미널은 미지원 — `docs/cli-reference.md` 참조).
4. 포커스된 메시지에서 `f`를 누르면 그 메시지의 턴에서 분기가 시작되고, 다음에 보내는 메시지가 그 지점에서 새 브랜치로 이어진다.
5. Composer에서는 기존과 동일하게 `Ctrl+C`/`Ctrl+V`로 입력 텍스트를 복사/붙여넣기할 수 있다(신규 구현 아님, Textual 기본 제공).

전체 단축키 목록은 TUI 안에서 `/hotkeys`로 확인할 수 있다.

## 완료 증거
- `Run:` `uv run pytest tests/test_tui_cli.py -k "focus_cycle" -q` → PASS
- `Run:` `uv run pytest tests/test_tui_cli.py -k "fork" -q` → PASS
- `Run:` `uv run pytest tests/test_tui_cli.py -k "copy_message" -q` → PASS
- `Run:` `uv run pytest tests/test_tui_cli.py -k "composer_clipboard" -q` → PASS
- `Run:` `grep -n "Tab" agentos/terminal/tui/app.py | grep -i focus && grep -n "복사\|clipboard" docs/cli-reference.md && grep -n "OSC 52\|지원하지 않는 터미널\|반영되지 않을 수" docs/cli-reference.md` → 3개 grep 모두 매치 출력
- `Run:` `uv run pytest tests/ -q` → 117 passed (기존 114 이상, 신규 실패 없음)
- `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` → 8 passed (secret redaction 회귀 없음)
- 변경 파일: `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py`, `docs/cli-reference.md`, `tests/test_tui_cli.py`, `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md`

## 아카이브 결정
구현 완료 및 전체 검증 통과, Gate 2 2라운드 전원 PASS 확보. 사용자가 이 세션에서 별도로 archive/commit/PR을 요청하면 진행한다(계획 문서를 `.agentos/project/exec-plans/archive/`로 이동). 아직 사용자 요청이 없어 `active/`에 유지한다.
