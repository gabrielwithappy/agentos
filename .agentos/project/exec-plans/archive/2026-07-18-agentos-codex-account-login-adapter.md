# AgentOS Codex account-login adapter 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-18<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> usability_review_reason: 실제 provider status/login/logout, JSONL run, 오류/복구 문구를 추가하므로<br>
> implementation_started_at: 2026-07-18T14:33:13Z<br>
> implementation_completed_at: 2026-07-18T14:39:02Z<br>
> implementation_duration: 5m 49s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 승인된 `0004` credential strategy에 따라 Codex CLI의 ChatGPT account-login/session을 AgentOS real provider adapter로 안전하게 위임한다.

**사용자 결과:** 사용자는 API key를 AgentOS에 저장하지 않고도 기존 Codex CLI 로그인 상태를 통해 `agentos llm status --provider codex`와 `agentos run --json --once ... --provider codex`를 검증할 수 있다.

**진행 상태:** 구현 완료. Gate 2 review, Codex adapter implementation, tests, docs alignment, and real Codex smoke checks passed.

**아키텍처:** AgentOS는 Codex token이나 `auth.json`을 직접 파싱하지 않는다. `agentos/llm/providers/codex_cli.py`가 installed `codex` CLI를 subprocess로 호출하고, stdout JSONL/텍스트를 AgentOS `LLMEvent` 계약으로 정규화한다. 실제 네트워크와 session refresh는 Codex CLI가 소유하며, AgentOS는 sanitized status/event/error surface만 제공한다.

**기술 스택:** Python 3.11+, Typer, pytest, subprocess, dataclasses/typing, JSONL stdout events, Codex CLI.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Gate 2 review, Codex CLI provider adapter, CLI wiring, fake CLI tests, secret regression, docs alignment, real Codex status/run smoke |
| 현재 위치 | implementation closeout |
| 다음 단계 | 사용자가 원하면 active plan archive 또는 후속 VS Code/ACP bridge plan |
| 완료 신호 | fake Codex CLI tests, secret regression, opt-in real Codex status/run checks가 PASS했고 AgentOS가 raw credential을 저장하거나 출력하지 않음 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | Codex CLI 로그인 세션을 사용하는 AgentOS real provider adapter |
| 누구를 위한 것인가? | 프로젝트 오너, CLI 사용자, VS Code bridge 후속 구현자, 보안 리뷰어 |
| 일상 사용에서 무엇이 달라지는가? | `--provider codex`가 unsupported error 대신 Codex CLI 로그인 상태와 실제 응답을 JSON/JSONL로 반환할 수 있다. |
| 무엇은 바뀌지 않는가? | AgentOS는 API key를 받거나 저장하지 않고, 자체 OAuth client를 등록하지 않고, VS Code/ACP/app-server bridge를 구현하지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Codex CLI preflight | Codex CLI 설치·로그인 상태가 안전하게 진단됨 | `agentos/llm/providers/codex_cli.py`, `agentos/commands/llm.py` | `Run:` `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "status or login"`<br>`Expected:` selected tests pass |
| 2. Subprocess adapter | fake Codex CLI로 실제 provider event contract가 재현됨 | `agentos/llm/session.py`, `agentos/llm/providers/codex_cli.py` | `Run:` `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "stream or subprocess"`<br>`Expected:` selected tests pass |
| 3. CLI JSON/JSONL 연결 | `--provider codex`가 status/login/logout/run에 연결됨 | `agentos/commands/llm.py`, `agentos/commands/run.py` | `Run:` `.venv/bin/python -m pytest tests/test_cli.py tests/test_codex_provider.py -q`<br>`Expected:` selected tests pass |
| 4. 실제 Codex opt-in smoke | 로그인된 환경에서 실제 Codex status/run을 수동 opt-in으로 검증 가능 | local Codex CLI integration | `Run:` `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli llm status --json --provider codex`<br>`Expected:` sanitized JSON status |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/traces/reviews/2026-07-18-agentos-codex-account-login-adapter/`, `.agentos/project/exec-plans/README.md`.
- durable result surface: `agentos/llm/providers/codex_cli.py`, `agentos/llm/session.py`, `agentos/commands/llm.py`, `agentos/commands/run.py`, `tests/test_codex_provider.py`, `tests/test_llm_core.py`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`.
- documentation-only exception: 없음. 이 계획은 code and tests implementation plan이다.

## 의도 근거

- Intent Sheet: `.agentos/project/exec-plans/archive/reference/intent/intent-20260718-agentos-codex-account-login-adapter.md`
- Completed prerequisite: `.agentos/project/exec-plans/active/2026-07-18-agentos-llm-core-mvp.md`
- Approval ADR: `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- Reference analysis: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
- Official Codex auth docs: `https://developers.openai.com/codex/auth`, checked on 2026-07-18.

## 범위 및 비범위

포함:
- Codex provider id: `codex`.
- Codex CLI executable discovery with `CODEX_CLI_PATH` override and `codex` PATH fallback.
- `agentos llm status --json --provider codex` using `codex login status`.
- `agentos llm login/logout --provider codex` delegating to `codex login` and `codex logout` without reading raw credentials.
- `agentos run --json --once ... --provider codex` delegating to a Codex CLI one-shot run path, normalizing output to AgentOS `start`, `message_delta`, `done`, and `error` JSONL events.
- fake Codex CLI tests for installed/missing/unauthenticated/success/failure behavior.
- opt-in real integration checks guarded by `AGENTOS_CODEX_INTEGRATION=1`.
- redaction blocking raw token, raw key, raw environment, raw Codex stderr, auth file contents, and synthetic sentinel leaks.

제외:
- AgentOS 자체 OAuth browser/device-code implementation.
- OAuth client registration, redirect listener, token refresh/revocation implementation inside AgentOS.
- direct parsing of `~/.codex/auth.json` or OS keyring secrets.
- API key input/import/storage/API-key adapter.
- non-Codex provider registry, model catalog, gateway, daemon, marketplace, automatic failover.
- VS Code extension, ACP, Codex app-server protocol, long-running stdio server.
- tests that require real secrets in repo, logs, stdout/stderr, or artifacts.

## 의존성 분석

- 외부 의존성: installed Codex CLI for real integration only.
- Official auth basis: OpenAI Codex auth docs state Codex CLI supports ChatGPT sign-in via `codex login`, status via `codex login status`, logout via `codex logout`, local credential caching, and API key auth. This plan uses ChatGPT account-login only and excludes API key auth.
- Unit test baseline: fake Codex CLI scripts must cover all behavior without network or real credentials.
- Real integration gate: never run real provider calls unless `AGENTOS_CODEX_INTEGRATION=1` and `codex login status` succeeds.
- Billing/entitlement: approved in `0004`, but every real model-call verification remains explicit opt-in.
- Runtime assumption: `.venv/bin/python -m pytest` is the project test runner because plain `pytest` may resolve to system Python in this checkout.

## 의존성 게이트

| name | type | required | preflight Run / Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| Codex CLI | local executable | Unit tests에는 false. `AGENTOS_CODEX_INTEGRATION=1` real smoke에는 true. | `Run:` `command -v codex >/dev/null && codex --version >/tmp/agentos-codex-version.out && test -s /tmp/agentos-codex-version.out && echo "PASS codex-cli-installed" \|\| echo "PASS codex-cli-not-installed-unit-tests-only"`<br>`Expected:` one PASS line | fake Codex CLI unit tests only | Default verification skips real integration. 사용자가 real smoke를 명시 요청했는데 CLI가 없으면 NEEDS_CONTEXT로 보고한다. |
| Codex account-login session | local user auth session | Default/unit tests에는 false. 실제 logged-in status/run smoke에는 true. | `Run:` `codex login status` when and only when real smoke is requested or `AGENTOS_CODEX_INTEGRATION=1` is set.<br>`Expected:` exit 0 means authenticated; non-zero means unauthenticated. | sanitized unauthenticated status | `llm status` returns sanitized unauthenticated recovery. `run` emits one sanitized `error` event and exits non-zero. |
| Network/model entitlement | external service | Only with `AGENTOS_CODEX_INTEGRATION=1` one-shot run smoke. | `Run:` `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli run --json --once "Reply with OK." --provider codex`<br>`Expected:` JSONL `start`, `message_delta`, `done` if entitled. | fake CLI unit tests | Real run failure emits one sanitized `error` event, no token/raw stderr/env/auth file content, non-zero exit. |

## 사용자 출력 계약

`--provider codex`의 user-facing JSON/JSONL surface는 다음 계약을 구현하고 테스트한다.

- Missing CLI status/login/logout:
  - JSON fields include `provider:"codex"`, `mode:"account-login"`, `status:"missing_cli"`, `credential_present:false`, `authenticated:false`, `persistent_credential:false`, `action:<status|login|logout>`, and `next_command:"codex login"`.
  - `message` says the Codex CLI executable is not available without echoing PATH or environment.
  - `recovery` says `Install Codex CLI, then run: codex login`.
- Unauthenticated status:
  - JSON fields include `provider:"codex"`, `mode:"account-login"`, `status:"unauthenticated"`, `credential_present:false`, `authenticated:false`, `persistent_credential:false`, and `next_command:"agentos llm login --provider codex"`.
  - `recovery` says `Run: agentos llm login --provider codex or codex login`.
- Authenticated status:
  - JSON fields include `provider:"codex"`, `mode:"account-login"`, `status:"authenticated"`, `credential_present:true`, `authenticated:true`, `persistent_credential:true`, and no token/auth file path/raw CLI output.
- Login/logout JSON mode:
  - JSON fields include `provider:"codex"`, `mode:"account-login"`, `action:"login"` or `action:"logout"`, `status:<authenticated|logged_out|missing_cli|failed>`, `message`, and optional `recovery`/`next_command`.
  - Success reports only sanitized action/status result. Browser/device flow remains owned by Codex CLI.
- One-shot run failure:
  - JSONL contains exactly one `error` event when Codex CLI cannot start or returns non-zero before any output contract is established.
  - Error event includes `provider:"codex"`, `mode:"account-login"`, `error.code`, `error.message`, `recovery`, and `metadata.retryable`.
  - Raw stderr, environment, token strings, auth file contents, and auth file paths are not emitted.

## 파일 구조

- 생성: `agentos/llm/providers/codex_cli.py` - Codex CLI subprocess provider adapter.
- 수정: `agentos/llm/providers/__init__.py` - export Codex provider.
- 수정: `agentos/llm/session.py` - add provider registry for `mock` and `codex`.
- 수정: `agentos/commands/llm.py` - route status/login/logout to provider-specific behavior.
- 수정: `agentos/commands/run.py` - allow `--provider codex` JSONL run path.
- 수정: `tests/test_codex_provider.py` - fake Codex CLI unit/CLI/redaction/integration-gate tests.
- 수정: `tests/test_llm_core.py` - preserve mock contract and unsupported-provider expectations after `codex` becomes supported.
- 수정: `.agentos/project/03-system-contract.md` - record Codex CLI delegation interface.
- 수정: `.agentos/project/04-safety-risk-verification.md` - record Codex subprocess and integration verification gates.

## Task 0: 구현 전 preflight

**파일:**
- 수정: 없음

**사용자에게 보이는 마일스톤:** 승인·환경·baseline이 실제 provider 구현을 시작할 수 있는 상태인지 확인한다.

- [x] **Step 0.1: 승인 ADR과 API-key 제외 경계를 확인한다.**

Run: `rg -q "^approval_status: approved$" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "^credential_type: account-login$" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "API key.*사용하지 않음" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS codex-account-login-approved"`
Expected: `PASS codex-account-login-approved`

- [x] **Step 0.2: existing mock LLM baseline을 보존한다.**

Run: `.venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py -q`
Expected: tests pass.

- [x] **Step 0.3: Codex CLI 문서 기준 command availability를 기록한다.**

Run: `command -v codex >/dev/null && codex --version >/tmp/agentos-codex-version.out && test -s /tmp/agentos-codex-version.out && echo "PASS codex-cli-installed" || echo "PASS codex-cli-not-installed-unit-tests-only"`
Expected: one of `PASS codex-cli-installed` or `PASS codex-cli-not-installed-unit-tests-only`.

## Task 1: Codex CLI provider adapter 추가

**파일:**
- 생성: `agentos/llm/providers/codex_cli.py`
- 수정: `agentos/llm/providers/__init__.py`
- 수정: `agentos/llm/session.py`
- 생성: `tests/test_codex_provider.py`

**사용자에게 보이는 마일스톤:** AgentOS가 Codex CLI 로그인 상태를 secret-safe status로 읽고, fake Codex CLI를 통해 real provider event contract를 검증할 수 있다.

- [x] **Step 1.1: Codex CLI executable discovery와 sanitized subprocess env를 구현한다.**

`CODEX_CLI_PATH`가 있으면 해당 실행 파일을 우선 사용하고, 없으면 PATH의 `codex`를 사용한다. Subprocess env는 allowlist 방식으로 구성하고, AgentOS test sentinel과 필요한 process basics만 넘긴다. Raw environment dump는 어떤 error에도 넣지 않는다.

Run: `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "executable or subprocess_env"`
Expected: selected tests pass.

- [x] **Step 1.2: `codex login status`를 ProviderStatus로 정규화한다.**

Installed/missing/authenticated/unauthenticated cases를 fake CLI로 검증한다. `credential_present`와 `authenticated`는 status success 기준으로 true가 될 수 있지만, raw token/auth file path/content는 payload에 넣지 않는다.

Run: `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "status"`
Expected: selected tests pass.

- [x] **Step 1.3: `codex exec --json` 또는 documented one-shot run path를 LLMEvent stream으로 정규화한다.**

Fake CLI stdout이 JSONL이면 JSON object를 우선 파싱하고, 일반 텍스트이면 sanitized `message_delta`로 감싼다. Success order는 `start`, one or more `message_delta`, `done`이다. Failure order는 exactly one `error` event and non-zero caller exit이다.

Run: `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "stream or failure_event"`
Expected: selected tests pass.

## Task 2: CLI 명령 연결

**파일:**
- 수정: `agentos/commands/llm.py`
- 수정: `agentos/commands/run.py`
- 수정: `tests/test_codex_provider.py`
- 수정: `tests/test_llm_core.py`

**사용자에게 보이는 마일스톤:** `--provider codex`가 더 이상 unsupported가 아니며, 로그인 상태·로그인 위임·로그아웃 위임·one-shot run이 testable contract로 동작한다.

- [x] **Step 2.1: `agentos llm status --json --provider codex`를 연결한다.**

Run: `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "cli_status_codex"`
Expected: selected tests pass and JSON includes `provider:"codex"`, `mode:"account-login"`, and no raw secret values.

- [x] **Step 2.2: `agentos llm login/logout --provider codex`를 Codex CLI에 위임한다.**

Login command는 `codex login`을 호출하고, logout command는 `codex logout`을 호출한다. JSON mode에서는 sanitized action/status result만 출력한다. Interactive browser login 자체는 Codex CLI가 소유한다.

Run: `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "cli_login_logout_codex"`
Expected: selected tests pass.

- [x] **Step 2.3: `agentos run --json --once ... --provider codex`를 연결한다.**

Run: `.venv/bin/python -m pytest tests/test_codex_provider.py -q -k "cli_run_codex_jsonl"`
Expected: selected tests pass and JSONL includes `start`, `message_delta`, and `done`.

## Task 3: 보안 회귀와 실제 integration gate

**파일:**
- 수정: `tests/test_codex_provider.py`
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`

**사용자에게 보이는 마일스톤:** 실제 Codex 연동은 opt-in으로만 실행되고, unit tests는 real token 없이 secret-safe하게 provider contract를 검증한다.

- [x] **Step 3.1: 전체 신규 Codex CLI surface에 sentinel redaction regression을 추가한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_codex_provider.py -q -k "redaction or subprocess_env or unauthenticated"`
Expected: selected tests pass and captured stdout/stderr excludes `SENTINEL_SECRET` except explicit verifier labels.

- [x] **Step 3.2: AgentOS source가 API key/token storage path를 만들지 않았는지 확인한다.**

Run: `! rg -q "OPENAI_API_KEY|AGENTOS_LLM_API_KEY|ANTHROPIC_API_KEY|refresh_token|access_token" agentos tests && echo "PASS no-agentos-secret-storage"`
Expected: `PASS no-agentos-secret-storage`

- [x] **Step 3.3: opt-in real Codex status smoke를 문서화하고 실행 가능하게 한다.**

이 command는 `AGENTOS_CODEX_INTEGRATION=1`이 있을 때만 실행한다. CI/default test에서는 skip한다.

Run: `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli llm status --json --provider codex`
Expected: if Codex CLI is logged in, sanitized JSON reports `provider:"codex"`, `mode:"account-login"`, and no raw token/auth file/raw environment/raw stderr. If not logged in, sanitized JSON reports unauthenticated recovery text.

- [x] **Step 3.4: opt-in real Codex one-shot run smoke를 문서화하고 실행 가능하게 한다.**

Run: `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli run --json --once "Reply with OK." --provider codex`
Expected: if Codex CLI is logged in and entitled, JSONL includes `start`, at least one `message_delta`, and `done`; no raw token/auth file/raw environment/raw stderr. If unavailable, JSONL emits one sanitized `error` event and exits non-zero.

## Task 4: docs/project 정렬과 final verification

**파일:**
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`
- 수정: 이 active plan

**사용자에게 보이는 마일스톤:** 실제 Codex adapter 구현 경계, 사용법, 검증 증거가 후속 세션에서도 재현 가능하게 남는다.

- [x] **Step 4.1: docs/project에 Codex CLI delegation boundary를 반영한다.**

Run: `rg -q "Codex CLI delegation" .agentos/project/03-system-contract.md && rg -q "codex-account-login-adapter" .agentos/project/04-safety-risk-verification.md && echo "PASS codex-provider-docs-aligned"`
Expected: `PASS codex-provider-docs-aligned`

- [x] **Step 4.2: focused final verification을 실행한다.**

Run: `.venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py tests/test_codex_provider.py -q`
Expected: all selected tests pass.

- [x] **Step 4.3: lifecycle board와 Gate 2 evidence validity를 확인한다.**

Run: `.venv/bin/python .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && .venv/bin/python .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-18-agentos-codex-account-login-adapter.md`
Expected: lifecycle refresh exits 0 and review check reports PASS after Gate 2 artifacts are recorded.

## Gate 2 리뷰 증거

`reviewed: true`로 바꾸기 전에 다음 artifact가 모두 이 계획 경로·normalized plan hash·검토 시점·검토자 identity/provenance·독립 verdict·implementer/reviewer 분리를 기록해야 한다.

- `.agents/traces/reviews/2026-07-18-agentos-codex-account-login-adapter/plan-reviewer.json` — plan-reviewer PASS
- `.agents/traces/reviews/2026-07-18-agentos-codex-account-login-adapter/principle-auditor.json` — principle-auditor PASS/CLEAN
- `.agents/traces/reviews/2026-07-18-agentos-codex-account-login-adapter/usability-reviewer.json` — usability-reviewer PASS

세 artifact와 Gate 2 합의가 없는 경우 이 계획은 review pending이며 구현을 시작하지 않는다. 이 artifact의 작성 주체는 독립 `plan-reviewer`, `principle-auditor`, `usability-reviewer`이며, implementer는 구현 Task 산출물로 리뷰 증거를 사후 생성하거나 보정하지 않는다.

## 세션 중단 대비 체크포인트

- 현재 완료 범위: Codex CLI account-login adapter implementation and verification complete.
- 미완료 작업: 없음. Archive는 사용자 명시 요청 전까지 보류.
- 다음 세션 첫 작업: 사용자가 원하면 active plan archive 또는 VS Code/ACP bridge 후속 계획.
- 아직 안 한 검증: 없음 for planned default/focused checks. Real Codex status and one-shot smoke both ran with `AGENTOS_CODEX_INTEGRATION=1`.
- 관련 HISTORY checkpoint: root `HISTORY.md` is absent in this checkout; use this active plan and `.agents/traces/reviews/2026-07-18-agentos-codex-account-login-adapter/` for evidence.

## 리뷰 반영 이력

- 초안: completed LLM Core MVP, approved `0004` ADR, local Pi/Hermes/Codex reference analysis, and official Codex auth docs를 바탕으로 작성.
- Gate 2 first pass: plan-reviewer, principle-auditor, usability-reviewer all found plan-quality issues before implementation. 보정 내용: explicit dependency gate, testable user output contract, reviewer artifact ownership separation.
- Gate 2 re-review: plan-reviewer PASS, principle-auditor PASS/CLEAN, usability-reviewer PASS. `reviewed: true` set after `.venv/bin/python .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-18-agentos-codex-account-login-adapter.md` returned PASS.

## 구현 결과

구현 완료:

- `agentos/llm/providers/codex_cli.py` added `CodexCliProvider` using Codex CLI subprocess delegation.
- `agentos/llm/session.py` now supports `mock` and `codex` providers.
- `agentos/commands/llm.py` routes `status/login/logout --provider codex`.
- `agentos/commands/run.py` emits non-zero exit after provider error JSONL.
- `tests/test_codex_provider.py` covers fake Codex CLI discovery, env allowlist, status/login/logout, JSONL parsing, real Codex `item.completed` message shape, failure, and redaction.
- `.agentos/project/03-system-contract.md` and `.agentos/project/04-safety-risk-verification.md` record Codex CLI delegation boundaries and verification gates.

## 사용 방법

먼저 Codex CLI login 상태를 준비한다:

```bash
codex login
codex login status
```

AgentOS에서 상태를 확인한다:

```bash
.venv/bin/python -m agentos.cli llm status --json --provider codex
```

AgentOS에서 one-shot 대화를 실행한다:

```bash
.venv/bin/python -m agentos.cli run --json --once "Reply with OK." --provider codex
```

AgentOS는 Codex token, auth file content/path, raw stderr, raw environment를 출력하거나 저장하지 않는다.

## 완료 증거

- Gate 2: `.venv/bin/python .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-18-agentos-codex-account-login-adapter.md` -> `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`.
- Preflight: `PASS codex-account-login-approved`, `16 passed`, `PASS codex-cli-installed`.
- Focused Codex tests: `.venv/bin/python -m pytest tests/test_codex_provider.py -q` -> `13 passed`.
- Final focused suite: `.venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py tests/test_codex_provider.py -q` -> `29 passed`.
- Secret regression: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_codex_provider.py -q -k "redaction or subprocess_env or unauthenticated"` -> `3 passed, 10 deselected`.
- Secret storage scan: `! rg -q "OPENAI_API_KEY|AGENTOS_LLM_API_KEY|ANTHROPIC_API_KEY|refresh_token|access_token" agentos tests && echo "PASS no-agentos-secret-storage"` -> `PASS no-agentos-secret-storage`.
- Docs alignment: `rg -q "Codex CLI delegation" .agentos/project/03-system-contract.md && rg -q "codex-account-login-adapter" .agentos/project/04-safety-risk-verification.md && echo "PASS codex-provider-docs-aligned"` -> `PASS codex-provider-docs-aligned`.
- Harness integrity: sync-manifest check -> `PASS 하네스 무결성 확인 완료`.
- Real Codex status smoke: `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli llm status --json --provider codex` -> authenticated JSON status.
- Real Codex one-shot smoke: `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli run --json --once "Reply with OK." --provider codex` -> JSONL `start`, `message_delta` with `OK`, and `done`.

## 아카이브 결정

이 계획은 active에 남아 있으며, 사용자가 명시적으로 archive를 요청할 때에만 lifecycle 명령으로 이동한다.
