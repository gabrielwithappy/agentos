# AgentOS TUI 심층 UX/UI 개선 (Pi TUI 아키텍처 완벽 대응)

> **상태:** 완료

## [Goal Description]
Pi TUI 코드베이스에 대한 심층 분석(`pi_tui_analysis.md` 참고) 결과, Pi TUI는 단순한 UI 프레임워크가 아닌 Undo Stack, Kill Ring, 페이스트 압축 마커, 인라인 자동완성, IME 커서 동기화 등 극한의 에디터 UX를 자체 구현한 시스템임이 확인되었습니다.

본 계획의 목표는 사용자 관점에서 **Pi TUI와 AgentOS TUI(Textual 기반)의 사용 만족도를 100% 동일한 수준까지 끌어올리는 것**입니다. 이를 위해 Textual의 렌더링 이점을 살리되, 부족한 에디터 UX와 대화 히스토리 처리 방식을 다단계(Phase 1~3)로 나누어 근본적으로 재설계 및 구현합니다.

## User Review Required

> [!IMPORTANT]
> 본 계획은 AgentOS TUI의 아키텍처를 대대적으로 변경합니다. 전체 목표 달성을 위해 아래 3단계로 나누어 점진적으로 구현을 진행합니다.
> - **Phase 1 (이번 반복):** 대화 히스토리 누적(수직 스크롤) 및 스트리밍 완료 시 마크다운(Rich Text) 렌더링.
> - **Phase 2 (다음 반복):** `Composer` 위젯 내부에 Undo/Redo 스택, Emacs 키바인딩(Kill Ring), 대용량 텍스트 페이스트 마커 로직 이식.
> - **Phase 3 (최종 반복):** 플로팅 오버레이 기반 자동완성(`/`, `Tab`) 및 한/영 입력기(IME) 커서 튐 현상 방지 동기화.
> 현재는 **Phase 1** 구현에 착수하기 위한 준비가 완료되었습니다. 동의하시면 즉시 Phase 1 코드를 작성하겠습니다.

## Proposed Changes (Phase 1: 대화 로그 및 마크다운 렌더링)

### `agentos/terminal/tui/widgets.py`
- **[MODIFY] Transcript 위젯:** 
  - 부모 클래스를 `Static`에서 `VerticalScroll`로 변경하여 스크롤 가능한 대화 로그 컨테이너로 전환.
  - 새 메시지가 올 때마다 화면을 덮어쓰지 않고 `self.mount()`를 통해 하단에 메시지를 누적.
- **[NEW] ChatMessage 위젯:** 
  - `Static`을 상속받는 단위 메시지 위젯.
  - 내부 상태로 `role` (user/assistant)을 가져 배경색과 여백을 다르게 렌더링.
  - `update_text(text: str)` 메서드를 두어 스트리밍 중에는 평문을 업데이트하고, 턴이 종료(done)되면 내부 텍스트를 `rich.markdown.Markdown(text)` 객체로 변환하여 코드 하이라이팅 적용.

### `agentos/terminal/tui/app.py`
- **[MODIFY] 입력 처리 로직 (`on_composer_submitted`):**
  - 사용자 입력을 받으면 `Transcript`에 사용자의 `ChatMessage`를 즉시 마운트.
  - LLM 응답 대기용 빈 `ChatMessage`를 추가로 마운트한 뒤 참조(Reference)를 `run_stream`으로 전달.
- **[MODIFY] 렌더링 라우팅 (`run_stream`):**
  - 스트리밍 청크가 도착할 때마다 전달받은 `ChatMessage`의 내용을 갱신.
  - 갱신 후 `Transcript.scroll_end()`를 호출하여 항상 최신 텍스트가 보이도록 오토 스크롤 구현.

## Proposed Changes (Phase 2: 고급 에디터 UX - Undo, Kill Ring, Paste Marker)

### `agentos/terminal/tui/widgets.py`
- **[MODIFY] Composer (TextArea 상속) 확장:**
  - **Undo Stack 구현:** `on_key` 이벤트에서 입력 상태를 주기적(스페이스 입력 등)으로 스택에 저장하고, `Ctrl+Z`, `Ctrl+Y` 입력 시 복구/재실행하는 로직 구현.
  - **Kill Ring (Emacs 키바인딩):** `Ctrl+K`(줄 끝까지 삭제), `Ctrl+U`(줄 처음까지 삭제), `Alt+Backspace`(단어 삭제) 입력 시 삭제된 텍스트를 자체 `kill_ring` 리스트에 저장. `Ctrl+Y` 입력 시 버퍼에서 꺼내어 붙여넣기(Yank) 동작 구현.
  - **Paste Marker (대용량 붙여넣기 압축):** Textual의 `Paste` 이벤트를 가로채어, 클립보드 텍스트가 10줄 이상일 경우 실제 화면(TextArea)에는 `[paste #1 +N lines]` 마커 텍스트만 삽입. 내부 딕셔너리에 마커 ID와 실제 텍스트를 맵핑하여, 폼 제출(`Submitted`) 시 원본 텍스트로 치환하여 전송하도록 래핑.

## Proposed Changes (Phase 3: 자동완성 오버레이 및 IME 최적화)

### `agentos/terminal/tui/widgets.py` & `app.py`
- **[NEW] AutocompleteOverlay 위젯:**
  - `OptionList`를 포함하는 플로팅(Floating) 컨테이너 위젯 추가. `Composer`의 현재 커서 위치를 추적하여 화면 상 적절한 좌표에 `layer="overlay"` 형태로 띄움.
- **[MODIFY] Composer 자동완성 트리거 로직:**
  - 입력창 맨 앞에서 `/` 입력 시 명령어(Command) 리스트 오버레이 호출.
  - 입력 도중 `Tab` 입력 시 현재 입력된 단어를 기반으로 파일 시스템 경로(File Path)를 읽어와 오버레이에 파일 목록 출력.
  - 상하 방향키(`Up/Down`) 입력을 가로채어 오버레이 내의 옵션을 탐색하도록 Focus 위임.
- **IME 동기화 튜닝 (연구/적용):**
  - Textual 프레임워크가 제공하는 기본 커서 렌더링 방식 분석 후, 한글 입력 시 가상 커서와 하드웨어 커서 간의 간극을 줄일 수 있는 시퀀스 패치(필요시 Pi TUI의 `CURSOR_MARKER` 방식 모방) 적용 검토.

## Verification Plan
- **Phase 1:** `uv run agentos --provider codex` 대화 누적 및 마크다운 정상 작동 확인.
- **Phase 2:** 에디터에서 대용량 텍스트 붙여넣기 시 마커 생성 여부, `Ctrl+K/U/Y` 및 `Ctrl+Z` 단축키 정상 동작 확인.
- **Phase 3:** `/` 및 `Tab` 키로 오버레이 팝업 노출 및 파일/명령어 선택 정상 동작 확인.

## 아카이브 결정 (2026-07-21)
- **사유:** Phase 1(대화 히스토리/마크다운 렌더링)과 Phase 2(Undo, Kill Ring, Paste Marker)는 이후 커밋(`6d2ebd7`, `b018cea`, `f08ce29`, `9f6c42c`)과 `.agentos/project/exec-plans/2026-07-21-tui-transcript-improvement.md`(완료 처리됨)에서 이미 구현·검증되어 이 문서와 중복된다.
- **Phase 3 처리:** 플로팅 자동완성 오버레이(파일 경로 `Tab` 완성)와 IME 커서 동기화는 이번 아카이브 시점까지 구현되지 않았다. 이 두 항목은 `2026-07-21-tui-ux-improvement.md`의 범위에도 포함되지 않으며, 별도 요청이 있을 때 새 계획 문서로 다시 제안한다. 조용히 폐기하지 않고 여기 명시적으로 기록한다.
- **후속 조치:** `active/`에서 `archive/`로 이동. 활성 계획은 `.agentos/project/exec-plans/active/2026-07-21-tui-ux-improvement.md` 단일 문서로 일원화한다.
