# AgentOS TUI — pi TUI 격차 해소 (Phase 2) 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-22<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-21T23:03:47Z<br>
> implementation_completed_at: 2026-07-21T23:16:53Z<br>
> implementation_duration: 13m 6s<br>
> **usability_review_required:** true<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `2026-07-21-pi-tui-architecture-and-code-analysis.md`가 "Phase 2 이후 장기 적용 후보"로 분류했던 4개 항목(`/tree` 분기 탐색기, 도구별 커스텀 렌더러, 고도화된 diff 렌더러, 이미지 프로토콜) 중, 사용자 승인에 따라 **선행 조건을 포함해 실제로 구현 가능한 항목까지 범위를 확장**한다.
- 선행 조건 없이 즉시 구현 가능한 스트리밍 취소/로딩 인디케이터(pi의 `cancellable-loader.ts` 대응, 이번 계획에서 신규 발견)도 함께 포함한다.
- diff 렌더러와 이미지 프로토콜은 이번 계획에서도 범위 밖으로 유지한다(사유는 아래 "이번 범위에 포함하지 않는 것" 참조 — 사용자가 "Phase 2를 진행하기 위한 모든 작업"을 승인했으나, 이 두 항목은 선행 조건을 만들어도 활용할 대상(diff: 실제 파일 편집 도구, 이미지: 특수 터미널 프로토콜 호환성) 자체가 이번 계획 범위 밖의 별개 대형 작업이라 함께 묶으면 계획 하나의 크기가 검증 불가능한 수준으로 커진다).

**사용자 결과 요약:**
- **스트리밍 취소/로딩 인디케이터 (신규):** 메시지를 보낸 뒤 첫 응답 조각이 도착하기 전까지 회전 스피너와 "Thinking…" 표시가 나타나고, 이 대기 중 `Esc`를 누르면 진행 중이던 턴이 즉시 취소되고 대화창에 취소 표시가 남는다(지금은 대기 중 아무 표시가 없고 `Esc`가 세션 재개 오버레이에만 반응해, 응답이 오래 걸리면 멈춘 것처럼 보이고 취소할 방법이 없었다).
- **세션 분기(branch) 데이터 모델 (신규, 선행 조건):** 세션 저장 포맷에 각 턴이 어떤 이전 턴에서 갈라졌는지(`parent_turn_id`)를 기록하는 필드가 추가된다. 사용자에게는 아직 분기를 만드는 UI가 없으므로(이번 계획 범위 밖 UI는 다음 항목 참고) 평소 사용에는 변화가 없다 — 기존 세션 파일과 완전히 호환되며(필드 없으면 선형으로 취급), 다음 항목의 `/tree`가 이 데이터를 읽어 시각화한다.
- **`/tree` 분기 탐색기 (신규):** `/tree` 명령으로 현재 세션의 턴들을 ASCII 트리로 볼 수 있다. 현재 AgentOS는 사용자가 분기를 만드는 액션(예: 이전 턴으로 되돌아가 다른 메시지 보내기)이 없으므로, 이번 계획에서는 항상 선형 체인(가지가 하나뿐인 트리)으로 보인다 — 이는 의도된 결과이며, 향후 분기 생성 UI가 추가되면 같은 `/tree` 명령이 실제 분기도 그대로 보여준다.
- **도구별 커스텀 렌더러 아키텍처 (신규, 선행 조건 + 1개 예시 렌더러):** 도구 실행 결과를 항상 같은 형식의 평문(`Tool result: ...`)이 아니라, 도구 이름에 따라 다른 방식으로 보여줄 수 있는 확장 지점이 생긴다. 이번 계획에서는 이 확장 지점 자체와, 이를 사용하는 예시로 mock 공급자의 `mock_tool` 결과를 표 형태로 보여주는 렌더러 1개를 함께 구현해 아키텍처가 실제로 동작함을 보여준다. 등록되지 않은 도구는 지금처럼 평문(`Tool result: ...`)으로 계속 보인다 — 즉 화면이 바뀌는 도구는 `mock_tool` 하나뿐이고 나머지는 회귀 없이 그대로다.
- **바뀌지 않는 부분:** 세션 파일의 JSONL append-only 저장 방식, `agentos.session/v1`/`agentos.cli-event/v1` 스키마 버전 번호, 기존 슬래시 커맨드(`/hotkeys`, `/theme`, `/tools`, `/usage` 등)의 동작, LLM 공급자 인증/전송 방식은 바뀌지 않는다. 분기를 실제로 "만드는" UI(예: 이전 턴으로 되돌아가 재입력)는 이번 계획에 포함하지 않는다 — 데이터 모델과 조회(`/tree`)만 준비한다.
- **이번 범위에 포함하지 않는 것(다음 후보로 명시):** 분기 생성 UI(과거 턴에서 갈라지는 새 턴 만들기), 고도화된 diff 렌더러(실제 파일 편집 도구가 AgentOS에 없어 활용 대상 부재), Kitty/Sixel 이미지 프로토콜(터미널 호환성 이슈가 커 별도 조사 필요), 도구별 커스텀 렌더러의 추가 사례(파일 목록, 검색 결과 등 — 아키텍처만 이번에 만들고 확장은 이후 계획에서 점증적으로 추가).

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 새 패키지, 새 자격증명, 새 네트워크 호출 없음. 기존 Textual 8.2.8, Rich, 기존 세션 저장 파일 포맷만 사용한다.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `agentos/terminal/events.py`, `agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/state.py`, `agentos/terminal/tui/commands.py`, `agentos/terminal/tui/renderers.py`, `docs/cli-reference.md`, `.agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md`(Phase 2 진행 상태 갱신)

**진행 상태:** 완료 — 마일스톤 1~6 구현 및 검증 완료

**아키텍처:**
- **스트리밍 취소/로딩 인디케이터:**
  - `state.py`: `TuiStatus`에 새 필드 없음(턴 진행 여부는 `app.py`가 소유). `AgentOSTui.__init__`에 `self._active_turn_worker: Worker | None = None`을 추가(취소 여부 판정은 별도 플래그 없이 `Worker.is_cancelled`를 단일 진실 소스로 사용 — 아래 참조).
  - `app.py`: 메시지 전송 시 `Transcript`에 로딩 표시용 임시 메시지(`role="loading"`, 텍스트 "Thinking…")를 즉시 추가하고, 첫 `reasoning`/`tool_call`/`message_delta` 이벤트 도착 시 이 로딩 메시지를 제거(`Transcript.remove_message`)한다. `run_stream`은 `@work(thread=True)`로 시작되며 시작 시 `self._active_turn_worker = get_current_worker()`(Textual `textual.worker.get_current_worker()`)로 자기 자신의 `Worker` 핸들을 저장한다. `action_cancel()`을 확장해, 세션 재개 오버레이가 열려있지 않고 `self._active_turn_worker is not None and self._active_turn_worker.is_running`이면 `self._active_turn_worker.cancel()`을 호출하고, transcript에 "Turn cancelled." 메시지를 추가하며 로딩 메시지를 제거한다. `run_stream`의 스트림 `for` 루프는 매 이벤트 처리 전 `get_current_worker().is_cancelled`를 확인해 `True`면 즉시 반복을 중단한다(단일 메커니즘: `Worker.cancel()`→`is_cancelled` 플래그, 별도의 커스텀 불리언 플래그를 추가로 두지 않는다 — 이는 Textual의 표준 협조적 취소 패턴이며, `codex_cli.py::_run_codex`의 `timeout` 기반 subprocess 강제 종료와는 다른 계층이다. 이번 계획은 `codex` 공급자의 subprocess 강제 kill 로직을 변경하지 않는다 — 취소 시 스트림 소비를 중단하면 파이프가 닫히며 subprocess가 자연 종료되는 기존 동작에 맡기고, 범위를 TUI 레이어의 협조적 취소로 한정한다).
  - `widgets.py`: `ChatMessage.loading`(테두리 없음, 회전 스피너 문자 애니메이션은 Textual 내장 `LoadingIndicator` 위젯을 재사용하거나 텍스트 스피너 프레임 리스트로 최소 구현 — 복잡한 커스텀 애니메이션 엔진을 만들지 않는다) CSS 클래스와 `Transcript.remove_message(message: ChatMessage)` 메서드(위젯 트리에서 해당 자식만 제거) 추가.
  - **인앱 도움말 텍스트 동기화(usability-reviewer 지적 반영):** Esc의 동작이 "오버레이 닫기만"에서 "대기 중인 턴도 취소"로 바뀌므로, 사용자가 실제로 참조하는 세 곳의 안내 문구를 함께 갱신한다 — 그러지 않으면 사용자가 잘못된 정보를 보고 의도치 않게 진행 중 턴을 취소하거나(비가역), 취소가 가능한 줄 몰라 응답이 멈춘 것처럼 오인할 수 있다.
    - `app.py:24-40`의 `_HOTKEYS_TABLE` 문자열: `Esc               Cancel / close overlay` 줄을 `Esc               Cancel turn (while waiting) / close overlay`로 갱신.
    - `app.py:130-133`의 `/help` 배너 텍스트: `"Ctrl-C cancels a turn.\nEsc closes overlays. EOF exits..."`를 `"Ctrl-C cancels a turn.\nEsc cancels a waiting turn or closes overlays. EOF exits..."`로 갱신.
    - `app.py:448`의 non-TTY 콘솔 안내 문구: 동일한 문장으로 `console.print(...)` 텍스트를 갱신.
- **세션 분기 데이터 모델:**
  - `events.py`: `CliEvent`(현재 9개 필드: `type`/`session_id`/`turn_id`/`provider`/`mode`/`payload`/`metadata`/`timestamp`/`schema_version`)에 `parent_turn_id: str | None = None` 필드를 새로 추가하고 `to_dict()`의 반환 dict에도 `"parent_turn_id": self.parent_turn_id`를 포함시킨다. `wrap_provider_event(event, *, session_id, turn_id, provider, mode, parent_turn_id=None)`에 새 키워드 인자를 추가해 `CliEvent(...)` 생성 시 그대로 전달한다(기존 호출부는 `parent_turn_id`를 생략하면 `None`이 기본값이므로 하위 호환 유지). `CLI_EVENT_SCHEMA_VERSION`("agentos.cli-event/v1")은 필드 추가만으로는 변경하지 않는다 — 기존 소비자는 새 키를 무시할 수 있는 JSON object 구조이므로 하위 호환.
  - `sessions.py`: `append_event()` 자체는 이미 완성된 `event: dict`를 그대로 파일에 쓰는 얇은 함수이므로 시그니처를 바꾸지 않는다. `parent_turn_id`는 `sessions.py`가 아니라 호출부인 `app.py`의 `run_stream()`이 `wrap_provider_event(..., parent_turn_id=self._last_turn_id)` 형태로 채워 넣는다(`self._last_turn_id: str | None`을 `AgentOSTui.__init__`에서 `None`으로 초기화하고, 매 턴 종료 시 해당 턴의 `turn_id`로 갱신 — 다음 턴 전송 시 그 값을 `parent_turn_id`로 사용). 이번 계획에서는 분기를 만드는 UI가 없으므로 실제로는 항상 "바로 이전 턴"이 부모가 된다(선형 체인).
  - 기존 세션 파일(이 필드가 없는 JSONL 라인)을 읽을 때는 `dict.get("parent_turn_id")`로 조회해 `None`으로 취급한다.
- **`/tree` 분기 탐색기 (마일스톤 2 완료 후에만 착수 가능 — 마일스톤 2가 기록하는 `parent_turn_id`가 없으면 트리를 구성할 그래프 엣지 자체가 없다):**
  - `commands.py`: `/tree` 슬래시 커맨드 추가.
  - `app.py`: `/tree` 핸들러가 `read_session(session_id)`로 현재 세션의 이벤트를 읽어 각 이벤트의 `turn_id`/`parent_turn_id`(`.get()`으로 안전 조회, 없으면 `None`) 쌍으로 부모-자식 그래프를 만들고, 루트부터 들여쓰기 기반 ASCII 트리 문자열(예: `├─`, `└─`, `│`)로 렌더링해 transcript에 표시한다. 트리 렌더링 로직은 순수 함수 `render_turn_tree(events: list[dict]) -> str`로 `renderers.py`에 추가해 위젯 마운트 없이 단위 테스트 가능하게 한다. 현재 턴이 없으면 `"No turns yet. Next: send a message."`를 표시한다(다른 empty-state 문구와 동일한 패턴).
- **도구별 커스텀 렌더러 아키텍처:**
  - `renderers.py`: 기존 `render_event(payload)`(고정 문구 렌더링)와 별개로, `TOOL_RENDERERS: dict[str, Callable[[dict], str]]` 레지스트리와 `register_tool_renderer(name: str, renderer: Callable[[dict], str])` 함수를 추가. **디스패치 순서(principle-auditor 지적 반영, Secret/Env Governance 고정):** `render_event()` 내부의 기존 `safe = sanitize(event)` 줄 **이후**, `tool_result` 분기에서 `metadata = safe.get("metadata") or {}`로 이미 계산된 `safe`/`metadata`를 그대로 커스텀 렌더러에 전달한다 — 즉 `TOOL_RENDERERS`를 조회하고 호출하는 코드는 `sanitize()` 호출 지점보다 아래(이후)에 위치해야 하며, `app.py` 등 호출부에서 raw `payload`를 직접 커스텀 렌더러에 넘기는 경로를 만들지 않는다(그러면 sanitize가 우회된다). `metadata.get("name")`이 레지스트리에 있으면 해당 렌더러에 `safe`(sanitize를 거친 dict)를 넘겨 호출하고, 없으면 기존 고정 문구(`Tool result: {summary}`) 경로를 그대로 사용한다(fallback 보장 — 회귀 없음).
  - 예시 렌더러: `render_mock_tool_table(safe_payload: dict) -> str`을 구현해 `mock_tool`의 결과를 파이프 구분 표 형태(`| field | value |`)로 렌더링하고, 모듈 로드 시 `register_tool_renderer("mock_tool", render_mock_tool_table)`로 등록한다. 이 렌더러는 이미 sanitize를 거친 dict만 인자로 받으므로 별도의 sanitize 호출을 다시 하지 않는다(중복 sanitize 방지, 단일 경로 유지).
- `docs/cli-reference.md`: `/tree` 명령, 스트리밍 취소(Esc) 동작, 커스텀 렌더러 존재를 문서화.
- `.agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md`: "Phase 2 이후 장기 적용 후보" 섹션에 이번 계획으로 착수/완료된 항목(분기 데이터 모델, `/tree`, 커스텀 렌더러 아키텍처, 스트리밍 취소)과 여전히 범위 밖인 항목(분기 생성 UI, diff 렌더러, 이미지 프로토콜)을 갱신.

**기술 스택:**
- Python 3.12, Textual 8.2.8 (`pyproject.toml` 요구사항: `textual>=6.0.0`), Rich

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 마일스톤 1~6 구현 완료, 전체 테스트 및 tmux 수동 시연으로 검증 완료 |
| 완료됨 | Gate 2 3라운드 독립 서브에이전트 리뷰 PASS(reviewed: true), 마일스톤 1~6 구현(스트리밍 취소/로딩, `parent_turn_id`, `/tree`, 도구별 렌더러, 문서 갱신), 전체 테스트 107 passed, tmux 수동 시연 |
| 현재 위치 | 구현 완료. 사용자 확인 대기 |
| 다음 단계 | 사용자 요청 시 archive/commit/PR 준비 |
| 완료 신호 | 스트리밍 중 로딩 표시와 Esc 취소가 동작하고, `/tree`가 턴 트리를 보여주고, `mock_tool` 결과가 표로 렌더링되며, 전체 테스트가 통과하고, tmux 세션에서 각 기능이 수동으로 시연됨 — 모두 충족(`## 완료 증거` 참고) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 스트리밍 취소/로딩 인디케이터 | 메시지 전송 후 첫 응답 조각 전까지 "Thinking…" 로딩 표시가 보이고, 이 상태에서 `Esc`를 누르면 즉시 "Turn cancelled."가 표시되며 로딩 표시가 사라짐. `/hotkeys`, `/help`, non-TTY 안내 문구도 Esc의 새 동작(대기 중인 턴 취소)을 정확히 설명함 | `agentos/terminal/tui/app.py`(`_HOTKEYS_TABLE`, `/help` 배너, non-TTY 안내문 포함), `agentos/terminal/tui/widgets.py` | `Run:` `uv run pytest tests/test_tui_cli.py -k "loading or cancel_turn" -q` / `Expected:` PASS (로딩 메시지가 첫 이벤트 도착 시 사라짐, `Esc` 취소 시 "Turn cancelled." 메시지와 로딩 제거 모두 검증). `Run:` `grep -n "Cancel turn\|cancels a waiting turn" agentos/terminal/tui/app.py` / `Expected:` `_HOTKEYS_TABLE`, `/help` 배너, non-TTY 안내문 세 곳 모두에서 발견됨(usability-reviewer 지적 반영 확인) |
| 2. 세션 분기 데이터 모델 | 사용자가 직접 체감하는 화면 변화는 없음(하위 호환 확인용) — 기존 세션을 열어도 그대로 동작함 | `agentos/terminal/events.py`, `agentos/terminal/tui/app.py` | `Run:` `uv run pytest tests/ -k "test_parent_turn_id" -q` / `Expected:` PASS. 신규 테스트는 모두 `test_parent_turn_id_...`로 명명(예: `test_parent_turn_id_defaults_to_none_for_legacy_events`, `test_parent_turn_id_set_to_previous_turn_id`, `test_wrap_provider_event_accepts_parent_turn_id`) — 기존 무관 세션/이벤트 테스트와 매치되지 않음을 사전에 `grep -rn "def test_" tests/ | grep -i "session\|event"`로 확인 |
| 3. `/tree` 분기 탐색기 (마일스톤 2 완료 후 착수) | `/tree` 입력 시 현재 세션의 턴들이 들여쓰기 트리로 나타남(분기 생성 UI가 없으므로 항상 단일 체인). 턴이 없으면 안내 문구가 보임 | `agentos/terminal/tui/commands.py`, `agentos/terminal/tui/app.py`, `agentos/terminal/tui/renderers.py`, `docs/cli-reference.md` | `Run:` `uv run pytest tests/test_tui_cli.py -k tree -q` / `Expected:` PASS (빈 상태, 단일 체인 렌더링 모두 검증). `Run:` `grep -n "/tree" docs/cli-reference.md` / `Expected:` 발견됨 |
| 4. 도구별 커스텀 렌더러 아키텍처 | `mock_tool` 실행 결과가 기존 평문 대신 표 형태로 보임. 다른 도구(등록되지 않은 이름)는 기존과 동일한 평문으로 계속 보임(회귀 없음) | `agentos/terminal/tui/renderers.py` | `Run:` `uv run pytest tests/test_tui_cli.py -k "tool_renderer or mock_tool_table" -q` / `Expected:` PASS (등록된 도구는 표, 미등록 도구는 기존 평문 경로로 fallback함을 각각 검증). `Run:` `AGENTOS_TEST_SECRET=AGENTOS_SENTINEL_SECRET uv run pytest tests/test_tui_cli.py -k test_mock_tool_table_redacts_secret -q` / `Expected:` PASS — `mock_tool` 결과 payload에 시크릿 문자열을 넣어 `render_event()`를 호출했을 때 표 렌더링 출력에 시크릿 원문이 아니라 redaction 마스크만 나타나는지 전용으로 검증하는 신규 테스트(principle-auditor 지적 반영: 기존 `-k redact` 테스트는 이 신규 코드 경로를 실행하지 않으므로 별도 필요) |
| 5. 문서/레퍼런스 갱신 | `docs/cli-reference.md`에 `/tree`와 취소 동작이 반영되고, pi TUI 레퍼런스 문서의 Phase 2 후보 섹션이 이번 계획의 진행 상태로 갱신됨 | `docs/cli-reference.md`, `.agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md` | `Run:` `grep -n "/tree\|Esc.*취소\|cancel" docs/cli-reference.md` / `Expected:` 발견됨. `Run:` `grep -n "Phase 2" ".agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md"` / `Expected:` 갱신된 상태 문구 발견 |
| 6. 전체 안정성 검증 및 tmux 시연 | 기존 TUI 명령어와 LLM 상호작용이 깨지지 않고, tmux 세션에서 로딩/취소/`/tree`/표 렌더링이 실제로 동작함을 눈으로 확인 가능 | 전체 테스트 스위트 + tmux 수동 시연 | `Run:` `uv run pytest tests/ -q` / `Expected:` 전체 PASS. `Run:` `tmux new-session -d -s <name> 'uv run agentos --provider mock'` 후 메시지 전송/Esc/`/tree`/`/tools` 순서로 `tmux send-keys` + `tmux capture-pane -p` 확인 / `Expected:` 각 화면에서 로딩 표시, 취소 문구, 트리, 표 렌더링이 순서대로 보임 |

## 리뷰 반영 이력
- (초안) 레퍼런스 문서(`2026-07-21-pi-tui-architecture-and-code-analysis.md`)의 "Phase 2 이후" 후보 4개를 재검토한 결과, 모두 AgentOS에 없는 선행 기능(분기 세션 모델, 플러그인 아키텍처, 파일 편집 도구, 특수 터미널 프로토콜)을 전제로 함을 확인. 사용자에게 범위 확인 질문(`AskUserQuestion`)을 거쳐 "phase2를 진행하기 위한 모든 작업을 진행하자"는 승인을 받아, 선행 조건(분기 데이터 모델, 커스텀 렌더러 아키텍처)까지 포함하는 확장 범위로 계획을 작성함. diff 렌더러와 이미지 프로토콜은 선행 조건을 만들어도 활용 대상 자체가 없거나(diff: 편집 도구 부재) 별도의 대형 호환성 조사가 필요해(이미지: 터미널 프로토콜) 이번 계획에서도 명시적으로 범위 밖으로 유지. 계획 진행 중 pi TUI 레퍼런스 코드에서 기존 문서에 없던 `cancellable-loader.ts` 대응 격차(스트리밍 취소/로딩 인디케이터)를 신규 발견해 마일스톤 1로 추가.
- Gate 2 리뷰(plan-reviewer/principle-auditor/usability-reviewer)가 완료되면 `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase2/`에 증거 파일을 생성한다.
- **1차 plan-reviewer 리뷰:** FAIL(블로킹 4건). 증거: `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase2/plan-reviewer.md`. 핵심 지적: (1) `agentos/terminal/events.py`의 `CliEvent`/`wrap_provider_event()`에 실제로 `parent_turn_id` 필드가 없는데 계획이 있는 것처럼 서술함 — 구현 시 즉시 `TypeError` 발생. (2) 마일스톤 2 검증의 `-k "parent_turn_id or session"`이 기존 무관 세션 테스트와 매치될 위험. (3) 마일스톤 3(`/tree`)이 마일스톤 2에 의존하는데 순서 의존성이 명시되지 않음. (4) `self._active_turn_worker`와 `self._turn_cancelled` 두 취소 메커니즘이 혼용 서술됨.
  - 대응: `events.py`를 Durable Result Surface/마일스톤 2 owner surface에 추가하고, `CliEvent`에 `parent_turn_id: str | None = None` 필드와 `wrap_provider_event(..., parent_turn_id=None)` 키워드 인자를 신설하는 것으로 아키텍처를 정정함(`sessions.py`는 변경 대상에서 제외 — `append_event`는 이미 완성된 dict를 쓰기만 하는 얇은 함수라 그대로 둠). 마일스톤 2 검증을 `-k "test_parent_turn_id"`로 좁히고 신규 테스트 명명 규칙을 명시함. 마일스톤 3 제목에 "(마일스톤 2 완료 후 착수)"를 명시함. 취소 메커니즘을 `Worker.cancel()`→`get_current_worker().is_cancelled` 단일 경로로 통일하고 별도 불리언 플래그를 제거함.
  - **프로세스 고지(항목 0, 정정됨):** 이 1차 리뷰는 계획 작성자 본인이 plan-reviewer 역할을 자기검토(self-review)로 수행한 것이었다. `.agents/vendors/claude.md`는 Task/Agent 도구가 사용 가능한 Claude Code 환경에서 자기검토 fallback을 명시적으로 금지하므로, 이 1차 라운드는 유효한 Gate 2 증거로 인정하지 않는다. 아래 2차 라운드에서 독립 서브에이전트(Agent 도구, `general-purpose` subagent, 계획 작성자와 분리된 별도 컨텍스트) 3개를 병렬로 호출해 plan-reviewer/principle-auditor/usability-reviewer를 다시 수행했다.
- **2차 Gate 2 리뷰 (독립 서브에이전트, 정식):**
  - **plan-reviewer:** FAIL. 1차에서 지적된 4건(아키텍처 불일치, 검증 커맨드 범위, 마일스톤 순서 의존성, Worker 취소 메커니즘 혼용)은 실제 코드(`events.py`, `app.py`, `textual.worker`)와 대조 검증한 결과 모두 정확히 반영되어 있음을 독립적으로 재확인했다. 유일한 블로킹 사유는 계획 문서에 `usability-reviewer=PASS` 증거가 없다는 점이었다(usability-reviewer가 아래처럼 별도로 FAIL을 냈으므로 이 지적은 그대로 유효).
  - **principle-auditor:** REVISE. P1-P4/Protected Path/Runtime Contract Governance는 모두 통과. 유일한 지적: `mock_tool` 표 렌더러가 `sanitize()`를 거친다는 주장이 `render_event()` 내부의 정확히 어느 지점(디스패치 순서)에서 안전한 dict를 넘기는지 명시되지 않았고, 전용 시크릿 리댁션 테스트도 없어 Secret/Env Governance 게이트 기준으로 REVISE. 대응: 위 "도구별 커스텀 렌더러 아키텍처" 절에 `TOOL_RENDERERS` 디스패치가 `render_event()`의 `safe = sanitize(event)` 이후에 위치해야 함을 명시하고, 마일스톤 4 검증에 `test_mock_tool_table_redacts_secret` 전용 테스트를 추가함.
  - **usability-reviewer:** FAIL. Esc가 대기 중인 턴도 취소하도록 바뀌는데, 사용자가 실제로 참조하는 인앱 도움말(`_HOTKEYS_TABLE`, `/help` 배너, non-TTY 안내문 — 모두 `app.py` 내)이 갱신 대상에서 빠져 실수로 진행 중 턴을 취소할 위험이 있다고 지적. 대응: 위 "스트리밍 취소/로딩 인디케이터" 아키텍처 절과 마일스톤 1 owner surface/검증에 `app.py:24-40`, `app.py:130-133`, `app.py:448` 세 곳의 문구 갱신과 grep 검증을 추가함.
  - 세 리뷰 모두 신규 증거 파일: `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase2/{plan-reviewer,principle-auditor,usability-reviewer}.json`(`review_artifacts.py record`로 생성, plan_sha256/reviewer_id/reviewer_source/summary/reviewed_at 포함). 위 3건 수정 반영 후 3차 독립 서브에이전트 리뷰를 재실행해 PASS를 확보해야 `reviewed: true` 전이가 가능하다.
- **3차 Gate 2 리뷰 (독립 서브에이전트, 최종):** 위 2차 라운드의 3건 수정을 반영한 뒤, 별도의 신규 독립 서브에이전트 3개(계획 작성자와 분리된 컨텍스트, 이전 대화 기억 없음)를 다시 병렬 호출해 재검증했다.
  - **plan-reviewer:** PASS. Esc 도움말 3곳(`app.py:24-40/130-133/448`)의 인용 문구·신규 문구·grep 검증이 실제 소스와 정확히 일치함을 재확인, `TOOL_RENDERERS`의 `sanitize()` 이후 디스패치 순서와 `test_mock_tool_table_redacts_secret` 전용 테스트도 확인. (비블로킹 참고: tmux가 `의존성 게이트`에 별도 선언되지 않았으나, 마일스톤 6의 핵심 자동 검증은 tmux 없이도 완결되므로 블로킹 아님으로 판단.)
  - **principle-auditor:** PASS. `renderers.py`/`redaction.py` 실측 대조로 REVISE 사유(디스패치 위치, 전용 테스트 부재) 완전 해소 확인. 마일스톤 1 확장(Esc 도움말 동기화)도 순수 문자열 동기화로 신규 원칙 위반 없음.
  - **usability-reviewer:** PASS. Esc 도움말 3곳의 인용/신규 문구가 실제 소스와 일치하며, 오버레이가 열려 있고 턴이 대기 중인 동시 상태에서도 오버레이 닫기가 우선되어 실수로 턴이 취소되지 않음을 코드로 확인(`app.py`의 아키텍처 절 "세션 재개 오버레이가 열려있지 않고" 조건). 블로킹 없음.
  - **Gate 2 자동 체크리스트 형식 버그 발견 및 수정:** 3차 리뷰 중 plan-reviewer가 `.agents/traces/reviews/2026-07-22-tui-pi-clone-phase2/`에 1차(자기검토, 무효) 산출물 외 유효한 `.json` 증거가 없음을 지적했다. 이를 계기로 `review_artifacts.py check`를 직접 실행해보니 `reviewers=plan-reviewer,principle-auditor`만 출력되고 `usability-reviewer`가 요구 목록에서 누락됨을 발견 — 원인은 헤더의 `> usability_review_required: true<br>` 줄에 굵게(`**...**`) 마크업이 없어 `USABILITY_REQUIRED_RE`(`^> \*\*usability_review_required:\*\* true...$`) 정규식이 매치하지 못했기 때문이다. 헤더를 `> **usability_review_required:** true<br>`로 수정해 재확인한 결과 `reviewers=plan-reviewer,principle-auditor,usability-reviewer`로 정상 인식됨을 확인했다.
  - `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py record`로 3개 역할 모두 `.json` 증거 파일을 기록했고(`reviewer_id=subagent-{role}-20260722-2`, `implementer_id=claude-main-session-tui-phase2`), `review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-22-tui-pi-clone-phase2.md` 실행 결과 `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`를 확인했다. 이에 따라 헤더를 `reviewed: true`, `> **상태:** 구현 계획 (실행 대기)`로 전이한다.

## 구현 결과

마일스톤 1~6을 순서대로 구현했다.

- **스트리밍 취소/로딩 인디케이터**: 메시지 전송 후 첫 응답 조각 전까지 "Thinking…" 로딩 메시지가 표시되고, 이 상태에서 `Esc`를 누르면 Textual의 `Worker.cancel()`/`get_current_worker().is_cancelled` 협조적 취소로 즉시 턴이 취소되며 "Turn cancelled."가 표시된다. `/hotkeys`, `/help`, non-TTY 안내 문구도 Esc의 새 동작을 반영하도록 함께 갱신했다(`agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`).
- **세션 분기 데이터 모델**: `agentos/terminal/events.py`의 `CliEvent`에 `parent_turn_id: str | None = None` 필드와 `wrap_provider_event(..., parent_turn_id=None)` 키워드 인자를 추가했다. 기존 세션 파일(필드 없음)은 `.get()` 조회로 `None` 취급되어 하위 호환된다.
- **`/tree` 분기 탐색기**: `/tree` 명령으로 현재 세션의 턴을 들여쓰기 ASCII 트리로 볼 수 있다(`agentos/terminal/tui/renderers.py::render_turn_tree`). 분기 생성 UI가 아직 없어 항상 단일 체인으로 보이지만, 렌더링 함수 자체는 실제 분기 데이터가 주어지면 올바르게 여러 갈래를 그린다(단위 테스트로 검증).
- **도구별 커스텀 렌더러 아키텍처**: `renderers.py`에 `TOOL_RENDERERS` 레지스트리와 `register_tool_renderer()`를 추가하고, `mock_tool` 결과를 `| field | value |` 표로 렌더링하는 예시 렌더러를 등록했다. 등록되지 않은 도구는 기존과 동일한 평문(`Tool result: ...`)으로 계속 렌더링된다.
- **구현 중 발견 및 수정한 항목(계획 대비 보강)**:
  - `agentos/llm/providers/mock.py`의 `tool_result` 이벤트 metadata에 `name` 필드가 없어 도구별 렌더러 디스패치가 동작하지 않는 것을 구현 중 발견했다. `metadata={"name": "mock_tool", "summary": ...}`로 보강해 예시 렌더러가 실제로 동작하도록 했다(계획의 Durable Result Surface에는 없었으나, 승인된 아키텍처를 실제로 동작시키기 위한 최소 보강).
  - 기존 테스트 `test_transcript_shows_process_events_before_final_answer`가 `mock_tool`의 옛 평문 출력을 검증하고 있어, 새 표 형식에 맞게 갱신했다(계획에서 의도한 화면 변화이므로 예상된 조정).

## 사용 방법

`uv run agentos --provider mock` (또는 실제 provider)로 TUI를 실행한다.
- 메시지를 보내면 응답 도착 전까지 "Thinking…"이 보인다. 대기 중 `Esc`를 누르면 턴이 취소된다.
- `/tree`를 입력하면 현재 세션의 턴 트리가 보인다.
- 도구 실행 결과 중 `mock_tool`은 표 형태로, 그 외 도구는 기존과 동일한 평문으로 보인다.
- `/hotkeys`, `/help`에서 갱신된 Esc 동작 설명을 확인할 수 있다.

## 완료 증거

- `Run:` `uv run pytest tests/test_tui_cli.py -k "loading or cancel_turn" -q` / `PASS` (2 passed)
- `Run:` `uv run pytest tests/ -k "test_parent_turn_id" -q` / `PASS` (4 passed)
- `Run:` `uv run pytest tests/test_tui_cli.py -k tree -q` / `PASS` (4 passed)
- `Run:` `uv run pytest tests/test_tui_cli.py -k "tool_renderer or mock_tool_table" -q` / `PASS` (3 passed)
- `Run:` `AGENTOS_TEST_SECRET=AGENTOS_SENTINEL_SECRET uv run pytest tests/ -k redact -q` / `PASS` (8 passed)
- `Run:` `grep -n "/tree\|Esc.*취소\|cancel" docs/cli-reference.md` / 발견됨
- `Run:` `grep -n "Phase 2" ".agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md"` / 갱신된 상태 문구 발견됨
- `Run:` `uv run pytest tests/ -q` / `PASS` 107 passed, 1 deselected(`tests/test_cli.py::test_setup_command`은 이 계획과 무관한 사전 존재 ANSI 컬러 코드 환경 의존 실패로, `git stash`로 되돌린 베이스라인에서도 동일하게 실패함을 확인)
- tmux 수동 시연(`agentos-phase2-demo` 세션): 메시지 전송 → `Tool call:`/`| field | value |` 표 렌더링 확인, `/tree` 1턴/2턴 선형 체인 렌더링 확인, `/hotkeys`에서 "Cancel turn (while waiting) / close overlay" 문구 확인. Esc 취소는 mock provider가 지연 없이 즉시 완료되어 tmux 수동 타이밍으로는 재현되지 않았으나, 동일 메커니즘을 제어된 지연(`threading.Event`)으로 정밀 검증하는 자동 테스트(`test_escape_cancel_turn_stops_further_output`)로 확인됨.

## 아카이브 결정

구현과 검증이 모두 완료되어 이 계획을 `완료` 상태로 표시한다. 사용자가 명시적으로 archive를 요청하면 `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py archive .agentos/project/exec-plans/active/2026-07-22-tui-pi-clone-phase2.md --status 완료`로 이동한다.
