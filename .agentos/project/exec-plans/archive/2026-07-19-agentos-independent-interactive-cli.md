# AgentOS 독립 대화형 CLI 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-19<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> implementation_started_at: 2026-07-19T06:40:00Z<br>
> implementation_completed_at: 2026-07-19T06:54:07Z<br>
> implementation_duration: 14m 7s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** source checkout과 현재 작업 디렉터리에 의존하지 않는 AgentOS 자체 CLI를 만들고, 대화형 입력·session·선언형 hook을 동일한 이벤트 계약 위에서 안전하게 운영한다.

**사용자 결과:** 사용자는 설치한 `agentos` 한 명령으로 대화형 세션을 시작하거나 단발 자동화를 실행하고, hook과 입력 처리 결과를 이해 가능한 상태·복구 안내와 함께 사용할 수 있다.

**진행 상태:** ADR-0005와 root project 문서는 갱신되었고, Gate 2 reviewer evidence가 PASS/CLEAN으로 확보되었다. 구현과 fresh verification이 완료되었다.

**아키텍처:** 기존 `agentos/cli.py`와 provider runtime을 유지한 채, terminal shell을 command router, input/session service, built-in hook pipeline, typed event renderer로 분리한다. text interactive mode와 JSONL automation mode는 동일한 turn/event 모델을 소비한다. setup은 CLI user-home만 초기화하고 harness는 explicit project-root adapter로 유지하여 protected `.agents` asset을 package에 복제하지 않는다. pi에서 mode/event/session separation을, Hermes에서 command family·diagnostic/recovery pattern을 가져오되 각 프로젝트의 runtime과 gateway는 이식하지 않는다.

**기술 스택:** Python 3.11+, Typer, Rich, `tomllib`, `pathlib`, `json`, `subprocess`, `pytest`, `pexpect` 또는 표준 pseudo-TTY helper (둘 중 하나를 구현 전 dependency gate에서 확정).

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | ADR-0002 취소 표기, ADR-0005 추가, root project 문서 정렬, 독립 CLI/session/hook 구현, focused/isolated/user-flow/public verification |
| 현재 위치 | active plan closeout 완료 |
| 다음 단계 | 사용자 요청 시 archive 또는 PR/commit 준비 |
| 완료 신호 | `PASS cli-focused-suite`, `PASS agentos-cli-isolated-install`, `PASS interactive-cli-acceptance`, `PASS agentos-independent-cli-suite` |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `agentos`로 시작하는 대화형 CLI, 단발 실행, session 관리, hook 상태 확인, 설치·진단·복구 안내 |
| 누구를 위한 것인가? | AgentOS를 로컬에서 사용하거나 자동화에 연결하는 개발자와 harness 운영자 |
| 일상 사용에서 무엇이 달라지는가? | source checkout의 `.agents` 경로나 단순 mock REPL을 추측하지 않고, help와 오류가 다음 명령을 알려 주며 입력 취소·hook 실패도 예측 가능하게 복구된다. |
| 무엇은 바뀌지 않는가? | Codex account-login은 외부 Codex CLI가 소유하며 AgentOS는 raw credential, API key, provider stderr를 저장·노출하지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 설치 가능한 CLI | 다른 디렉터리에서도 `agentos --help/setup/doctor` 사용 | package metadata, paths, setup/doctor | `PASS agentos-cli-isolated-install` |
| 2. 공통 실행 계약 | `agentos`, `run --once`, `--json`이 같은 event/exit semantics 제공 | command router, event/render modules | `PASS cli-run-contract` |
| 3. 대화형 session | 입력, Ctrl-C/EOF, session 재개와 복구가 일관됨 | interactive/session modules | `PASS interactive-cli-contract` |
| 4. Hook 입력 관리 | 사용자가 허용된 input policy를 설정하고 실패 이유를 확인 | declarative hook modules, config | `PASS cli-hook-secret-regression` |
| 5. 안내와 릴리스 근거 | 설치·사용·복구 문서가 실제 명령과 일치 | README, getting-started, CLI reference | `PASS cli-docs-aligned`; `PASS agentos-independent-cli-suite` |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, `.agentos/project/exec-plans/evolution-status.md`.
- durable result surface: `agentos/`, `pyproject.toml`, `tests/`, `scripts/verify-cli-*.sh`, `README.md`, `README.ko.md`, `docs/getting-started.md`, `docs/cli-reference.md`, 그리고 project root contract docs.
- documentation-only exception: 없음. 이 계획은 product CLI와 검증을 구현한다.

## 설계 결정과 구현 가이드

### 1. 명령 grammar와 mode

root `agentos`만 TTY에서 interactive text mode를 시작한다. root command의 stdin 또는 stdout이 TTY가 아니면 묵시 전환하지 않고 `agentos run --once <prompt>` 또는 `--json`을 stderr로 안내하고 exit `2`로 종료한다. `agentos run --once`와 `agentos run --once --json`은 pipe/redirected stdout에서 유효하며 command 표면은 아래로 고정한다.

```text
agentos [--version] [--help]                         # TTY interactive session
agentos run --once PROMPT [--provider P] [--json]
agentos session list | show ID | resume ID | delete ID [--yes] | prune --before DATE [--yes]
agentos hook list | enable NAME | disable NAME | config show
agentos setup [--home PATH]
agentos doctor [--json]
agentos llm status|login|logout --provider P [--json]
agentos harness [--project-root PATH] [engine args...]
```

- root `agentos` does not silently become `run`; it is the interactive shell only.
- `--json` is valid only for commands with a documented machine contract. It writes one sanitized JSON object per stdout line; diagnostics go only to stderr.
- `run --once` is the scriptable turn entry point. Positional prompt, empty prompt, unsupported provider, no-TTY, invalid option, cancellation의 exit code와 recovery text를 table-driven tests로 고정한다.
- existing `agentos` and `aos` console entry points remain aliases. Hidden legacy aliases (`skill add`, `agent add`) remain until a separate deprecation decision.

| Situation | stdout | stderr/text recovery | exit |
|---|---|---|---|
| `agentos` in valid TTY, `/exit` or EOF | text session close only | none | 0 |
| root `agentos` without TTY | none | `Interactive mode requires a TTY. Next: agentos run --once "<prompt>".` | 2 |
| `run --once` success | text response; JSONL if `--json` | none | 0 |
| invalid option, empty prompt, invalid session/hook config | no JSONL payload | specific validation and next command | 2 |
| unsupported provider or provider failure | exactly one sanitized `error` JSONL event in JSON mode; none otherwise | sanitized recovery only | 1 |
| critical hook rejection/timeout | exactly one sanitized `error` JSONL event in JSON mode; none otherwise | hook name, phase, recovery; no input echo | 1 |
| non-critical hook failure | normal response/event stream | one sanitized warning | 0 |
| first Ctrl-C in interactive turn | text cancellation status | `Turn cancelled. You can enter another prompt or /exit.` | stays in session |
| second Ctrl-C during cancellation | none | `Exiting after cancellation.` | 130 |
| `session delete` confirmation declined or `prune` preview/no-match | preview/status only | none | 0 |
| `session delete` or `prune` without TTY and without `--yes` | no mutation; no JSONL payload | `Confirmation requires a TTY. Next: rerun the same command with --yes.` | 2 |
| requested session absent | none | `Session <id> was not found. Next: agentos session list` | 2 |

### 2. Typed event, session, hook contract

All renderers consume an immutable `CliEvent` envelope: `schema_version`, `type`, `session_id`, `turn_id`, `timestamp`, `provider`, `mode`, `payload`, `metadata`. `payload` never contains raw environment, credential, or unredacted provider stderr. Initial event types are `session_started`, `input_received`, `input_normalized`, `hook_started`, `hook_completed`, `hook_failed`, `turn_started`, existing LLM `start/message_delta/done/error`, `turn_cancelled`, `session_closed`.

Session storage is `AGENTOS_HOME/sessions/<uuid>.jsonl` plus `AGENTOS_HOME/sessions/<uuid>.meta.json`. Metadata schema `agentos.session/v1` contains only `session_id`, `created_at`, `updated_at`, `provider`, `mode`, `event_schema_version`, and optional user label. Event files use `agentos.cli-event/v1`; neither schema contains raw environment or provider stderr. Create files with user-only permissions where supported, write through a sibling temp file plus atomic rename, and validate schema/version before resume. There is no automatic retention deletion: sessions remain until the user explicitly cleans them. `session delete ID` prompts `Delete session <id>? [y/N]`; non-interactive use without `--yes` exits `2` with `Confirmation requires a TTY. Next: rerun the same command with --yes.` and changes nothing. `session prune --before DATE` first lists exact affected IDs and requires the same confirmation/`--yes`; no-match reports `No sessions matched; nothing deleted.` and exits `0`. A declined confirmation changes nothing. Session content is local user data; diagnostics and hook metrics store only counts, duration, result code, and redacted reason.

First-MVP hooks are built-in declarative policies loaded from `AGENTOS_HOME/config.toml`, schema `agentos.hooks/v1`: `trim_whitespace`, `reject_empty`, `prepend_context_file`, `max_input_chars`, and `record_turn_metrics`. There is no `command`, Python import, shell expansion, or project-local code hook. Every hook entry has exact fields `enabled:boolean`, `order:integer(0..999)`, `critical:boolean`, and `timeout_ms:integer(1..2000)`; omitted timeout defaults to `2000`. `agentos hook enable|disable NAME` validates NAME against the registry then atomically persists the boolean configuration; `hook list` prints effective phase/order/enabled/critical state and `hook config show` prints redacted effective TOML values. `prepend_context_file` is disabled by default and accepts a basename only; its resolved target must be a regular non-symlink UTF-8 `.md` file directly below `AGENTOS_HOME/context/`, no larger than `65536` bytes. Critical validation hooks fail closed before provider invocation; non-critical metric hooks warn on stderr/text status and continue. User configuration is validated before activation.

### 3. Packaging and project-local harness adapter

`agentos setup` initializes only the user-owned CLI state (`config.toml`, `sessions/`, `context/`, schema manifest) under `AGENTOS_HOME`; it never copies `.agents` or a harness asset. The installer validates target containment, creates required directories with user-only permissions when supported, and writes the schema manifest atomically. `doctor` reports the CLI state schema and optional harness availability. `harness` accepts mandatory `--project-root`; it canonicalizes that root, requires `<root>/.agents/skills/harness/core-engine/harness_loop.py`, and rejects a missing engine with `Next: run agentos setup for CLI state, then pass the AgentOS project with --project-root.` It does not discover parent directories or package protected harness files.

### 4. Interactive UX

Use Rich for rendering and a minimal line editor compatible with Python's terminal facilities; do not add a full-screen TUI in this plan. The prompt shows the active provider and a short session label. `/help`, `/status`, `/session`, `/hooks`, `/clear`, and `/exit` are CLI-shell commands and never become provider prompts. `/session` shows `list`, `show <id>`, `resume <id>` usage or performs those read/resume actions; deletion/pruning is delegated to explicit `agentos session` commands. `/hooks` shows the effective table and directs mutation to `agentos hook enable|disable`. Ctrl-C cancels the active input/turn once, leaves the prior valid session intact, and returns to the prompt. EOF and `/exit` close the session cleanly. A second Ctrl-C during cancellation exits `130`. No-TTY root execution never blocks waiting for input.

### 5. Reference adoption boundary

| Reference | Adopt | Do not adopt |
|---|---|---|
| pi | shared session/event model across text and JSON modes, explicit print/interactive separation, session id validation, project-trust boundary | Bun/TypeScript runtime, virtual-DOM TUI, extension code loading, provider catalog |
| Hermes | command-family organization, early diagnostic/recovery paths, input sanitation, explicit session actions | gateway, platform connectors, process-title/platform bootstrapping, arbitrary plugin behavior |

## 의존성 분석

- 외부 의존성: 아래에 선언함.
- 스캔 기준: Python/Typer/Rich package, package build and isolated-install commands, pseudo-TTY verification, user-state initialization, explicit project-root harness adapter, provider runtime assumptions.

## 의존성 게이트

### Python development environment
- name: Python development environment
- type: nonstandard-local-tool
- required: true
- purpose: install declared runtime and test dependencies reproducibly.
- preflight:
  Run: `uv sync --group dev && .venv/bin/python -c "import typer, rich; print('PASS cli-dev-deps-ready')"`
  Expected: `PASS cli-dev-deps-ready`
- fallback:
  available: false
  reason: system `pytest` without Typer/Rich cannot prove the package contract.
- failure_behavior: NEEDS_CONTEXT

### Pseudo-TTY test runtime
- name: Pseudo-TTY test runtime
- type: nonstandard-local-tool
- required: true
- purpose: prove Ctrl-C, EOF, prompt and recovery behavior without a manual terminal.
- preflight:
  Run: `.venv/bin/python -c "import pty; print('PASS pty-stdlib-ready')"`
  Expected: `PASS pty-stdlib-ready`
- fallback:
  available: true
  trigger: `pexpect` is unavailable or incompatible on a supported platform.
  action: use a checked-in standard-library `pty` test helper with the same acceptance transcript.
  limits: no full-screen cursor-layout assertion; the first MVP deliberately has no full-screen TUI.
  verification:
    Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --self-check`
    Expected: `PASS pty-cli-driver-ready`
- failure_behavior: use_fallback

## 파일 구조

- 수정: `pyproject.toml` - console scripts and test dependency declaration.
- 수정: `agentos/cli.py` - root command callback, TTY dispatch, shared context and command registration.
- 수정: `agentos/commands/run.py`, `agentos/commands/setup.py`, `agentos/commands/doctor.py`, `agentos/commands/harness.py`, `agentos/commands/llm.py` - command implementations moved onto the shared contracts without changing credential boundaries.
- 생성: `agentos/commands/session.py`, `agentos/commands/hook.py` - Typer command groups for session CRUD and declarative-hook state; both are registered by `agentos/cli.py`.
- 생성: `agentos/terminal/__init__.py` - terminal subsystem public boundary.
- 생성: `agentos/terminal/events.py` - versioned `CliEvent`, serialization and validation.
- 생성: `agentos/terminal/paths.py` - `AGENTOS_HOME`, containment, schema-manifest and permission helpers.
- 생성: `agentos/terminal/sessions.py` - atomic session JSONL/metadata storage and lifecycle.
- 생성: `agentos/terminal/hooks.py` - declarative built-in hook registry, validation, order, timeout and redaction.
- 생성: `agentos/terminal/interaction.py` - TTY input loop, slash command parsing, cancellation/EOF state machine.
- 생성: `agentos/terminal/render.py` - text and JSONL renderer separation.
- 생성: `tests/test_cli_contract.py`, `tests/test_interactive_cli.py`, `tests/test_cli_hooks.py`, `tests/test_cli_isolated_install.py` - command, terminal, hook, package behavior regressions.
- 생성: `tests/helpers/pty_cli_driver.py` - portable pseudo-TTY transcript driver.
- 생성: `scripts/verify-cli-isolated-install.sh`, `scripts/verify-cli-user-flow.sh` - reproducible user-facing acceptance scripts.
- 생성: `docs/cli-reference.md` - command grammar, modes, hooks, sessions, recovery and privacy reference.
- 수정: `README.md`, `README.ko.md`, `docs/getting-started.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md` - user docs and requirement/contract traceability.

## 작업

### Task 0: 실행 기준과 기존 계약을 고정한다

**파일:**
- 수정: `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`
- 생성: 테스트·script paths listed in File Structure

**사용자에게 보이는 마일스톤:** 설치 전제와 command/hook 안전 경계가 명확해져, 구현 중 기존 provider 계약이 흔들리지 않는다.

- [x] **Step 0.1: 개발 의존성과 baseline을 기록한다.**

`uv sync --group dev` 후 existing focused tests를 `.venv/bin/python`으로 실행한다. 기존 `uv run pytest`가 system interpreter에서 Typer를 찾지 못한 경우를 product regression으로 오인하지 말고, dependency preflight failure로 기록한다.

Run: `uv sync --group dev && .venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py tests/test_codex_provider.py -q && echo 'PASS cli-baseline'`
Expected: `PASS cli-baseline`

- [x] **Step 0.2: ADR·requirements·provider safety contracts의 reference를 검증한다.**

Run: `rg -q 'REQ-CLI-001' .agentos/project/02-product-scope-and-requirements.md && rg -q '0005-agentos-independent-interactive-cli' .agentos/project/03-system-contract.md .agentos/project/04-safety-risk-verification.md .agentos/project/06-decisions-change-log.md && rg -q 'status: 취소됨' .agentos/project/reference/decisions/0002-agentos-repl-deprecation.md && rg -q 'raw token' .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo 'PASS cli-doc-contract'`
Expected: `PASS cli-doc-contract`

- [x] **Step 0.3: Gate 2 리뷰 증거를 확보한다.**

`plan-reviewer`, `principle-auditor`, `usability-reviewer`는 서로 다른 reviewer identity/source로 이 계획의 최신 SHA-256을 검토한다. plan 수정마다 세 artifact를 새 SHA로 갱신하며, protected `.agents/` asset 변경이 포함되면 authorized-architect approval을 추가로 받는다.

Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-19-agentos-independent-interactive-cli.md`
Expected: `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`

### Task 1: CLI shell과 user-state installation 기반을 구현한다

**파일:**
- 수정: `pyproject.toml`, `agentos/cli.py`, `agentos/commands/setup.py`, `agentos/commands/doctor.py`, `agentos/commands/harness.py`
- 생성: `agentos/terminal/__init__.py`, `agentos/terminal/paths.py`, `tests/test_cli_isolated_install.py`, `scripts/verify-cli-isolated-install.sh`

**사용자에게 보이는 마일스톤:** 설치된 명령이 source checkout 밖에서도 동일한 help, setup, doctor, explicit project-root harness recovery를 제공한다.

- [x] **Step 1.1: user-state path resolver를 만든다.**

`AGENTOS_HOME`의 absolute canonical path를 한 곳에서 resolve한다. CLI-state destination의 symlink escape·relative traversal·existing incompatible schema manifest를 fail closed한다. setup은 `config.toml`, `sessions/`, `context/`, `state-manifest.json`만 만들고 project harness asset을 copy하지 않는다.

Run: `.venv/bin/python -m pytest tests/test_cli_isolated_install.py -q -k 'paths or state or containment' && echo 'PASS cli-path-state-contract'`
Expected: `PASS cli-path-state-contract`

- [x] **Step 1.2: setup/doctor/harness의 설치·복구 계약을 바꾼다.**

`setup`은 CLI-state directory creation과 schema-manifest atomic write를 수행하며 existing compatible state를 idempotently preserve한다. `doctor --json`은 schema-versioned sanitized status를 출력한다. `harness --project-root`는 explicit root만 확인해 engine argv를 quoted data로 전달한다.

Run: `.venv/bin/python -m pytest tests/test_cli_contract.py tests/test_cli_isolated_install.py -q -k 'setup or doctor or harness' && echo 'PASS cli-install-diagnostic-contract'`
Expected: `PASS cli-install-diagnostic-contract`

- [x] **Step 1.3: 실제 installed console script를 isolated environment에서 검증한다.**

script는 `mktemp -d` 아래 virtual environment를 만들고 wheel/install을 수행한 뒤, source tree 밖 cwd에서 `agentos --help`, setup, doctor, missing-project harness recovery를 확인한다. cleanup은 validated temp directory만 trap에서 제거한다.

Run: `bash scripts/verify-cli-isolated-install.sh`
Expected: `PASS agentos-cli-isolated-install`

### Task 2: 공통 event와 단발 실행 contract를 구현한다

**파일:**
- 수정: `agentos/cli.py`, `agentos/commands/run.py`, `agentos/commands/llm.py`, `agentos/llm/types.py`, `agentos/llm/session.py`
- 생성: `agentos/terminal/events.py`, `agentos/terminal/render.py`, `tests/test_cli_contract.py`

**사용자에게 보이는 마일스톤:** 사람이 보는 text output과 자동화 JSONL이 같은 turn 상태를 안정적인 순서와 exit code로 전달한다.

- [x] **Step 2.1: `CliEvent` envelope와 renderer를 도입한다.**

기존 `LLMEvent`는 provider adapter의 하위 event로 보존하고, CLI layer가 session/turn metadata를 추가한다. JSONL renderer에는 ANSI/Rich markup·progress·debug text를 쓰지 않으며 text renderer는 human recovery를 보여 준다.

Run: `.venv/bin/python -m pytest tests/test_cli_contract.py -q -k 'event or jsonl or stdout' && echo 'PASS cli-event-contract'`
Expected: `PASS cli-event-contract`

- [x] **Step 2.2: root/`run --once` option과 failure matrix를 고정한다.**

table-driven test로 exact exit matrix의 empty prompt, invalid option, root no-TTY, unsupported provider, `--json` misuse, provider error, critical/non-critical hook failure, Ctrl-C와 provider success를 검증한다. Existing provider JSONL event names `start`, `message_delta`, `done`, `error` and payloads remain unchanged for `run --once --json`; CLI lifecycle is added only as `metadata.cli` fields to those events, not as new top-level event names. A versioned regression fixture verifies prior machine consumers parse the unchanged sequence.

Run: `.venv/bin/python -m pytest tests/test_cli_contract.py tests/test_llm_core.py -q && echo 'PASS cli-run-contract'`
Expected: `PASS cli-run-contract`

### Task 3: 대화형 입력과 session lifecycle을 구현한다

**파일:**
- 수정: `agentos/cli.py`, `agentos/commands/run.py`
- 생성: `agentos/commands/session.py`
- 생성: `agentos/terminal/interaction.py`, `agentos/terminal/sessions.py`, `tests/test_interactive_cli.py`, `tests/helpers/pty_cli_driver.py`

**사용자에게 보이는 마일스톤:** 사용자는 TTY에서 `agentos`를 열어 입력하고, `/help`, `/status`, `/session`, `/hooks`, `/clear`, `/exit`, Ctrl-C, EOF를 예측 가능하게 사용할 수 있다.

- [x] **Step 3.1: session storage와 slash command state machine을 만든다.**

session ID는 UUID를 생성하고 user-provided ID는 strict format으로 validate한다. `session delete ID` preview/confirmation/`--yes`, `session prune --before DATE` affected-ID preview/confirmation/`--yes`, no-match, cancellation, requested-missing-session, non-TTY without `--yes` exit `2`/exact recovery/no mutation을 each test한다. malformed JSONL/metadata, foreign schema version, missing session은 읽기 전에 오류와 recovery를 출력하고 변경하지 않는다. `/clear`는 terminal display만 정리하며 saved history를 삭제하지 않는다.

Run: `.venv/bin/python -m pytest tests/test_interactive_cli.py -q -k 'session or slash or recovery' && echo 'PASS cli-session-contract'`
Expected: `PASS cli-session-contract`

- [x] **Step 3.2: pseudo-TTY cancel/EOF transcript를 검증한다.**

driver는 process start, `/help`, `/session`, `/hooks`, invalid slash command, normal prompt, first Ctrl-C, a second prompt, a second Ctrl-C during cancellation, and EOF를 separate transcripts로 실행한다. 별도 destructive transcript는 TTY `session delete ID`와 `session prune --before DATE`에서 default `N`, explicit `y`, affected-ID preview, post-action file absence를 assert한다. event/order, exact exit code, visible recovery, no hang timeout, valid persisted session, no secret output을 assertion한다. interactive test가 normal pipe에서 prompt를 기다리지 않는 것도 확인한다.

Run: `.venv/bin/python -m pytest tests/test_interactive_cli.py -q && .venv/bin/python tests/helpers/pty_cli_driver.py --self-check && echo 'PASS interactive-cli-contract'`
Expected: `PASS interactive-cli-contract`

### Task 4: 선언형 hook/input lifecycle을 구현한다

**파일:**
- 생성: `agentos/terminal/hooks.py`, `agentos/commands/hook.py`, `tests/test_cli_hooks.py`
- 수정: `agentos/terminal/events.py`, `agentos/terminal/interaction.py`, `agentos/terminal/sessions.py`, `agentos/commands/run.py`, `agentos/cli.py`

**사용자에게 보이는 마일스톤:** 사용자는 `agentos hook list`와 config를 통해 활성 정책과 결과를 확인하며, 입력 오류나 hook timeout에서 안전하게 복구한다.

- [x] **Step 4.1: versioned config와 built-in hook registry를 구현한다.**

`config.toml` parsing은 `agentos.hooks/v1`, field ranges, unknown key를 validate하고 secret-looking values는 display하지 않는다. built-in hook은 고정 registry만 허용하며 phase order는 stable sort `(phase, order, name)`이다. enable/disable persistence, default-disabled context hook, context filename basename validation, `AGENTOS_HOME/context` containment, non-symlink regular-file rule, 65536-byte limit을 test한다.

Run: `.venv/bin/python -m pytest tests/test_cli_hooks.py -q -k 'config or registry or ordering or context' && echo 'PASS cli-hook-registry-contract'`
Expected: `PASS cli-hook-registry-contract`

- [x] **Step 4.2: timeout, cancellation, error, redaction을 검증한다.**

critical hook rejection은 provider adapter가 호출되지 않았음을 mock으로 proof한다. non-critical metrics hook failure는 one warning event와 continued turn을 proof한다. synthetic sentinel은 hook config/input/provider diagnostic/captured stdout/stderr/session metadata 어디에도 남지 않아야 한다.

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_cli_hooks.py tests/test_llm_core.py -q && echo 'PASS cli-hook-secret-regression'`
Expected: `PASS cli-hook-secret-regression`

### Task 5: 사용 설명과 end-to-end verification을 완성한다

**파일:**
- 생성: `docs/cli-reference.md`, `scripts/verify-cli-user-flow.sh`
- 수정: `README.md`, `README.ko.md`, `docs/getting-started.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`

**사용자에게 보이는 마일스톤:** 새 사용자는 설치부터 첫 대화, 단발 자동화, hook 확인, 실패 복구, 개인정보 경계까지 실제 명령으로 따라갈 수 있다.

- [x] **Step 5.1: CLI reference와 onboarding을 갱신한다.**

문서는 command grammar, JSONL stdout/stderr rule, built-in hook list, session file ownership, no-TTY recovery, Codex credential boundary, example output의 redaction을 설명한다. README quickstart는 source checkout가 아닌 installed CLI user flow를 먼저 보여 준다.

Run: `rg -q 'agentos hook list' docs/cli-reference.md && rg -q 'agentos run --once' README.md README.ko.md docs/getting-started.md && rg -q 'raw token' docs/cli-reference.md && echo 'PASS cli-docs-aligned'`
Expected: `PASS cli-docs-aligned`

- [x] **Step 5.2: 사용자 관점 acceptance를 script로 실행한다.**

script는 isolated CLI를 setup하고 mock provider 대화 transcript, `/help`, `/session`, `/hooks`, enabled hook display, rejected empty input recovery, pseudo-TTY deletion preview/default-N/explicit-y/prune confirmation, non-TTY deletion-without-`--yes` exit `2` recovery, `--yes` deletion, Ctrl-C and second-Ctrl-C, JSONL one-turn compatibility fixture, doctor JSON, no-TTY root error path를 수행한다. stdout JSON parsing, stderr separation, timeout, no secret sentinel, session artifact integrity를 assert한다.

Run: `bash scripts/verify-cli-user-flow.sh`
Expected: `PASS interactive-cli-acceptance`

- [x] **Step 5.3: public boundary와 manifest를 최종 검증한다.**

`.agents`는 이 계획의 수정 대상이 아니다. public suite를 fresh run하고 unrelated known baseline failure가 있으면 PASS claim을 하지 않고 exact failure와 scope impact를 plan closeout에 기록한다.

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash scripts/verify-public-test-suite.sh && git diff --check && echo 'PASS agentos-independent-cli-suite'`
Expected: `PASS agentos-independent-cli-suite`

## 단순성 게이트

- 요구사항 밖에 추가한 컴포넌트: `terminal` subsystem, session/hook modules, pseudo-TTY verification.
- 필요한 이유: 독립 설치, interactive/automation parity, input/hook safety, user-facing recovery는 command function에 직접 섞으면 검증 불가능해진다. 이 모듈들은 각 책임을 하나씩만 가진다.
- 더 단순한 대안 검토: pi TUI·Hermes gateway·third-party hook runtime·packaged `.agents` asset을 채택하지 않는다. Rich line-oriented shell과 built-in declarative hooks, explicit project-root harness adapter만 구현한다.

## 리뷰 반영 이력

- 초안: ADR-0002 취소와 ADR-0005 승인 후 root project documents를 기준으로 작성.
- [Gate 2 1차] command owner, session/hook policy, exit matrix, JSONL compatibility, deletion recovery, protected asset boundary가 불명확함 → `commands/session.py`·`commands/hook.py` ownership, immutable schema/retention/config contracts, exact exit matrix, metadata-only JSONL compatibility, pseudo-TTY destructive-flow transcripts, no packaged `.agents` policy를 추가함.
- [Gate 2 2차] destructive confirmation의 pseudo-TTY coverage와 no-TTY deletion recovery가 불명확함 → TTY delete/prune default-N·explicit-y transcript, non-TTY no-`--yes` exit `2`/exact recovery/no-mutation contract를 추가함.

## 세션 인계 체크포인트

| 필드 | 현재 값 |
|---|---|
| 현재 완료 범위 | 독립 CLI, user-state setup/doctor, explicit harness adapter, run JSONL metadata, session CRUD, built-in hook lifecycle, docs, scripts |
| 미완료 작업 | 없음. archive/commit/PR은 별도 사용자 요청 대기 |
| 다음 세션 첫 작업 | 필요 시 active plan archive 또는 PR 준비 |
| 아직 안 한 검증 | 없음 |
| 관련 HISTORY checkpoint | `[EVOLUTION_APPLIED] trigger_id=agentos-independent-interactive-cli` closeout 기록 예정 |

## 구현 결과

- `agentos` root command는 TTY에서 interactive session을 열고 no-TTY에서는 exit `2`와 `agentos run --once "<prompt>"` 복구 안내를 낸다.
- `agentos setup`은 `AGENTOS_HOME` 아래 `config.toml`, `sessions/`, `context/`, `state-manifest.json`만 만들며 `.agents`를 복사하지 않는다.
- `agentos doctor --json`, `agentos harness --project-root`, `agentos session ...`, `agentos hook ...`, `agentos run --once [--json]` 계약을 구현했다.
- built-in declarative hook registry와 local session JSONL/meta 저장소를 추가했다.
- `docs/cli-reference.md`, README, getting-started, clean/isolated/user-flow verifier를 새 CLI 계약에 맞췄다.

## 사용 방법

```bash
uv run agentos setup
uv run agentos doctor
uv run agentos run --once "hello from AgentOS"
uv run agentos run --once "hello from AgentOS" --json
uv run agentos hook list
uv run agentos session list
```

TTY에서는 `uv run agentos`로 대화형 session을 시작한다. pipe/redirect 환경에서는 `agentos run --once`를 사용한다.

## 완료 증거

- `PASS cli-baseline`
- `PASS cli-doc-contract`
- `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`
- `PASS cli-path-state-contract`
- `PASS cli-install-diagnostic-contract`
- `PASS agentos-cli-isolated-install`
- `PASS cli-event-contract`
- `PASS cli-run-contract`
- `PASS cli-session-contract`
- `PASS interactive-cli-contract`
- `PASS cli-hook-registry-contract`
- `PASS cli-hook-secret-regression`
- `PASS cli-docs-aligned`
- `PASS interactive-cli-acceptance`
- `PASS agentos-independent-cli-suite`
- `PASS reviewer-gap-fixes`
- focused implementation suite: `53 passed`

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 이 완료된 계획은 `.agentos/project/exec-plans/active/`에 남긴다.
