# AgentOS TUI — pi/hermes TUI 클론 (Phase 5: 설정 관리 UI `/settings`) 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-23<br>
> reviewed: false (리뷰 증거 파일 생성 전까지 절대 true로 변경 불가)<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 사용자가 TUI를 벗어나거나 별도 셸에서 `agentos hook enable/disable` CLI를 실행하지 않고도, TUI 안에서 `/settings`로 현재 훅(hook) 설정을 확인하고 켜고 끌 수 있게 한다 (pi TUI의 "설정 관리 UI" 패턴 이식, 인벤토리 문서 §1.6).

**사용자 결과 요약:**
- 최종 결과: TUI에서 `/settings`를 입력하면 현재 등록된 훅 목록(이름, 단계, 활성화 여부)이 화면에 표시되고, 방향키로 항목을 고른 뒤 `Enter`를 누르면 그 훅의 켜짐/꺼짐이 즉시 바뀌며 화면은 열린 채로 유지되어 여러 항목을 연달아 조정할 수 있다. `Esc`를 누르면 변경사항이 저장된 채로 화면이 닫히고 Composer로 돌아간다.
- 대상 독자: AgentOS TUI를 터미널에서 사용하는 개발자/운영자.
- 일상 사용의 변화: 입력 전처리 훅(공백 정리, 빈 입력 거부, 최대 길이 제한, 컨텍스트 파일 자동 첨부 등)을 세션 도중 TUI를 벗어나지 않고 즉시 켜고 끌 수 있다.
- 바뀌지 않는 경계: 훅의 `value`(예: `prepend_context_file`의 파일명), `order`, `timeout_ms`, `critical` 필드 편집은 이번 범위에 포함하지 않는다 — 활성화/비활성화 토글만 지원한다(아래 "이번 범위에 포함하지 않는 것" 참조). 세션 파일 포맷(JSONL), `sanitize()` secret redaction 경로, 기존 훅 스키마(`agentos.hooks/v1`)와 `agentos hook` CLI 동작은 변경하지 않는다 — TUI는 기존 백엔드 위에 화면만 추가한다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 훅 설정을 읽고 쓰는 백엔드(`agentos/terminal/hooks.py`의 `effective_hooks()`, `set_hook_enabled()`)와 `config.toml`(`agentos.hooks/v1` 스키마) 저장 로직은 이미 구현되어 있고 `tests/test_cli_hooks.py`와 `agentos hook list/enable/disable` CLI로 이미 검증된 상태다. 이번 계획은 TUI 화면(신규 `ModalScreen`)만 추가하고 새 패키지나 새 스키마를 도입하지 않는다.
- 검증 근거: `agentos/terminal/hooks.py:55` (`effective_hooks`), `agentos/terminal/hooks.py:92` (`set_hook_enabled`), `agentos/commands/hook.py`(기존 CLI `list`/`enable`/`disable` 커맨드가 동일 함수를 이미 호출), `tests/test_cli_hooks.py`(기존 백엔드 테스트) 직접 확인 완료.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거.
- Durable Result Surface: `agentos/terminal/tui/widgets.py`(신규 `SettingsScreen`), `agentos/terminal/tui/app.py`(`_open_settings_picker` 핸들러), `agentos/terminal/tui/commands.py`(`/settings` `SlashCommand` 등록), `docs/cli-reference.md`, `tests/test_tui_cli.py`. 인벤토리 문서(`2026-07-22-pi-hermes-tui-feature-inventory.md`) §1.6은 이번 Phase 5 완료로 갱신한다(계획 자체는 해당 문서를 수정하지 않고, 구현 완료 후 갱신).

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기 중 (아직 서브에이전트 리뷰를 요청하지 않음 — 이 세션의 목적은 계획 문서 작성까지)

**아키텍처:**
- 기존 `ThemeScreen`/`CommandPaletteScreen`(둘 다 `ModalScreen[str]`, `widgets.py`)과 동일한 모달 패턴을 재사용해 `SettingsScreen(ModalScreen[str])`을 추가한다. `compose()`에서 `agentos.terminal.hooks.effective_hooks()`를 호출해 각 `HookSpec`을 `OptionList` 항목으로 표시하고(예: `"[x] trim_whitespace  input  order=10"` / `"[ ] prepend_context_file  input  order=40"`), 상단 `Label`에 "Enter로 켜기/끄기, Esc로 닫기" 안내를 둔다.
- **중요한 설계 차이 — 반드시 구현 중 실측으로 재확인할 것**: `ThemeScreen`/`CommandPaletteScreen`은 항목 선택 시 `self.dismiss(value)`로 화면을 즉시 닫는다. `SettingsScreen`은 그와 달리 `Enter`를 눌러도 화면이 닫히지 않고 토글된 상태로 목록이 갱신되어야 한다(여러 훅을 연달아 조정하는 사용자 흐름을 지원하기 위함). `on_option_list_option_selected`에서 `self.dismiss()`를 호출하는 대신 `hooks.set_hook_enabled(name, not current_enabled)`를 호출한 뒤 `OptionList.clear_options()` + 새 라벨 재삽입(또는 `replace_option_prompt`가 이 Textual 버전에 존재하면 그것)으로 해당 행만 갱신한다. Phase 4에서 Gate 2 정적 분석이 실제 Textual 디스패치 순서를 놓쳐 구현 중 재설계가 필요했던 전례가 있으므로(`2026-07-22-tui-pi-clone-phase4.md` "구현 결과" 참조), 이 부분은 계획 승인 후 실제 구현 착수 시 `OptionList` API를 직접 확인하고 최소 재현 테스트로 먼저 검증한 뒤 본 구현을 진행한다.
- `Esc`는 기존 패턴과 동일하게 `self.dismiss("")`로 화면을 닫고 Composer로 포커스를 되돌린다(`app.py`의 `_open_theme_picker`처럼 콜백에서 `composer.focus()` 처리).
- `agentos/terminal/tui/commands.py`의 `COMMANDS`에 `/settings`(`handler_id="settings"`)를 등록하고, `agentos/terminal/tui/app.py`의 `process_input()`에 `_open_settings_picker()` 분기를 추가한다(`_open_theme_picker()`와 동일한 `push_screen(SettingsScreen(...), callback)` 구조).
- 기존 `/hooks` 커맨드(현재 고정 문자열 `"Hooks: only existing AgentOS-built hooks are shown."`을 출력)는 이번 계획에서 로직을 바꾸지 않는다. 다만 사용자가 실제 조정 방법을 찾을 수 있도록 그 안내 문구 자체는 마일스톤 4에서 "/settings로 켜고 끌 수 있습니다" 한 문장을 추가하는 최소 수정만 포함한다(신규 기능 추가 아님, 안내 문구 보강).

**기술 스택:**
- Python, Textual(`ModalScreen`, `OptionList`, `Label`, Pilot 테스트 하네스), pytest, 기존 `agentos.terminal.hooks` 모듈.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 계획 초안 작성 완료, Gate 2 리뷰 대기 |
| 완료됨 | 인벤토리 문서 재검토로 선행 조건 없는 유일한 미구현 후보(§1.6 설정 관리 UI) 식별, 기존 훅 백엔드(`hooks.py`) 확인, 계획 초안 작성 |
| 현재 위치 | 계획 문서 작성 완료. 서브에이전트 리뷰(plan-reviewer/principle-auditor/usability-reviewer) 요청 전 |
| 다음 단계 | Gate 2 서브에이전트 리뷰 → 통과 시 마일스톤 1부터 순서대로 구현 |
| 완료 신호 | 아래 마일스톤의 `Run:`/`Expected:` 검증이 모두 통과하고 `docs/cli-reference.md`에 `/settings`가 반영됨 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. `SettingsScreen` 모달 — 훅 목록 표시 | `/settings`를 입력하면 현재 등록된 모든 훅이 이름/단계/활성화 여부와 함께 목록으로 표시됨 | `agentos/terminal/tui/widgets.py`(`SettingsScreen`) | `Run:` `uv run pytest tests/test_tui_cli.py -k "settings_screen_lists" -q` / `Expected:` PASS — `SettingsScreen`을 직접 마운트하거나 `pilot`으로 `/settings` 입력 후, 화면에 `effective_hooks()`가 반환하는 모든 훅 이름이 나타남을 assert |
| 2. Enter로 토글, 화면 유지 | 목록에서 훅을 선택하고 `Enter`를 누르면 해당 훅의 켜짐/꺼짐이 즉시 바뀌고 화면이 닫히지 않아 다른 훅도 연달아 조정 가능 | `agentos/terminal/tui/widgets.py`(`SettingsScreen.on_option_list_option_selected`) | `Run:` `uv run pytest tests/test_tui_cli.py -k "settings_toggle" -q` / `Expected:` PASS — `pilot.press("enter")`로 특정 훅을 토글한 뒤 `hooks.effective_hooks()`로 실제 `config.toml`에 반영된 `enabled` 값이 바뀌었음을 assert, 그리고 같은 `pilot` 세션에서 `SettingsScreen`이 여전히 마운트된 상태임을 assert |
| 3. `/settings` 커맨드 등록 및 Esc로 닫기 | `/settings`가 커맨드 팔레트(`/help`, `Tab` 자동완성)에 나타나고, `Esc`를 누르면 화면이 닫히며 Composer로 포커스가 돌아감 | `agentos/terminal/tui/commands.py`(`COMMANDS`에 `/settings` 추가), `agentos/terminal/tui/app.py`(`process_input`의 `handler_id == "settings"` 분기, `_open_settings_picker`) | `Run:` `uv run pytest tests/test_tui_cli.py -k "settings_command or settings_escape" -q` / `Expected:` PASS — `/settings` 입력 시 `SettingsScreen`이 열리고, `pilot.press("escape")` 후 `pilot.app.focused`가 Composer임을 assert |
| 4. 안내 문구 동기화 | `docs/cli-reference.md`와 `/hooks` 안내 문구에 `/settings`로 훅을 켜고 끌 수 있다는 설명이 반영됨 | `docs/cli-reference.md`, `agentos/terminal/tui/app.py`(`/hooks` 핸들러의 고정 문자열 한 문장 보강) | `Run:` `grep -n "/settings" docs/cli-reference.md agentos/terminal/tui/app.py` / `Expected:` 두 파일 모두에서 `/settings` 관련 설명 줄이 출력됨 |
| 5. 전체 회귀 검증 | 기존 기능(테마, 분기, 클립보드, 스트리밍 등)이 깨지지 않음 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` 기존 통과 건수(117) 이상 PASS, 신규 실패 없음. `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` / `Expected:` PASS (secret redaction 회귀 없음) |

## 이번 범위에 포함하지 않는 것 (명시적 제외)

참조: `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md` §1.2, §1.3, §1.7, §2.3, §2.6, §2.4(잔여 항목)

- **훅 `value`/`order`/`timeout_ms`/`critical` 필드 편집** — pi의 설정 UI는 "토글, 범위 슬라이더"까지 지원하지만, 이번 Phase 5는 즉시 값이 있는 유일한 사용자 체감 조작(켜기/끄기)에 집중하고 나머지 필드 편집은 별도 조사(입력 검증, `HookError` 경계 재사용 방식)가 필요해 제외한다. 필요 시 후속 Phase에서 다룬다.
- **고도화된 Diff 렌더러(§1.2)** — 파일 수정 도구(write_file/apply_patch 등)가 AgentOS에 없어 활용처가 없다. 선행 시스템 필요.
- **이미지 프로토콜 지원(§1.3)** — 터미널 호환성(Kitty/Sixel) 조사가 선행되어야 하며 난이도가 높다(★★★★☆). 별도 조사 필요.
- **세션 압축 인디케이터(§1.7)** — AgentOS에 context 압축(compaction) 백엔드 로직이 없어 표시할 대상이 없다. 선행 시스템 필요.
- **서브에이전트 트리 시각화(§2.3)** — 멀티에이전트 오케스트레이션 지원이 먼저 필요. AgentOS는 현재 단일 에이전트 아키텍처.
- **다중 첨부 파일/이미지 업로드(§2.6)** — 멀티모달 LLM provider 지원이 먼저 필요.
- **음성 입력 토글키(§2.4 잔여)** — 별도 STT 서브시스템 도입이 선행되어야 함.
- **Grapheme 단위 커서 이동 전면 재작업(§2.4 잔여)** — Phase 4에서도 동일 사유로 제외됨: 범위가 크고 별도 조사가 필요해 이번 Phase에서도 제외한다.

## 리뷰 반영 이력
- 초안 작성 — 2026-07-23. 인벤토리 문서(§1~§2) 전체를 재검토해 Phase 1~4에서 이미 구현된 항목(분기 생성 UI, 모델 선택기, 인디케이터 스타일, 알림 배너, 클립보드 통합, 자동완성 퍼지 검색, 스트리밍 마크다운 점진적 렌더링)을 제외하고 남은 후보 중 "선행 조건 없음" 기준을 충족하는 항목이 설정 관리 UI(§1.6)뿐임을 확인함. §1.6은 인벤토리 문서 자체에 "설정 스키마 정의 필요"라는 하위 우선순위 사유가 적혀 있었으나, 실제로는 `agentos/terminal/hooks.py`에 `agentos.hooks/v1` 스키마와 `effective_hooks()`/`set_hook_enabled()`가 이미 구현·테스트되어 있어 그 전제가 더 이상 유효하지 않음을 코드 확인으로 검증함(선행 조건 해소됨).
- Gate 2 서브에이전트 리뷰(plan-reviewer, principle-auditor, usability-reviewer)는 아직 요청하지 않았다. 사용자 요청("계획문서를 작성하자")이 문서 작성까지였으므로, 리뷰·구현은 별도 세션/요청에서 진행한다.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정

2026-07-26, 사용자 요청에 따라 archive 처리. 사유: `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md`가 AgentOS 제품 방향을 "AgentOS control plane은 Work Contract/Context Compiler/lifecycle-evidence/Verification Runner/vendor adapter 상태를 소유하고, vendor execution plane(Codex/Claude/OpenCode)의 실제 대화·tool loop·기능을 복제하지 않는다"로 확정했다. 이 계획은 pi TUI의 설정 관리 UI 패턴을 그대로 이식하는 pi 클로닝 로드맵의 일부이며, `reviewed: false`로 아직 Gate 2 리뷰 전이었다. 0006 채택 이후 신규 vendor UX 이식 확장은 별도 reviewed implementation plan(0006을 근거로 삼는)에서 재검토되어야 하므로, 이 초안은 구현하지 않고 archive로 이동한다. 코드 변경은 없었다(계획 문서만 존재).
