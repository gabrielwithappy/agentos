# AgentOS pi 스타일 부트스트랩 컨텍스트 주입 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-24<br>
> reviewed: true (plan-reviewer PASS, principle-auditor PASS, usability-reviewer PASS — 증거: `.agents/traces/reviews/2026-07-24-agentos-pi-bootstrap-context/{plan-reviewer,principle-auditor,usability-reviewer}.json`)<br>
> implementation_started_at: 2026-07-24T00:00:00Z<br>
> implementation_completed_at: 2026-07-24T00:00:00Z<br>
> implementation_duration: (같은 세션 내 연속 구현)<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 사용자가 새 AgentOS 세션을 시작하면, 프로젝트 루트(및 조상 디렉토리)의 `AGENTS.md`/`CLAUDE.md`와 설치된 스킬 메타데이터가 pi와 동일한 방식으로 세션 첫 system 메시지에 자동 주입되어, 매 턴 사용자가 직접 붙여넣지 않아도 LLM이 프로젝트 지침과 사용 가능한 스킬을 인지한 상태로 응답하게 한다.

**사용자 결과 요약:**
- 최종 결과: `agentos` interactive session이나 TUI를 새로 열면, 세션의 첫 신뢰된 system 메시지에 발견된 `AGENTS.md`/`CLAUDE.md` 원문과 설치된 스킬의 name/description/location 목록이 포함된다. 세션 시작 시 콘솔에 "부트스트랩 컨텍스트: N개 파일, M개 스킬 로드됨(`/status`로 목록 확인)" 배너가 출력되고, 확장된 `/status` 명령으로 실제 로드된 파일 경로와 스킬 이름을 확인할 수 있다. 원치 않으면 `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1` 환경변수로 세션별로 끌 수 있다.
- 대상 독자: AgentOS CLI/TUI로 반복 세션을 여는 개발자 및 프로젝트 유지관리자.
- 일상 사용의 변화: 프로젝트 루트에 `AGENTS.md`/`CLAUDE.md`를 두면 별도 조작 없이 모든 새 세션에 자동 반영된다. 스킬을 설치(`agentos skill install`)하면 다음 세션부터 자동으로 목록이 노출된다. 조상 디렉토리(공유 모노레포 루트, 홈 디렉토리 등)에 있는 `AGENTS.md`/`CLAUDE.md`까지 함께 로드될 수 있다는 점을 `docs/cli-reference.md`에서 명시적으로 경고한다.
- 바뀌지 않는 경계: 기존 `ConversationState`/`ConversationRuntime`/`build_context()`의 트리밍·연속성(continuation) 로직은 변경하지 않는다. 스킬 본문 전체는 시스템 프롬프트에 넣지 않고 pi와 동일하게 name/description/location 메타데이터만 노출한다(lazy-loading — 필요 시 LLM이 별도로 읽음, 이번 범위에는 "읽기" 액션 자체가 없으므로 실제로는 안내 텍스트로만 존재). `redact_text()` secret redaction 경로와 `TRUSTED_SYSTEM_SOURCE` 신뢰 경계는 그대로 유지한다. 기존 세션 JSONL/스냅샷 포맷과 `agentos.conversation/v1` 스키마는 변경하지 않는다. 읽기 실패한 컨텍스트 파일(권한 오류, 인코딩 오류, 깨진 심볼릭 링크)은 세션 시작을 막지 않고 조용히 건너뛰되, 시작 배너에 건너뛴 경로 수를 표시한다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 파일시스템 읽기(`AGENTS.md`/`CLAUDE.md`/`SKILL.md`)만 필요하며 네트워크 호출이 없다.
- 검증 근거: `agentos/conversation/types.py:12`(`TRUSTED_SYSTEM_SOURCE`, 현재 populate하는 코드 없음 — 직접 확인 완료), `agentos/conversation/persistence.py:38`(`empty_state()` — 신규 세션 생성 지점, system 메시지 없이 시작), `agentos/terminal/sessions.py:184`(`resume_conversation_state()` — 세션 재개 진입점), `agentos/commands/skill.py:10`(`get_skills_dir()` — `AGENTOS_HOME/core/.agents/skills`가 기존 스킬 설치 위치), `agentos/terminal/paths.py:16`(`agentos_home()` — `AGENTOS_HOME` 환경변수 및 대칭링크 방지 검증 패턴), `agentos/llm/redaction.py:24`(`redact_text()` — 기존 secret redaction 유틸, 신규 로더도 재사용).
- **주의: pi 레퍼런스 저장소는 이 `agentos` 저장소 하위가 아니라 워크스페이스 루트에 별도 clone으로 존재한다.** 정확한 절대 경로: `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi`(이 `agentos` 저장소와 형제 디렉토리, git submodule 아님, 이 계획의 의존성으로 추가하지 않음 — read-only 참고 자료). 리뷰어/구현자는 이 절대 경로로 직접 열어 재확인해야 한다: `references/pi/packages/coding-agent/src/core/resource-loader.ts:67-120`(`loadContextFileFromDir`/`loadProjectContextFiles` — 조상 디렉토리 순회 + 디렉토리당 첫 매치 우선 패턴, 전역 `agentDir` 우선 후 조상→cwd 순서로 배열에 push), `references/pi/packages/coding-agent/src/core/system-prompt.ts:28-162`(`buildSystemPrompt` — `<project_context><project_instructions path="...">...</project_instructions></project_context>` 및 `<available_skills>` XML 조립 방식, customPrompt 유무에 따라 두 분기 모두 동일한 project_context/skills append 로직 사용), `references/pi/packages/coding-agent/src/core/skills.ts:335-360`(`formatSkillsForPrompt` — `<skill><name>/<description>/<location></skill>` 메타데이터만 노출, 본문 미포함).

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거. hermes-agent 구조 비교 조사(`@`-include 미지원 재확인, prompt injection 스캔, 동적 truncation 캐핑 설계 참고)는 `.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md`에 영속화(후속 계획에서 재참조 예정).
- Durable Result Surface: 신규 `agentos/conversation/bootstrap.py`(컨텍스트 파일 탐색 + 시스템 메시지 조립), `agentos/conversation/persistence.py`(`empty_state()` 호출부에 부트스트랩 연결), `agentos/terminal/sessions.py`(`resume_conversation_state()` 신규 세션 경로), `agentos/terminal/interaction.py`(`/status` 확장 및 시작 배너 출력), `agentos/terminal/tui/app.py`(`/status`의 `_bootstrap_status_text()` — TUI가 실제 기본 진입점이라 실사용 중 발견되어 추가), `agentos/commands/skill.py`(스킬 메타데이터 파싱 재사용을 위한 최소 리팩터, 필요 시), `docs/cli-reference.md`, `tests/test_conversation_bootstrap.py`(신규), `tests/test_conversation_persistence.py`/`tests/test_conversation_runtime.py`/`tests/test_cli.py`/`tests/test_tui_cli.py`(회귀 확인).

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기 중 (핵심 하네스 서브에이전트만 최소 리뷰 — 사용자 지시에 따름)

**아키텍처:**
- pi의 `resource-loader.ts`(파일 탐색) + `system-prompt.ts`(조립) 2계층 구조를 AgentOS에 이식하되, AgentOS의 provider-agnostic 메시지 모델(`ConversationMessage`)에 맞춰 "시스템 프롬프트 문자열"이 아니라 "신뢰된 system 메시지 1건"으로 표현한다.
- 신규 `agentos/conversation/bootstrap.py`:
  - `discover_context_files(cwd, agent_home) -> list[ContextFile]`(`ContextFile`은 `path`/`content`/`skipped: bool`/`skip_reason: str | None`을 담는 작은 dataclass): pi의 `loadProjectContextFiles`와 동일하게, `agent_home`(전역, 예: `AGENTOS_HOME/core`)에서 먼저 하나, 그 다음 `cwd`부터 파일시스템 루트까지 조상 디렉토리를 순회하며 각 디렉토리당 `AGENTS.md`(대소문자 변형 포함) → 없으면 `CLAUDE.md`를 찾아 **디렉토리당 첫 매치만** 채택한다. 순서는 전역 → 최상위 조상 → cwd(가장 가까운 지침이 프롬프트에서 나중에/더 강조되도록 pi와 동일 순서 유지). **읽기 실패 처리**: 발견된 파일이 권한 오류/인코딩 오류/깨진 심볼릭 링크로 읽기 실패하면 세션 시작을 막지 않고 조용히 건너뛰며(`skipped=True`, `skip_reason`에 원인 기록), 그 파일은 시스템 메시지에 포함되지 않는다. 건너뛴 개수는 반환값을 통해 상위(배너 출력 지점)로 전달된다.
  - `discover_skills(skills_dir) -> list[SkillMeta]`: `agentos/commands/skill.py:get_skills_dir()`가 가리키는 디렉토리를 스캔해 각 하위 디렉토리의 `SKILL.md` 프론트매터(name/description, 없으면 디렉토리명/첫 줄 fallback)만 파싱한다. 본문 전체는 읽지 않는다. 동일하게 읽기 실패 시 조용히 건너뛴다.
  - `build_bootstrap_message(context_files, skills) -> ConversationMessage | None`: 발견된 것이 하나도 없으면(또는 전부 건너뛰었으면) `None`(신규 세션에 불필요한 빈 system 메시지를 만들지 않음). 있으면 pi의 `<project_context><project_instructions path="...">...</project_instructions></project_context>` 및 `<available_skills><skill><name>/<description>/<location></skill></available_skills>` 포맷을 그대로 재사용해 하나의 텍스트로 합치고, 각 파일 content는 `redact_text()`로 새니타이즈한 뒤 `role="system"`, `source=TRUSTED_SYSTEM_SOURCE`인 `ConversationMessage`로 반환한다.
  - **Opt-out**: 환경변수 `AGENTOS_SKIP_CONTEXT_BOOTSTRAP`이 truthy(예: `"1"`)이면 `discover_context_files`/`discover_skills`를 아예 호출하지 않고 부트스트랩 전체를 생략한다(파일이 커서 매 세션 토큰 비용이 부담스럽거나, 조상 디렉토리의 민감한 `AGENTS.md`를 세션에 영구히 남기고 싶지 않은 사용자를 위한 탈출구). 이 체크는 `bootstrap.py`의 최상위 진입 함수(예: `build_bootstrap_message_for_session(cwd, agent_home, skills_dir)`)에서 수행해 호출부(`sessions.py`)가 환경변수를 직접 알 필요가 없게 한다.
- `agentos/conversation/persistence.py`의 `empty_state()`가 호출되는 두 지점(`resume_conversation_state()`의 "세션을 한 번도 persist한 적 없음" 분기, `runtime/bench.py`의 벤치마크 초기화)에서, 부트스트랩 메시지가 있으면 그 브랜치의 root 메시지로 미리 append한다(`ConversationRuntime.submit_turn()`이 트리밍 시 `is_trusted_system()`으로 항상 우선 보존하는 기존 로직을 그대로 활용 — `build_context()` 변경 불필요, `agentos/conversation/context.py:54-55` 기존 분리 로직이 이미 이 케이스를 위해 존재함이 확인됨).
- 세션 **재개**(기존 이벤트/스냅샷이 있는 경우)에는 부트스트랩을 재주입하지 않는다 — 최초 생성 시점에 이미 커밋된 system 메시지가 브랜치 히스토리에 영구 보존되어 있으므로 중복 주입을 피한다. 프로젝트 파일이 세션 도중 바뀌는 경우는 이번 범위에 포함하지 않는다(pi도 세션 도중 재로딩은 별도 refresh 트리거로 분리되어 있음).
- **가시성**: `agentos/terminal/interaction.py`의 신규 세션 생성 직후, 부트스트랩 메시지가 실제로 커밋됐으면 `console.print(f"부트스트랩 컨텍스트: {파일수}개 파일, {스킬수}개 스킬 로드됨(건너뜀 {건너뜬수}개) — /status로 확인")` 형태의 1줄 배너를 출력한다(기존 `/hooks`/`/session` 안내 출력 패턴과 동일한 위치·스타일). 기존 `/status` 핸들러(`agentos/terminal/interaction.py:70-72`, 현재 `provider=... session=...`만 출력)를 확장해, 부트스트랩 메시지가 존재하면 로드된 컨텍스트 파일의 경로 목록과 스킬 이름 목록을 추가로 출력한다.
- `docs/cli-reference.md`에 다음을 명시적으로 추가한다: (1) `AGENTS.md`/`CLAUDE.md`가 **cwd부터 파일시스템 루트까지 조상 디렉토리를 순회하며** 자동 로드된다는 점과 그로 인한 위험(공유 모노레포 루트, 홈 디렉토리 등 예상 밖의 상위 디렉토리 파일이 포함될 수 있음), (2) `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1`로 끄는 방법, (3) `/status`로 실제 로드된 파일을 확인하는 방법.

**기술 스택:**
- Python 3.12+, 기존 `agentos.conversation`/`agentos.llm.redaction`/`agentos.terminal.paths` 모듈, pytest. 신규 외부 패키지 없음.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Gate 2 리뷰(plan-reviewer/principle-auditor/usability-reviewer 모두 PASS) 및 8개 마일스톤 구현·검증 완료 |
| 완료됨 | `agentos/conversation/bootstrap.py` 신규 구현, `persistence.py`/`sessions.py`/`interaction.py` 연결, `docs/cli-reference.md` 갱신, 전체 테스트 스위트 313 passed |
| 현재 위치 | 구현 및 검증 완료 |
| 다음 단계 | 사용자가 요청하면 커밋/PR 생성, 또는 archive로 이동 |
| 완료 신호 | 아래 8개 마일스톤의 `Run:`/`Expected:` 검증이 모두 PASS(달성), `docs/cli-reference.md`에 조상 디렉토리 순회 경고·opt-out·`/status` 확인법이 모두 반영됨(달성) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 컨텍스트 파일 탐색 | `AGENTS.md`/`CLAUDE.md`가 cwd부터 조상 디렉토리까지 탐색되어 발견됨(디렉토리당 첫 매치, 전역 홈 경로 포함) | `agentos/conversation/bootstrap.py`(`discover_context_files`) | `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "discover_context_files" -q` / `Expected:` PASS — 임시 디렉토리 트리에서 cwd/중간조상/루트 각각에 다른 내용의 `AGENTS.md`를 두고 모두 발견됨을 assert, 같은 디렉토리에 `AGENTS.md`와 `CLAUDE.md`가 둘 다 있으면 `AGENTS.md`만 채택됨을 assert |
| 2. 스킬 메타데이터 탐색 | 설치된 스킬(`AGENTOS_HOME/core/.agents/skills/*/SKILL.md`)의 name/description만 파싱되고 본문은 로드되지 않음 | `agentos/conversation/bootstrap.py`(`discover_skills`) | `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "discover_skills" -q` / `Expected:` PASS — 가짜 스킬 디렉토리 2개(정상 프론트매터, 프론트매터 없음 fallback)를 만들어 각각 올바른 메타데이터가 나오는지 assert |
| 3. 신뢰된 system 메시지 조립 | 발견된 컨텍스트 파일/스킬이 pi와 동일한 `<project_context>`/`<available_skills>` XML로 하나의 system 메시지에 합쳐지고, 아무것도 없으면 메시지가 생성되지 않음 | `agentos/conversation/bootstrap.py`(`build_bootstrap_message`) | `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "build_bootstrap_message" -q` / `Expected:` PASS — 빈 입력 시 `None` 반환, 비어있지 않을 때 `role=="system"`이고 `is_trusted_system()`이 `True`임을 assert. `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest tests/test_conversation_bootstrap.py -k redact -q` / `Expected:` PASS — 컨텍스트 파일 내용에 시크릿이 있으면 조립된 system 메시지에서 redact됨을 assert |
| 4. 신규 세션에 자동 연결 | 새 AgentOS 세션(`agentos run`/TUI)을 열면 부트스트랩 system 메시지가 브랜치의 첫 메시지로 이미 커밋되어 있고, 세션을 재개하면 중복 주입되지 않음 | `agentos/terminal/sessions.py`(`resume_conversation_state`의 "신규 세션" 분기) | `Run:` `uv run pytest tests/test_conversation_persistence.py tests/test_conversation_runtime.py -q` / `Expected:` 기존 통과 건수 이상 PASS, 신규 실패 없음. `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "resume_injects_once" -q` / `Expected:` PASS — 신규 세션은 system 메시지 포함, 같은 session_id로 재개 시 system 메시지가 중복되지 않고 정확히 1개임을 assert |
| 5. 가시성 배너와 `/status` 확장 | 새 세션 시작 시 "부트스트랩 컨텍스트: N개 파일, M개 스킬 로드됨(건너뜀 K개) — /status로 확인" 배너가 출력되고, `/status` 입력 시 실제 로드된 파일 경로와 스킬 이름이 나열됨 | `agentos/terminal/interaction.py`(`run_interactive`의 세션 생성 직후, `/status` 핸들러 확장) | `Run:` `uv run pytest tests/test_cli.py -k "bootstrap_banner or status_shows_context" -q` / `Expected:` PASS — pty/CLI 드라이버로 세션을 시작해 배너 텍스트가 출력됨을 assert, `/status` 입력 후 출력에 로드된 컨텍스트 파일 경로와 스킬 이름이 포함됨을 assert |
| 6. 읽기 실패 내성과 opt-out | 읽기 실패한 컨텍스트 파일이 있어도 세션이 정상 시작되고 건너뛴 개수가 배너에 표시됨. `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1`이면 부트스트랩 메시지 자체가 생성되지 않음 | `agentos/conversation/bootstrap.py`(읽기 실패 처리, opt-out 체크) | `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "skip_unreadable or opt_out" -q` / `Expected:` PASS — 읽기 권한이 없는 파일을 만들어 세션 시작이 실패하지 않고 해당 파일만 제외됨을 assert, `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1` 환경에서 `build_bootstrap_message_for_session(...)`이 `None`을 반환함을 assert |
| 7. 사용자 가시성 문서화 | `docs/cli-reference.md`에 (a) cwd부터 파일시스템 루트까지 조상 디렉토리를 순회해 자동 로드된다는 점과 그 위험, (b) `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1` 끄는 법, (c) `/status`로 확인하는 법이 설명됨 | `docs/cli-reference.md` | `Run:` `grep -n "AGENTOS_SKIP_CONTEXT_BOOTSTRAP\|상위 디렉토리\|filesystem root\|조상 디렉토리" docs/cli-reference.md` / `Expected:` 세 항목 모두에 대응하는 설명 줄이 각각 출력됨(단순히 "AGENTS.md" 문자열 존재가 아니라 opt-out 변수명과 조상 디렉토리 순회 경고 문구가 실제로 존재함을 확인) |
| 8. 전체 회귀 검증 | 기존 대화 지속성, TUI, Codex 스트리밍 기능이 깨지지 않음 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` 기존 통과 건수(300) 이상 PASS, 신규 실패 없음 |

## 이번 범위에 포함하지 않는 것 (명시적 제외)

- **세션 도중 컨텍스트 파일 재로딩(hot reload)** — pi도 별도 refresh 트리거로 분리되어 있고, AgentOS의 세션은 불변 메시지 체인이므로 재로딩은 "새 system 메시지 추가"라는 별도 설계가 필요해 제외한다.
- **커스텀 `SYSTEM.md`/`APPEND_SYSTEM.md` 오버라이드 지원(pi의 `discoverSystemPromptFile`)** — 이번 범위는 pi의 project-context/skill 주입만 이식하고, 전체 시스템 프롬프트 교체 기능은 별도 조사가 필요해 제외한다.
- **조상 디렉토리 순회 범위를 사용자가 세밀하게 제한하는 옵션(예: "N단계까지만" 설정)** — 이번 범위는 전면 on/off(`AGENTOS_SKIP_CONTEXT_BOOTSTRAP`)만 제공한다. 세밀한 depth 제한이나 디렉토리별 allowlist는 실사용 피드백을 본 뒤 별도 계획에서 다룬다.
- **스킬 본문을 LLM이 실제로 "읽어오는" 도구(read tool) 연동** — AgentOS는 현재 파일 읽기 도구를 LLM에 노출하지 않으므로, `<available_skills><location>`은 안내 텍스트로만 존재하고 실제 lazy-load 소비 경로는 이번 범위 밖이다(선행 시스템 필요).
- **확장(extension)/프롬프트 템플릿/테마 로더(pi의 `additionalExtensionPaths` 등)** — AgentOS에 대응 개념이 없고 이번 계획의 목표(AGENTS.md/CLAUDE.md + 스킬 메타데이터 주입)를 벗어나므로 제외한다.
- **`AGENTS.md`/`CLAUDE.md` 안의 `@파일경로` 참조(`@`-include) 재귀 전개** — 이 저장소 자신의 `CLAUDE.md`가 `@AGENTS.md`/`@.agents/vendors/claude.md` 형태로 다른 파일을 참조하지만, `discover_context_files()`는 원문을 그대로 읽을 뿐 이 참조 문법을 해석·전개하지 않는다(실사용 중 발견된 갭, 2026-07-25). **pi와 hermes-agent 둘 다 이 문법을 지원하지 않음을 코드 확인으로 검증했다**(pi: `references/pi/packages/coding-agent/src/core/resource-loader.ts`의 `loadContextFileFromDir`/`loadProjectContextFiles`는 `readFileSync`로 원문만 반환, `system-prompt.ts`의 `buildSystemPrompt`도 후처리 없이 그대로 삽입. hermes-agent: `references/hermes-agent/agent/prompt_builder.py`의 `_load_agents_md`/`_load_claude_md`도 동일하게 원문만 읽음 — 상세는 `.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md` 참조). 즉 `@`-include는 어느 레퍼런스의 기능도 아니라 Claude Code 고유의 `CLAUDE.md` 문법이므로, 이식이 아니라 신규 조사·설계가 필요하다. 사용자 확인 결과 별도 후속 계획으로 분리하기로 함.
- **Prompt injection 스캔 (hermes-agent 비교 조사에서 발견, 후속 계획 반영 대상으로 사용자 확인)** — hermes-agent의 `_scan_context_content()`(`agent/prompt_builder.py:50-66`)는 컨텍스트 파일 내용을 시스템 프롬프트에 넣기 전에 위협 패턴(프롬프트 인젝션, 역할극 하이재킹 등)을 검사해 발견 시 `[BLOCKED: ...]`로 대체한다. 현재 AgentOS의 `build_bootstrap_message()`는 `redact_text()`(시크릿 마스킹)만 적용하고 이런 인젝션 탐지가 없다 — 조상 디렉토리를 pi 방식으로 폭넓게 순회하는 AgentOS는 hermes보다 신뢰할 수 없는 상위 디렉토리 파일을 주울 위험이 더 크므로, 이번 범위에는 넣지 않되 후속 계획에서 우선 반영 대상으로 명시한다. 상세는 리서치 파일 참조.
- **모델 컨텍스트 윈도우 비례 동적 truncation (hermes-agent 비교 조사에서 발견, 후속 계획 반영 대상으로 사용자 확인)** — hermes-agent의 `_dynamic_context_file_max_chars()`(`agent/prompt_builder.py:1195-1228`)는 파일 크기 상한을 모델의 context window에 비례해 계산하고, 초과 시 head+tail만 남기며 전체를 읽는 법(`read_file` 경로)을 안내한다. 현재 AgentOS는 파일 크기 제한이 전혀 없어 거대한 `AGENTS.md`가 그대로 시스템 메시지에 들어간다 — 이번 범위에는 넣지 않되 후속 계획에서 반영 대상으로 명시한다. 상세는 리서치 파일 참조.

## 리뷰 반영 이력
- 초안 작성 — 2026-07-24. `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi`의 `resource-loader.ts`/`system-prompt.ts`/`skills.ts`를 직접 읽고 AgentOS의 `ConversationState`/`TRUSTED_SYSTEM_SOURCE`/`empty_state()`/`get_skills_dir()`와의 접합점을 확인해 초안 작성.
- 1차 `plan-reviewer` 리뷰 — 2026-07-24, FAIL. 두 가지 사유: (1) pi 레퍼런스 경로가 `agentos` 저장소 하위 상대 경로로 검증되지 않아 재현 불가능한 주장으로 판정됨 → "의존성 분석" 섹션에 워크스페이스 루트 기준 절대 경로(`/home/gabriel/agent/prj-agent/agentos-workspace/references/pi`)와 정확한 파일별 인용 근거를 명시해 수정함. (2) 이 계획은 CLI 안내 문구(`docs/cli-reference.md`)를 바꾸는 user-facing 계획이므로 `usability-reviewer` PASS가 AGENTS.md Rule 6/plan-reviewer 규칙상 override 불가능한 필수 게이트임을 지적받음 → 사용자 지시("핵심만 리뷰")를 이유로 생략하려던 문구를 제거하고, `usability-reviewer` 리뷰를 실제로 요청하는 것으로 정정함(아래 기록).
- 2차 `plan-reviewer` 재검토 — 2026-07-24, PASS. pi 레퍼런스 절대 경로 실존 및 인용 라인 정확성 재확인, usability-reviewer 우회 문구 완전 제거 확인.
- `principle-auditor` 리뷰 — 2026-07-24, PASS(승인). P1/P4/신뢰경계/조상디렉토리 순회 안전성(파일시스템 루트에서 정지, 디렉토리당 고정 파일명 2개만 확인해 glob/recurse 없음) 모두 검증 완료. 아티팩트: `.agents/traces/reviews/2026-07-24-agentos-pi-bootstrap-context/principle-auditor.json`.
- 1차 `usability-reviewer` 리뷰 — 2026-07-24, FAIL. 4가지 사유: (1) "사용자 결과 요약"이 `/status`로 로드된 파일을 확인할 수 있다고 약속했으나 어떤 마일스톤도 이를 구현/검증하지 않음, (2) 조상 디렉토리에 있는 민감하거나 큰 `AGENTS.md`/`CLAUDE.md`를 원치 않는 사용자를 위한 opt-out이 전혀 없음, (3) 컨텍스트 파일 읽기 실패(권한/인코딩/심볼릭 링크) 시 동작이 전혀 명시되지 않음, (4) `docs/cli-reference.md` 검증이 "AGENTS.md 문자열 존재"만 확인해 실제로 조상 디렉토리 순회 경고가 있는지는 강제하지 않음. → 마일스톤 5("가시성 배너와 `/status` 확장")·6("읽기 실패 내성과 opt-out")을 신규 추가하고, 마일스톤 7의 grep 검증을 opt-out 변수명·조상 디렉토리 경고 문구까지 구체적으로 확인하도록 강화했으며, "사용자 결과 요약"/"아키텍처"/"이번 범위에 포함하지 않는 것" 섹션에 배너 문구·opt-out 환경변수(`AGENTOS_SKIP_CONTEXT_BOOTSTRAP`)·읽기 실패 시 조용히 건너뛰는 동작을 명시함.

## 구현 결과

8개 마일스톤 모두 계획대로 구현하고 검증했다.

- 신규 `agentos/conversation/bootstrap.py`: `discover_context_files()`(전역 + 조상 디렉토리 순회, 디렉토리당 첫 매치, 읽기 실패는 `ContextFile.skipped`/`skip_reason`으로 표시), `discover_skills()`(`SKILL.md` 프론트매터 name/description만 파싱, 프론트매터 없으면 디렉토리명/첫 줄 fallback), `build_bootstrap_message()`(pi와 동일한 `<project_context>`/`<available_skills>` XML 조립, `redact_text()` 새니타이즈, 구조화된 경로/스킬명을 `metadata`에 저장), `build_bootstrap_message_for_session()`(opt-out 환경변수 `AGENTOS_SKIP_CONTEXT_BOOTSTRAP` 체크를 포함하는 최상위 진입점), `find_bootstrap_message()`(이미 커밋된 부트스트랩 메시지를 재파싱 없이 찾는 조회 헬퍼).
- `agentos/conversation/persistence.py`에 `empty_state_with_bootstrap()` 추가 — `empty_state()`를 감싸 부트스트랩 메시지가 있으면 브랜치의 첫 메시지로 커밋.
- `agentos/terminal/sessions.py`의 `resume_conversation_state()`가 "한 번도 persist된 적 없음" 분기에서만 위 함수들을 호출하도록 연결(`cwd` 파라미터 추가, 기본값 `Path.cwd()`). 재개/마이그레이션 경로는 그대로 유지되어 중복 주입되지 않음.
- `agentos/terminal/interaction.py`: 세션 생성 직후 `_print_bootstrap_banner()`가 배너를 출력하고(신규 세션·`/session resume` 양쪽), `/status` 핸들러가 로드된 컨텍스트 파일 경로와 스킬 이름을 나열하도록 확장.
- `docs/cli-reference.md`에 "Bootstrap Context" 섹션 추가 — 조상 디렉토리 순회 위험, `AGENTOS_SKIP_CONTEXT_BOOTSTRAP` opt-out, `/status` 확인법을 모두 명시.
- 테스트: 신규 `tests/test_conversation_bootstrap.py`(12개), `tests/test_interactive_cli.py`에 배너/`/status` 테스트 추가. 테스트 스위트 전체가 이 저장소 자신의 `AGENTS.md`를 우연히 픽업하지 않도록 `tests/conftest.py`에 autouse fixture로 `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1` 기본 적용(부트스트랩을 직접 검증하는 테스트는 자체 `monkeypatch`로 재정의). 기존 `test_conversation_persistence.py`의 신규 세션 테스트 1건을 격리된 cwd를 쓰도록 조정.
- 전체 검증: `uv run pytest tests/ -q` → 313 passed(회귀 없음, 신규 13개 포함). `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` → 16 passed. `grep` 기반 docs 검증 3건 모두 통과.

## 사용 방법

- `AGENTS.md` 또는 `CLAUDE.md`를 프로젝트 루트(또는 상위 디렉토리, 또는 `AGENTOS_HOME/core`)에 두면 다음에 여는 새 세션부터 자동으로 로드된다. 별도 조작 불필요.
- `agentos skill install <path>`로 설치한 스킬은 다음 새 세션부터 name/description/location이 자동으로 노출된다.
- 세션 시작 시 "부트스트랩 컨텍스트: N개 파일, M개 스킬 로드됨 — /status로 확인" 배너로 로드 여부를 바로 확인할 수 있다.
- `/status`를 입력하면 실제로 로드된 컨텍스트 파일의 전체 경로와 스킬 이름 목록이 출력된다.
- 원치 않으면(민감한 상위 디렉토리 파일, 토큰 비용 등) 세션 시작 전에 `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1`을 설정하면 부트스트랩 전체가 생략된다.
- 기존 세션을 재개(`/session resume <id>`)하면 최초 생성 시점에 이미 커밋된 부트스트랩 메시지가 그대로 유지되며 재주입되지 않는다.

## 아카이브 결정

2026-07-26 아카이브. Gate 2 리뷰 3종(plan-reviewer/principle-auditor/usability-reviewer) 모두 PASS(증거: `.agents/traces/reviews/2026-07-24-agentos-pi-bootstrap-context/`), 8개 마일스톤 `Run:`/`Expected:` 검증 전부 PASS, 전체 테스트 스위트 313 passed로 완료 확인. 사용자 확인 후 `plan_lifecycle.py archive`로 `active/` → `archive/` 이동.
