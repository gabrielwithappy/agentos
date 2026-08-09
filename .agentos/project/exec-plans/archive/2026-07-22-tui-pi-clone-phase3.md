# AgentOS TUI — pi/hermes TUI 클로닝 Phase 3 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-22<br>
> reviewed: true (Gate 2 자기검토 PASS — Antigravity fallback, 2026-07-22T13:30Z)<br>
> implementation_started_at: 2026-07-22T13:30:53Z<br>
> implementation_completed_at: 2026-07-22T13:39:15Z<br>
> implementation_duration: 8m 22s<br>
> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- Phase 1·2에서 이식한 기능 이후, pi TUI와 hermes TUI에서 추출한 다음 계층의 UX 패턴을 AgentOS TUI에 이식하여 사용자 경험을 한 단계 더 끌어올린다.
- 선행 조건이 없고 사용자 즉시 체감 가치가 높은 기능 6개를 우선 구현한다.
- 장기 기억 문서(§ 인벤토리)를 토대로 Phase 4 이후 후보군을 명확히 정의한다.

**사용자 결과 요약:**
- **알림 배너 (신규):** 오류나 경고가 발생했을 때 대화창에 긴 메시지를 추가하는 대신, 화면 상단에 잠깐 나타나는 배너(Toast)로 표시된다. `/hooks` 오류, 세션 저장 실패, provider 오류 등을 더 명확하게 알린다.
- **인디케이터 스타일 선택 (신규):** LLM이 응답을 생성하는 동안 보이는 로딩 표시를 4가지 스타일(kaomoji, emoji, ascii, unicode 브라이유 스피너) 중에서 선택할 수 있다. `/indicator [style]` 커맨드로 변경한다.
- **자동완성 퍼지 검색 (신규):** `/` 입력 시 열리는 커맨드 팔레트가 실시간으로 필터링된다. 정확한 이름을 몰라도 관련 단어만 입력하면 매칭되는 커맨드를 즉시 확인할 수 있다.
- **분기 생성 UI (신규):** 이전 대화 턴으로 돌아가 새 메시지를 보내면 새 분기(branch)가 생성된다. `/tree`에서 이미 분기 데이터 모델이 준비되어 있으므로, 분기를 만들면 즉시 `/tree`에서 트리 형태로 확인할 수 있다.
- **모델 선택기 `/model` (신규):** 세션 중 `/model [provider]` 명령으로 LLM 공급자를 전환할 수 있다. 현재 `agentos run --provider mock|codex` 인수로만 가능했던 것을 런타임에 변경 가능하게 한다.
- **스트리밍 마크다운 점진적 렌더링 (개선):** 응답 스트리밍 중에도 완성된 코드 블록, 테이블, 헤딩이 즉시 하이라이팅된다. 현재는 스트림 종료 후에야 마크다운이 렌더링된다.
- **바뀌지 않는 부분:** CLI 인수 인터페이스, 세션 JSONL 포맷(`agentos.session/v1`, `agentos.cli-event/v1`), secret redaction 레이어, 기존 slash 커맨드 동작, hook 파이프라인은 변경되지 않는다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 새 패키지 추가 가능성: `thefuzz`(퍼지 매칭, 선택적) — pyproject.toml에 optional dependency로 추가 고려.
- Textual 내장 기능 활용: `app.notify()` (배너), `LoadingIndicator` 대체 커스텀 위젯, `OptionList` 실시간 필터링.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `agentos/terminal/tui/app.py`, `agentos/terminal/tui/commands.py`, `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/renderers.py`, `docs/cli-reference.md`, `tests/test_tui_cli.py`
- Long-term Research Reference: `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md`

**진행 상태:** 계획 초안 작성 완료, Gate 2 리뷰 대기 중

**아키텍처:**
- 기존 `app.py` (AgentOSTui) 확장: `_indicator_style` 상태 추가, `action_cancel`에 배너 알림 연동
- `commands.py`: `/indicator`, `/model` 슬래시 커맨드 추가
- `widgets.py`: `LoadingIndicator` 대체 `SpinnerMessage` 커스텀 위젯, `CommandPaletteScreen` 실시간 필터링 개선
- `renderers.py`: 스트리밍 마크다운 부분 렌더링 로직 추가

**기술 스택:**
- Python 3.12+, Textual 8.2.8+, Rich, `thefuzz` (선택적 의존성)

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 계획 초안 작성 완료 |
| 완료됨 | 리서치 인벤토리 문서 작성, Phase 3 범위 정의 |
| 현재 위치 | Gate 2 리뷰 (plan-reviewer / principle-auditor / usability-reviewer) 대기 |
| 다음 단계 | Gate 2 리뷰 후 구현 실행 |
| 완료 신호 | `uv run pytest tests/ -q` PASS + 마일스톤별 수동 TUI 검증 PASS |

---

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. Preflight | 현재 테스트 회귀 없음 확인 | — | `Run: uv run pytest tests/ -q` `Expected: PASS (≥107 passed)` |
| 1. 알림 배너 (Toast) | hook 오류, provider 오류가 대화창 대신 화면 상단 배너로 표시됨 | `app.py` | `Run: uv run pytest tests/test_tui_cli.py -k notification -q` `Expected: PASS` |
| 2. 인디케이터 스타일 선택 | `/indicator kaomoji\|emoji\|ascii\|unicode` 실행 시 로딩 표시 스타일 변경됨 | `app.py`, `commands.py`, `widgets.py` | `Run: uv run pytest tests/test_tui_cli.py -k indicator -q` `Expected: PASS` |
| 3. 자동완성 퍼지 검색 | `/` 입력 후 텍스트 입력 시 커맨드 팔레트가 실시간으로 필터링됨 | `widgets.py` (CommandPaletteScreen), `commands.py` | `Run: uv run pytest tests/test_tui_cli.py -k palette -q` `Expected: PASS` |
| 4. 분기 생성 UI | 과거 ChatMessage 클릭 시 해당 턴에서 분기하여 새 메시지 입력 가능. `/tree`에서 분기 확인. | `app.py`, `widgets.py` (Transcript/ChatMessage), `terminal/events.py` | `Run: uv run pytest tests/test_tui_cli.py -k branch -q` `Expected: PASS` |
| 5. 모델 선택기 `/model` | `/model codex`, `/model mock` 등으로 세션 내 LLM provider 전환 가능 | `app.py`, `commands.py` | `Run: uv run pytest tests/test_tui_cli.py -k model_switch -q` `Expected: PASS` |
| 6. 스트리밍 마크다운 점진적 렌더링 | 응답 스트리밍 중 완성된 코드 블록/테이블이 즉시 하이라이팅됨 | `widgets.py` (ChatMessage.update_streaming), `renderers.py` | `Run: uv run pytest tests/test_tui_cli.py -k streaming_markdown -q` `Expected: PASS` |
| 7. 전체 검증 | 모든 테스트 통과, secret redaction 검증, docs 업데이트 확인 | `tests/`, `docs/cli-reference.md` | `Run: uv run pytest tests/ -q` `Expected: PASS` / `Run: AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` `Expected: PASS` |

---

## 마일스톤별 상세 구현 지침

### 마일스톤 1: 알림 배너 (Toast)

**목적:** pi의 `status-indicator.ts`와 hermes의 `Notice` 타입에서 영감을 받아, 오류/경고를 대화창 오염 없이 배너로 표시.

**변경 파일:**
- `agentos/terminal/tui/app.py`:
  - `_notify_error(msg: str)` 헬퍼 메서드 추가: `self.notify(msg, severity="error", timeout=5)`
  - `_notify_info(msg: str)` 헬퍼 메서드 추가: `self.notify(msg, severity="information", timeout=3)`
  - hook 오류 처리 부분에서 `ChatMessage` 추가 대신 `_notify_error()` 호출로 교체
  - provider 오류(`error` 이벤트) 처리에도 동일하게 적용

**테스트 추가:** `tests/test_tui_cli.py`에 `test_notification_on_hook_error` 추가

### 마일스톤 2: 인디케이터 스타일 선택

**목적:** hermes의 `renderIndicator()` 4가지 스타일을 Textual 방식으로 재현.

**변경 파일:**
- `agentos/terminal/tui/app.py`:
  - `self._indicator_style: str = "ascii"` 상태 추가 (기본값: ascii)
  - `/indicator` 커맨드 핸들러에서 `self._indicator_style` 업데이트
  - `_show_loading()` 메서드에서 스타일별 애니메이션 문자 사용
  - 스타일: `ascii` (|/-\), `unicode` (브라이유 ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏), `emoji` (⚕🌀🤔✨), `kaomoji` (고정 텍스트 "Thinking...")
- `agentos/terminal/tui/commands.py`:
  - `SlashCommand("/indicator", "Switch loading indicator style", "[ascii|unicode|emoji|kaomoji]", "indicator")` 추가
- `agentos/terminal/tui/widgets.py`:
  - `SpinnerMessage` 위젯 추가: 스타일별 프레임 배열 + `set_reactive` + `on_mount`에서 `set_interval(0.1, tick)` 패턴
  - 기존 `_loading_message: ChatMessage` → `SpinnerMessage` 타입으로 교체

**테스트 추가:** `test_indicator_style_switch`

### 마일스톤 3: 자동완성 퍼지 검색

**목적:** pi의 `autocomplete.ts` + `fuzzy.ts`에서 영감을 받아, 현재 `CommandPaletteScreen`을 실시간 필터링 UI로 개선.

**변경 파일:**
- `agentos/terminal/tui/widgets.py`:
  - `CommandPaletteScreen` 리팩토링:
    - `Input` 위젯 추가 (검색 입력창)
    - `Input.Changed` 이벤트에서 `matching_commands(query)` 호출 → `OptionList` 재구성
    - `OptionList`를 `DataTable` 또는 `ListView`로 교체하여 동적 필터링 지원
- `agentos/terminal/tui/commands.py`:
  - `matching_commands()` 함수 개선: 단순 substring 매칭 → 이중 평가 (exact prefix 우선, 이후 description 포함 퍼지 매칭)
  - `thefuzz`가 설치된 경우 fuzzy ratio 기반 정렬 추가 (선택적) — `try/except ImportError`로 감싸서 미설치 시 자동 폴백, 에러 없이 동작해야 함

**테스트 추가:** `test_command_palette_fuzzy_filter`

### 마일스톤 4: 분기 생성 UI

**목적:** pi의 `session-selector.ts`와 `tree-selector.ts`에서 영감. 이미 완성된 `parent_turn_id` 데이터 모델을 활용하여 실제 분기를 생성하는 UI를 추가.

**변경 파일:**
- `agentos/terminal/tui/widgets.py`:
  - `ChatMessage`: 포커스 상태에서 `f` 단축키로 `action_fork_from_here()` 발동 (Enter는 기존 대화창 동작과 충돌하므로 사용 금지)
  - `Transcript`: `on_chat_message_fork_requested(message: Message)` 메서드 — 해당 turn_id를 `parent_turn_id`로 설정하는 메시지를 app에 게시
- `agentos/terminal/tui/app.py`:
  - `on_transcript_fork_requested(event)` 핸들러 추가
  - `Composer`를 포커스하고 `self._pending_parent_turn_id = turn_id` 상태 저장
  - 다음 턴 제출 시 `wrap_provider_event()` 호출에서 `parent_turn_id=self._pending_parent_turn_id` 전달
- `agentos/terminal/events.py`:
  - **수정 불필요** — `wrap_provider_event(parent_turn_id: str | None = None)` 이미 구현됨 (Phase 2에서 추가됨)

**테스트 추가:** `test_branch_fork_creates_parent_turn_id`

### 마일스톤 5: 모델 선택기 `/model`

**목적:** pi의 `model-selector.ts`와 hermes의 `modelPicker.tsx`에서 영감. 세션 내 provider 런타임 전환.

**변경 파일:**
- `agentos/terminal/tui/commands.py`:
  - `SlashCommand("/model", "Switch LLM provider for this session", "[provider]", "model")` 추가
- `agentos/terminal/tui/app.py`:
  - `handler_model(arg: str)` 추가:
    - `arg`가 비어있으면 현재 provider와 사용 가능한 provider 목록 표시
    - `arg`가 유효한 provider name이면 `self.provider = arg` 업데이트 + 상태 표시
  - `ModelPickerScreen` (ModalScreen) 추가: `OptionList`로 `["mock", "codex"]` 표시, 선택 시 provider 전환

**테스트 추가:** `test_model_switch_command`

### 마일스톤 6: 스트리밍 마크다운 점진적 렌더링

**목적:** hermes의 `streamingMarkdown.tsx`에서 영감. 스트리밍 중 완성된 마크다운 블록 즉시 렌더링.

**변경 파일:**
- `agentos/terminal/tui/widgets.py`:
  - `ChatMessage.update_streaming(chunk: str)`:
    - 현재: 청크를 `_streaming_text`에 누적 후 Static으로 표시 (평문)
    - 개선: 누적 텍스트에서 완성된 코드 블록(triple-backtick) 또는 테이블 블록 탐지 → `Markdown` 위젯으로 렌더링
    - `_has_open_code_block()` 헬퍼: 누적 텍스트에서 triple-backtick(```` ``` ````으로 시작하는 라인) 출현 횟수가 홀수이면 미완성으로 판정. 역따옴표 개수 합산이 아닌 fence 라인 수를 기준으로 탐지하여 인라인 코드 혼동 방지.
    - 완성된 블록만 Markdown 렌더링, 미완성 부분은 평문 유지
  - `ChatMessage.finalize_streaming()`: 변경 없음 (전체 Markdown 최종 렌더링)

**테스트 추가:** `test_streaming_markdown_partial_code_block`

---

## 이번 범위에 포함하지 않는 것 (Phase 4 이후 후보로 명시)

참조: `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md`

- **Diff 렌더러** — 파일 편집 도구 추가 선행 필요
- **이미지 프로토콜 (Kitty/Sixel)** — 터미널 호환성 이슈, 별도 조사 필요
- **설정 관리 UI** — 설정 스키마 정의 선행 필요
- **세션 압축 인디케이터** — 백엔드 압축 로직 선행 필요
- **서브에이전트 트리 시각화** — 멀티에이전트 아키텍처 선행 필요

---

## 리뷰 반영 이력

- 초안 작성 — 2026-07-22, Gate 2 리뷰 대기 중
- Gate 2 자기검토 (Antigravity fallback) — 2026-07-22T13:30Z:
  - PASS: 마일스톤 구조/범위/검증 기준 적절
  - 수정 1: 마일스톤 4 키 바인딩 `enter` → `f`로 변경 (기존 동작 충돌 방지)
  - 수정 2: 마일스톤 4 `events.py` 수정 불필요 명시 (이미 `parent_turn_id` 파라미터 존재)
  - 수정 3: 마일스톤 3 `thefuzz` `ImportError` 폴백 명시
  - 수정 4: 마일스톤 6 역따옴표 탐지 방법 fence 라인 기준으로 보강
  - 증거 파일: `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase3/self-review.md`

## 구현 결과

마일스톤 0~7 전체 구현 및 검증 완료:
1. **알림 배너 (Toast):** `_notify_error()`, `_notify_info()` 구현으로 Hook 오류, 세션 오류 발생 시 화면 상단 배너 전송.
2. **인디케이터 스타일 선택:** `SpinnerMessage` 클래스 추가 (ascii `|/-\`, unicode `⠋⠙⠹...`, emoji `⚕️🌀🤔✨`, kaomoji `(・・;)...`). `/indicator [style]`로 동적 전환 지원.
3. **자동완성 퍼지 검색:** `CommandPaletteScreen`에 실시간 `Input` 필터링 및 `thefuzz` 기반 optional ratio 정렬 기능 이식.
4. **분기 생성 UI:** `ChatMessage` 포커스 상태에서 `f` 키를 눌러 특정 턴 기준 분기 지정 가능 (`_pending_parent_turn_id`). 다음 메시지 입력 시 해당 턴을 부모로 하는 신규 분기 생성.
5. **모델 선택기 `/model`:** 런타임에 LLM 공급자 전환 (`/model mock|codex`).
6. **스트리밍 마크다운 점진적 렌더링:** `_has_open_code_block()`, `_has_complete_markdown_block()` 헬퍼로 fence 라인 수 기반 완성 블록 탐지 후 스트리밍 중 마크다운 즉시 렌더링.
7. **검증:** `uv run pytest tests/ -q` 통과 (114 passed), secret redaction 테스트 통과 (8 passed), `docs/cli-reference.md` 문서 동기화 완료.

## 사용 방법

- `/indicator [ascii|unicode|emoji|kaomoji]` - 로딩 스피너 애니메이션 스타일 변경
- `/model [mock|codex]` - 세션 런타임 LLM 공급자 변경
- `/` 입력 후 커맨드 팔레트에서 실시간 텍스트 검색
- ChatMessage 선택 후 `f` 키 입력 시 해당 턴부터 분기하여 새 메시지 전송

## 아카이브 결정

Phase 3의 모든 마일스톤 구현 및 114개 unit test / 8개 redaction test 검증 완료. `docs/cli-reference.md` 업데이트 완료. 구현 상태 완료로 전환 후 archive 디렉토리로 이동.
