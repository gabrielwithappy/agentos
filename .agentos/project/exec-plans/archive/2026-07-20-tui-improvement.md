# AgentOS TUI 개선 1차 반복: 스트리밍 응답 및 기본 메뉴 구현

> **상태:** 완료
> **작성일:** 2026-07-20<br>
> reviewed: true (self-fallback 리뷰 완료)
> implementation_started_at: 2026-07-20T13:30Z
> implementation_completed_at: 2026-07-20T14:36Z
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- Pi TUI의 실시간 스트리밍 경험과 풍부한 메뉴 시스템을 AgentOS의 Textual 기반 TUI에 적용한다.
- LLM의 응답이 실시간으로(비동기적으로) 화면에 렌더링되도록 하여 사용자의 대기 시간을 줄인다.
- TUI 환경에서 사용할 수 있는 기본 메뉴(사이드바 또는 커맨드 팔레트 형태)를 도입하여 세션, 훅, 설정 등에 쉽게 접근할 수 있게 한다.

**사용자 결과 요약:** 
- 명령어 입력 후 LLM이 생성하는 텍스트가 즉각적으로 터미널에 타이핑되듯 나타납니다 (블로킹 프리징 해소).
- 단축키(예: `Ctrl+B` 또는 `F1`)를 통해 사이드바 메뉴를 열어 최근 세션을 선택하거나 사용 가능한 명령어를 조회할 수 있습니다.
- Pi TUI와 유사한 안정적이고 상호작용 가능한 프롬프트 입력을 경험할 수 있습니다.

**의존성 분석:**
- 외부 의존성: Python `textual` 프레임워크 내장 기능(`@work` 데코레이터, 백그라운드 스레드) 활용. 추가 설치 없음.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`

**진행 상태:** 구현 완료 및 fresh verification PASS

**아키텍처:** 
- `on_input_submitted` 내부에서 처리되던 `stream_once` 블로킹 로직을 `@work(thread=True)` 워커로 분리.
- Textual `call_from_thread`를 사용하여 메인 UI 스레드에서 `Transcript` 업데이트 수행.
- 메뉴 구성을 위해 Textual의 기본 기능(예: CommandPalette 연동 또는 별도 Sidebar 컴포넌트)을 추가.

**기술 스택:** 
- Python, Textual, AgentOS LLM Providers

---

## 오픈 퀘스천 (Open Questions)

> [!IMPORTANT]
> 1. **메뉴 UI 형태:** 메뉴를 Pi TUI의 SettingsList처럼 화면 중앙 오버레이로 띄울지, 아니면 화면 좌측에 고정되는 사이드바(Sidebar) 형태로 구현할지 사용자의 선호가 궁금합니다.
> 2. **메뉴 항목 구성:** 기본 메뉴에 '세션 관리', '명령어(Hook) 목록' 외에 당장 필요한 설정(Setting) 항목이 더 있을까요?

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 완료 및 fresh verification PASS |
| 완료됨 | 계획 초안 작성 |
| 현재 위치 | 완료 계획 archive 이관 |
| 다음 단계 | 심층 TUI UX 개선 계획에서 후속 반복 진행 |
| 완료 신호 | 비동기 스트리밍이 멈춤 없이 렌더링되고 기본 메뉴가 단축키로 토글 가능할 때 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. LLM 비동기 스트리밍 적용 | 입력 후 멈춤 없이 응답이 글자 단위로 화면에 출력됨 | `agentos/terminal/tui/app.py` | `Run:` `agentos run --tui` / `Expected:` 입력 시 응답이 점진적으로 노출됨 |
| 2. 기본 TUI 메뉴(사이드바) 추가 | `Ctrl+B`를 누르면 좌측 메뉴바가 나타나 세션 목록 등을 보여줌 | `agentos/terminal/tui/app.py`, `widgets.py` | `Run:` `agentos run --tui` / `Expected:` `Ctrl+B`로 메뉴 토글 동작 |
| 3. 입력창 사용성(Pi TUI 수준) 개선 | 멀티라인 지원 개선 및 자동완성(Autocomplete) UX 다듬기 | `widgets.py` (Composer 개선) | `Run:` `agentos run --tui` / `Expected:` 안정적인 다중줄 입력 동작 |

## 리뷰 반영 이력
- Self-fallback 리뷰 수행 (plan-reviewer, principle-auditor, usability-reviewer PASS)
- 리뷰 증거 경로: `.agents/traces/reviews/2026-07-20-tui-improvement/`
- 사용자 피드백: "1" (메뉴 UI 형태를 화면 중앙 오버레이 팝업으로 결정)

## 구현 결과
- `AgentOSTui.on_input_submitted` 내부에서 `stream_once`의 블로킹 호출을 `@work(thread=True)` 워커 스레드로 분리하여 비동기 점진적 렌더링(Streaming) 구현
- `MenuScreen(ModalScreen)` 클래스를 추가하고 `Ctrl+B` 단축키로 호출되는 중앙 화면 오버레이 방식의 팝업 메뉴(세션 이력, 명령어 등) 구현
- `Composer`를 `Input` 위젯에서 `TextArea` 위젯 기반으로 변경하여, 다중줄 입력 지원 (Shift+Enter: 개행, Enter: 입력 제출)

## 사용 방법
- `agentos run --tui` 실행 후 대화를 진행하면, 응답이 완성될 때까지 기다리지 않고 실시간으로 화면에 노출됩니다.
- 텍스트 입력 도중 줄바꿈이 필요할 경우 `Shift+Enter`를 사용합니다.
- TUI 화면 어디서나 `Ctrl+B`를 누르면 "AgentOS Menu" 팝업이 나타나며, 방향키와 `Enter`로 기능을 선택하거나 `Esc`로 닫을 수 있습니다.

## 아카이브 결정
- TUI 비동기 스트리밍, 메뉴 오버레이 및 다중줄 입력 컴포저 기능 구현 완료.
- `verify-public-test-suite.sh`를 통해 기존 테스트 스위트 회귀 없음(PASS) 확인.
- 다음 단계(기능 심화) 진행 시 본 문서를 archive로 이동.
