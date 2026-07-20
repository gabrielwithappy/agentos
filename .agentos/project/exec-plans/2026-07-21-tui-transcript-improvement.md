# [TUI Transcript] 구현 계획

> **상태:** 리뷰 대기 (완료 후 '완료'로 변경)
> **작성일:** 2026-07-21<br>
> reviewed: true (리뷰 증거 파일 생성 완료)<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- 사용자 관점에서 **Pi TUI**와 동일한 수준의 대화 히스토리 및 스트리밍 경험 제공.
- Textual 기반의 `Transcript` 및 `ChatMessage` UI를 개선하여 스트리밍 중 렌더링 깜빡임(Flashing)과 스크롤 성능 저하 문제를 근본적으로 해결.

**사용자 결과 요약:** 
- 긴 LLM 응답을 스트리밍 받을 때, 터미널 UI가 부드럽게 글자를 출력하고 깜빡이지 않게 됩니다.
- 메시지의 말풍선 UI(둥근 테두리, 배경색 등)가 모던하게 개선되어, 이전보다 가독성과 사용성이 크게 향상됩니다.
- 스트리밍 중 스크롤 조작이 방해받지 않고 매끄럽게 이어집니다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. (기존 Textual 0.81.0, Rich 라이브러리 사용)

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py`

**진행 상태:** 리뷰 통과, 구현 진행 중

**아키텍처:** 
- `ChatMessage`: `Static`을 상속받아 구현된 현재 구조에서 스트리밍 성능을 개선하기 위해 `Markdown` 렌더링을 지연 처리하거나 부드럽게 업데이트하는 방식으로 수정.
- `Transcript`: LLM 스트리밍 중 수백 번의 강제 스크롤 및 레이아웃 재계산(throttle) 최적화.
- `AgentOSTui`: `run_stream` 로직 내의 `call_from_thread` 갱신 주기를 최적화.

**기술 스택:** 
- Python, Textual, Rich

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 진행 중 |
| 완료됨 | 계획 작성, 리뷰 통과 |
| 현재 위치 | 마일스톤 1 및 2 구현 진행 |
| 다음 단계 | 마일스톤 3 및 테스트 |
| 완료 신호 | Textual 스트리밍 렌더링 시 깜빡임 없이 부드러운 스크롤 시연 및 테스트 통과 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. ChatMessage UI 개선 | 말풍선(테두리, 여백) 디자인이 프리미엄급으로 개선됨. | `agentos/terminal/tui/widgets.py` | `Run:` `uv run agentos --provider mock`, `Expected:` TUI UI가 모던하게 렌더링됨 |
| 2. 스트리밍 깜빡임 제거 | 긴 문장 출력 시 깜빡임 없이 글자가 나타남 | `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py` | `Run:` `uv run agentos --provider mock` 후 긴 문자열 입력, `Expected:` 화면 흔들림 없음 |
| 3. 마크다운 변환 최적화 | 스트리밍 종료 시 부드럽게 마크다운으로 전환됨 | `agentos/terminal/tui/widgets.py` | `Run:` 스트리밍 종료 대기, `Expected:` 마크다운 최종 렌더링 1회 수행됨 |

## 리뷰 반영 이력
- Self-review fallback 수행 (plan-reviewer, principle-auditor, usability-reviewer)
- 리뷰 결과: PASS (`audit-plan-review.md`, `audit-principle.md`, `audit-usability.md` 생성됨)

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
