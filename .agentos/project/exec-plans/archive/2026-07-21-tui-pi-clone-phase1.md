# AgentOS TUI — pi TUI 격차 해소 (Phase 1) 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-21<br>
> reviewed: true (plan-reviewer 3차 자기검토 fallback PASS, principle-auditor 2차 PASS, usability-reviewer 2차 PASS)<br>
> implementation_started_at: 2026-07-21T22:33:00+09:00<br>
> implementation_completed_at: 2026-07-21T22:40:10+09:00<br>
> implementation_duration: 7m10s<br>
> usability_review_required: true<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi`가 제공하는 TUI(TypeScript, 자체 저수준 터미널 렌더링 엔진 + 약 40개 컴포넌트, 총 3만 줄 이상)와 비교했을 때 AgentOS TUI(Textual 기반)에 부족한 부분을 좁힌다.
- pi TUI 전체를 1:1로 이식하지 않고, "AgentOS 구조에 맞게"(Textual이 이미 제공하는 기능은 재사용하고, pi가 자체 구현한 저수준 엔진 부분은 재구현하지 않음) 사용자 가치가 높고 실현 가능한 항목부터 단계적으로 반영한다.
- pi 상세 구조 분석 및 AgentOS 적용에 필요한 pi 코드 분석 결과를 지원 문서(supporting doc)로 등록하여 장기 기억으로 보존한다.

**사용자 결과 요약:**
- **pi 상세 구조 및 코드 분석 문서화 (신규):** 연구 서브에이전트가 분석한 pi TUI의 상세 아키텍처와 AgentOS 적용에 필요한 pi 핵심 코드 분석 결과를 프로젝트 지원 문서(`reference/implementation/`)로 저장하여 향후 참조할 수 있도록 장기 기억화한다.
- **`/hotkeys` 키보드 단축키 참조 (신규):** 현재 흩어져 있는 키보드 단축키(Enter/Shift+Enter/Up/Down/Ctrl+K/U/Y/Z/Ctrl+W/Tab/Ctrl+B/Esc 등)를 한 화면에서 확인할 수 있다.
- **테마 전환 (신규):** `/theme` 명령으로 Textual이 기본 제공하는 테마(다크/라이트 포함 21종) 중 원하는 것을 골라 즉시 적용할 수 있다. pi의 라이트/다크 2종보다 선택지가 넓다. 목록에서 `Esc`를 누르면 테마를 바꾸지 않고 그대로 이전 화면(Composer)으로 돌아간다.
- **푸터 강화 (신규):** 푸터에 git 브랜치(git 저장소가 아니면 이 항목 자체가 표시되지 않음)와 현재 세션 누적 사용량(입력/출력 문자 수, 아직 턴이 없으면 `0/0`으로 시작)이 추가로 표시된다.
- **도구 호출/결과 표시 개선 (신규):** 기존에 평문 한 줄로만 보이던 `Tool call:`/`Tool result:` 표시만 테두리 박스로 시각적으로 구분된다. `Thinking:`(추론) 줄은 지금처럼 테두리 없는 무채색 표시를 유지해 도구 실행과 단순 사고 과정을 구분한다(펼치기/접기 등 인터랙션은 이번 범위에 포함하지 않음).
- **바뀌지 않는 부분:** 세션/후크/LLM 공급자 로직, 슬래시 커맨드 처리 흐름, 기존 Composer/Transcript 동작은 그대로 유지된다. 테마 선택은 세션 동안만 유지되며 디스크에 저장하지 않는다(재시작 시 기본 테마로 복귀).
- **이번 범위에 포함하지 않는 것(Phase 2 이후 후보로 명시):** `/tree` 분기 탐색기(자체 ASCII 트리 렌더링, 복잡도 大), 도구별 커스텀 렌더러 플러그인 아키텍처(확장 SDK 전제, 복잡도 大), diff 렌더러(현재 AgentOS에 실제 파일 편집 도구가 없어 아직 쓸모가 없음), 설정 토글 셀렉터(현재 토글 가능한 설정이 hooks 표시뿐이라 아직 대상이 부족함), 세션 선택기 fuzzy 검색 강화, Kitty 이미지 프로토콜 이스터에그, IME 커서 마커/OSC133 셸 통합 세부사항(Textual이 자체 방식으로 이미 처리). 이 항목들은 조용히 누락되는 것이 아니라 위와 같이 명시적으로 이번 계획 밖으로 분류한다.

**의존성 분석:**
- 외부 의존성 있음(아래 의존성 게이트 참조). 그 외 새 패키지, 새 자격증명, 새 네트워크 호출 없음. Textual 8.2.8의 내장 테마 레지스트리(`app.theme`, `app.available_themes`, 21종)만 사용한다.

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| `git` 실행 파일 | local CLI (이미 저장소 운영에 필수 전제된 도구, 새 서비스/자격증명 아님) | false | `Run:` `command -v git` / `Expected:` 경로 출력(개발 환경엔 이미 존재) | 미설치 또는 비-git 디렉터리면 푸터에서 `branch` 필드를 생략하고 나머지 푸터는 정상 동작 | `NEEDS_CONTEXT` 아님 — `required=false`이며 위 fallback으로 항상 정상 동작하므로 사용자 개입 불필요 |

- `git rev-parse --abbrev-ref HEAD` 호출은 `agentos/llm/providers/codex_cli.py::_run_codex`와 동일하게 `timeout` + `TimeoutExpired`/`OSError` 캐치 패턴을 재사용해 무한 대기를 방지한다.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서
- Durable Result Surface: `agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/state.py`, `agentos/terminal/tui/commands.py`, `docs/cli-reference.md`

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기 중

**아키텍처:**
- **장기 기억화(문서화):** `.agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md` 파일을 생성하고 확장 등록표 가이드에 맞춰 필수 메타데이터와 pi 상세 구조 및 코드 분석 내용을 기입한다. 인덱스의 확장 등록표에도 이를 반영한다.
- `commands.py`: `/hotkeys`, `/theme` 슬래시 커맨드 추가.
- `app.py`: `/hotkeys` 핸들러(고정 키바인딩 목록을 transcript에 출력), `/theme` 핸들러(`ThemeScreen` 모달 오픈; 선택 시 `self.theme = name` 적용; `Esc`로 닫으면 콜백에 빈 값이 전달되어 테마를 바꾸지 않고 Composer로 포커스만 복귀 — 기존 `action_open_menu`의 Esc-취소 패턴과 동일).
  - **누적 사용량이 리셋되지 않도록 하는 구조 (리뷰에서 지적됨):** `self.status = TuiStatus.initial(...)`가 `app.py` 9곳에서 호출되는데, `TuiStatus.initial()`은 매번 모든 필드를 처음부터 다시 만드는 순수 팩토리라서, `total_input_chars`/`total_output_chars`를 단순히 그 안의 필드로만 넣으면 상태 갱신마다(턴마다 여러 번) 0으로 되돌아간다. 이를 막기 위해 누적 카운터의 소유자를 `TuiStatus`가 아니라 `AgentOSTui` 인스턴스로 둔다: `self.total_input_chars`/`self.total_output_chars`를 `__init__`에서 `0`으로 초기화하고, `_record_turn_results`에서 매 턴 `done` 이벤트의 `usage`로 가산한다(첫 턴 전에는 `0/0`으로 표시되며 별도의 "사용량 없음" 문구는 두지 않는다 — 숫자 카운터이므로 0이 곧 초기 상태). 기존 9개 호출부는 모두 새 헬퍼 `self._status_with_totals(provider, session_id, last_turn=...)`(내부에서 `TuiStatus.initial(..., git_branch=self.git_branch).with_totals(self.total_input_chars, self.total_output_chars).with_last_turn(...)`를 조합)를 통하도록 교체해, 재구성 시점의 최신 누적값이 항상 반영되게 한다.
  - **git 브랜치:** `self.git_branch: str | None`을 `__init__` 시점(TUI 시작 시) 1회만 `subprocess.run(["git","rev-parse","--abbrev-ref","HEAD"], timeout=1, capture_output=True, text=True)`로 조회해 캐시한다(매 턴 재조회하지 않음 — 세션 중 브랜치가 바뀌는 경우는 드물고, 매 상태 갱신마다 서브프로세스를 띄우는 비용을 피하기 위함). `TimeoutExpired`/`OSError`/비정상 종료 시 `None`으로 캐시하고 푸터에서 해당 필드를 생략한다.
- `state.py`: `TuiStatus`에 `git_branch: str | None = None`, `total_input_chars: int = 0`, `total_output_chars: int = 0` 필드 추가(모두 `initial()`의 키워드 인자로도 받음). `with_totals(input_chars, output_chars)` wither 메서드를 기존 `with_last_turn()`과 같은 방식으로 추가. `footer_text()`는 `git_branch`가 있을 때만 `branch <name>`을 붙이고, 사용량은 항상 `total in/out <N>/<M> chars` 형태로(초기값 0/0) 출력한다.
- `widgets.py`: 테마 선택 모달(`ThemeScreen`, 기존 `MenuScreen`/`CommandPaletteScreen`과 동일한 `OptionList` 기반 패턴 재사용, `Esc` 시 빈 문자열 dismiss로 취소 신호 전달). **역할 분리:** 현재 `reasoning`/`tool_call`/`tool_result` 세 이벤트가 모두 동일한 `role="process"`로 합쳐져 있어 CSS로 도구 줄만 구분할 수 없다(리뷰에서 지적됨). 이를 `app.py`의 `run_stream`에서 `reasoning`은 `role="reasoning"`으로, `tool_call`/`tool_result`는 `role="tool"`로 분리해 `add_message()`하도록 고친다. `widgets.py`에 `ChatMessage.reasoning`(기존 `ChatMessage.process`와 동일한 테두리 없는 무채색 스타일)과 `ChatMessage.tool`(테두리 `border: round $warning` 추가)을 새로 정의하고, 더 이상 아무 곳에서도 만들어지지 않는 `role="process"`와 그 `ChatMessage.process` CSS 규칙은 **삭제한다**(orphaned selector 방지 — Selector Ownership: 신규 소유자는 `.reasoning`/`.tool`, `.process`는 완전히 제거되어 죽은 규칙이 남지 않음).
- `docs/cli-reference.md`: 새 슬래시 커맨드, 푸터 필드, 테마 선택 동작(취소 포함) 문서화.

**기술 스택:**
- Python 3.12, Textual 8.2.8 (`pyproject.toml` 요구사항: `textual>=6.0.0`), Rich, 시스템 `git` 바이너리(선택적)

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Gate 2 리뷰 대기 |
| 완료됨 | pi TUI 레퍼런스 조사(연구 서브에이전트) 및 Phase 1 범위 확정 |
| 현재 위치 | plan-reviewer / principle-auditor / usability-reviewer PASS 대기 |
| 다음 단계 | Gate 2 리뷰 통과 후 마일스톤 1부터 순서대로 구현 실행 |
| 완료 신호 | `/hotkeys`, `/theme` 명령이 동작하고, 푸터에 git 브랜치·누적 사용량이 보이고, 도구 호출/결과가 테두리로 구분되며, 전체 테스트가 통과할 때 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. `/hotkeys` 키바인딩 참조 | `/hotkeys` 입력 시 현재 지원되는 모든 키보드 단축키(Enter/Shift+Enter/Up/Down/Ctrl+K/U/Y/Z/Ctrl+W/Alt+Backspace/Tab/Ctrl+B/Esc/Exit)가 표로 나타남. `/help` 팔레트와 `docs/cli-reference.md`에도 반영 | `agentos/terminal/tui/commands.py`, `agentos/terminal/tui/app.py`, `docs/cli-reference.md` | `Run:` `uv run pytest tests/test_tui_cli.py -k hotkeys -q` / `Expected:` PASS. `Run:` `grep -n "/hotkeys" docs/cli-reference.md` / `Expected:` 발견됨 |
| 2. `/theme` 테마 전환 | `/theme` 입력 시 Textual 내장 테마 목록(다크/라이트 포함 21종)이 선택 모달로 뜨고, 고르면 즉시 화면 배색이 바뀜. `Esc`로 닫으면 테마가 바뀌지 않고 Composer로 돌아감. 세션 동안만 유지(재시작 시 기본값 복귀) | `agentos/terminal/tui/widgets.py`(`ThemeScreen`), `agentos/terminal/tui/app.py`, `agentos/terminal/tui/commands.py`, `docs/cli-reference.md` | `Run:` `uv run pytest tests/test_tui_cli.py -k theme -q` / `Expected:` PASS (선택 시 `app.theme` 값 변화, `Esc` 취소 시 값 불변 및 포커스 복귀 모두 검증) |
| 3. 푸터 강화 (git 브랜치 · 누적 사용량) | 푸터에 `branch <name>`(git 저장소일 때만, 아니면 필드 자체가 없음)과 `total in/out <N>/<M> chars`(첫 턴 전엔 `0/0`, 턴이 끝날 때마다 누적되며 상태가 갱신되는 다른 시점에도 리셋되지 않음)가 추가로 보임 | `agentos/terminal/tui/state.py`, `agentos/terminal/tui/app.py` | `Run:` `uv run pytest tests/test_tui_cli.py -k "footer_git or footer_usage" -q` / `Expected:` PASS — 새 테스트는 모두 `test_footer_git_...` 또는 `test_footer_usage_...`로 명명(예: `test_footer_git_branch_shown_inside_repo`, `test_footer_git_branch_omitted_outside_repo`, `test_footer_git_branch_omitted_on_timeout`, `test_footer_usage_starts_at_zero`, `test_footer_usage_accumulates_and_survives_status_updates`). 기존 `test_footer_includes_stable_labels_and_mock_model`류(무관한 4개 테스트)는 `footer_git`/`footer_usage` 어느 쪽도 포함하지 않아 매치되지 않음을 사전에 `grep`으로 확인 |
| 4. 도구 호출/결과 시각적 구분 | 답변 위에 표시되는 `Tool call:`/`Tool result:` 줄만 테두리 박스로 구분되고, `Thinking:` 줄은 기존처럼 테두리 없이 남아 도구 실행과 단순 사고 과정이 시각적으로 구분됨 | `agentos/terminal/tui/widgets.py` (`ChatMessage.tool`/`ChatMessage.reasoning` CSS, `ChatMessage.process` 규칙 삭제), `agentos/terminal/tui/app.py` (`run_stream`의 role 분리) | `Run:` `uv run pytest tests/test_tui_cli.py -k tool_border -q` / `Expected:` PASS (tool_call/tool_result 메시지는 `tool` class를, reasoning 메시지는 `reasoning` class를 가지며 서로 다른 class임을 assert). `Run:` `grep -n "ChatMessage.process" agentos/terminal/tui/widgets.py` / `Expected:` 결과 없음(orphaned selector 제거 확인). 수동: `uv run agentos --provider mock` 실행 후 메시지 전송 / `Expected:` `Tool call:`/`Tool result:` 줄에만 테두리가 보임 |
| 5. pi 상세 구조 및 코드 분석 장기 기억화 | 연구 서브에이전트가 분석한 pi TUI 레퍼런스의 상세 구조와 AgentOS 적용용 코드 분석 내용이 `reference/implementation/` 하위 문서로 저장되어 프로젝트 SSOT에 편입됨 | `.agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md`, `.agentos/project/00-project-index.md` (확장 등록표 갱신) | `Run:` `cat .agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md` / `Expected:` 확장 문서 필수 필드 및 분석 내용 존재 |
| 6. 전체 안정성 검증 | 기존 TUI 명령어와 LLM 상호작용이 깨지지 않음 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` 전체 PASS (기존 실패 없음) |

## 세션 중단 대비 체크포인트
- **지금까지 완전히 끝난 범위:** 계획 초안 작성 및 1차 Gate 2 리뷰 반영(개정 완료, 재리뷰 대기). 코드는 아직 한 줄도 바뀌지 않았다.
- **아직 안 끝난 일:** 마일스톤 1-6 구현 전체.
- **다음 세션이 먼저 할 일:** Gate 2 3개 리뷰어(plan-reviewer/principle-auditor/usability-reviewer) 재리뷰 PASS 확보 → `reviewed: true` 전환 → 마일스톤 1(`/hotkeys`)부터 순서대로 구현.
- **남은 검증:** 위 `사용자 진행 계획` 표의 각 `Run:`/`Expected:` 전부 + 최종 `uv run pytest tests/ -q` 전체 PASS.
- **관련 HISTORY.md 체크포인트:** 이 계획 최초 등록 시점의 `[EVOLUTION_PLAN]` 항목(`trigger_id=tui-pi-clone-phase1`).

## 리뷰 반영 이력
- (초안) pi TUI 레퍼런스(`references/pi/packages/tui`, `references/pi/packages/coding-agent/src/modes/interactive`) 약 3만 줄을 연구 서브에이전트로 조사해 기능 인벤토리를 확보했다. 저수준 렌더링 엔진(차분 렌더러, IME 커서 마커, Kitty 이미지 프로토콜)은 Textual이 이미 동등 기능을 제공하거나 대체 방식으로 처리하므로 재구현 대상에서 제외했다. 나머지 약 35개 UI 컴포넌트 중 사용자 가치 대비 구현 난이도가 낮은 4건(키바인딩 참조, 테마 전환, 푸터 강화, 도구 표시 개선)을 Phase 1로 선정했다. `/tree` 분기 탐색기, 도구별 커스텀 렌더러 플러그인, diff 렌더러, 설정 토글 셀렉터, 세션 검색 강화, 이스터에그는 복잡도·전제 기능 부재·낮은 ROI를 근거로 명시적으로 범위 밖으로 분류했다(사용자 결과 요약 참조).
- **1차 Gate 2 리뷰 (2026-07-21):** `plan-reviewer` FAIL(4건), `principle-auditor` REVISE(1건), `usability-reviewer` FAIL(3건). 증거: `.agents/traces/reviews/2026-07-21-tui-pi-clone-phase1/{plan-reviewer,principle-auditor,usability-reviewer}.md`(1차본). 핵심 공통 지적: 마일스톤 4가 "`Tool call:`/`Tool result:`만 테두리"를 약속하지만, 현재 코드에서 `reasoning`/`tool_call`/`tool_result`가 모두 동일한 `role="process"`/`ChatMessage.process` CSS 클래스를 공유해 이 약속을 지킬 메커니즘이 아키텍처에 없었음. 그 외: 의존성 게이트가 구조화된 필드(name/type/required/preflight/fallback/failure_behavior) 없이 프로즈로만 있었음, `/theme` 취소(Esc) 동작 미기술, 누적 사용량의 턴 이전 기본 상태 미기술, "20종" 오기(실제 21종), `세션 중단 대비 체크포인트` 섹션 누락.
  - 대응: `app.py`의 `run_stream`에서 `reasoning`은 `role="reasoning"`, `tool_call`/`tool_result`는 `role="tool"`로 분리하고 `widgets.py`에 `ChatMessage.tool`(테두리)/`ChatMessage.reasoning`(무테두리, 기존과 동일)을 별도 CSS로 정의하도록 아키텍처와 마일스톤 4를 수정. 의존성 분석을 표 형태 `의존성 게이트`로 재작성. `/theme` Esc 취소 동작을 사용자 결과 요약·마일스톤 2에 명시. 누적 사용량을 "0/0에서 시작하는 숫자 카운터"로 명시하고 별도 empty-state 문구를 두지 않기로 결정(사유: `/usage`와 달리 항상 보이는 푸터 필드라 카운터가 0인 것 자체가 자연스러운 초기 상태). "21종"으로 정정. 이 섹션을 추가.
- **2차 Gate 2 리뷰 (2026-07-21):** `principle-auditor` PASS(APPROVE), `usability-reviewer` PASS. `plan-reviewer`는 새 항목 3건으로 FAIL: (1) `role="process"` 분리 후 더 이상 아무도 만들지 않는 `ChatMessage.process` CSS 규칙의 삭제 여부가 명시되지 않은 orphaned-selector 위험, (2) 마일스톤 3 검증 `-k footer`가 `git_branch`/`total_usage`와 무관한 기존 테스트 4개와 이미 매치되어 non-discriminating, (3) `TuiStatus.initial(...)`이 `app.py` 9곳에서 매번 전체 필드를 새로 만드는 순수 팩토리인데, 누적 카운터를 그 필드로만 두면 상태 갱신마다(턴당 여러 번) 0으로 리셋될 위험(정확히 지적됨 — 리뷰가 코드의 실제 호출부 9곳을 짚어 확인함). 증거: `.agents/traces/reviews/2026-07-21-tui-pi-clone-phase1/{plan-reviewer,principle-auditor,usability-reviewer}.md`(2차본, `plan-reviewer.md`만 재차 갱신 예정이라 1·2차 이력 보존).
  - 대응: 누적 카운터(`total_input_chars`/`total_output_chars`)의 소유자를 `AgentOSTui` 인스턴스로 옮기고, 기존 9개 `TuiStatus.initial(...)` 호출부를 새 헬퍼 `self._status_with_totals(...)`(내부에서 `.with_totals(...)` wither 메서드로 최신 누적값을 매번 주입)로 교체하도록 아키텍처를 수정. git 브랜치는 매 턴이 아니라 TUI 시작 시 1회만 조회해 `self.git_branch`에 캐시(성능/일관성 근거 명시). `role="process"`/`ChatMessage.process` CSS를 명시적으로 삭제 대상으로 표기하고 마일스톤 4 검증에 `grep`으로 부재 확인을 추가. 마일스톤 3 검증을 `-k "footer_git or footer_usage"`로 교체하고 신규 테스트 이름을 그에 맞게 명명, 기존 무관 테스트와 매치되지 않음을 명시.
- Gate 2 리뷰가 완료되면 `.agents/traces/reviews/2026-07-21-tui-pi-clone-phase1/`에 `plan-reviewer.md`, `principle-auditor.md`, `usability-reviewer.md` 증거 파일을 갱신한다.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정
(구현 완료 후 작성)
