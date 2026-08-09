# AgentOS LLM Core MVP 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-18<br>
> reviewed: true<br>
> usability_review_required: true (새 CLI 명령과 JSONL 출력, 오류/상태 문구를 추가하므로)<br>
> implementation_started_at: 2026-07-18T22:55:22+09:00<br>
> implementation_completed_at: 2026-07-18T22:59:49+09:00<br>
> implementation_duration: 4m 27s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** provider credential strategy approval 없이 검증 가능한 mock-only 최소 LLM runtime surface를 AgentOS에 추가한다.

**사용자 결과:** 사용자는 실제 Codex 계정 로그인 전에도 `agentos llm status`, mock login/logout, and `agentos run --json`으로 LLM 연결 계약과 secret redaction을 테스트할 수 있다.

**진행 상태:** mock-only LLM runtime 구현과 검증 완료. 계획은 active에 남아 있으며 archive는 사용자 요청 시 수행한다.

**아키텍처:** Pi docs의 단순 연결 구조를 Python/Typer에 맞게 축소 적용한다. CLI/VS Code 같은 사용자 surface는 provider-independent JSONL event만 보고, provider adapter는 `agentos/llm/` 아래에서 mock부터 시작한다. 실제 Codex OAuth/account-login, credential persistence, API key adapter, and billing-affecting provider calls는 이 계획에 포함하지 않는다. Mock provider status는 real credential, authentication, persistence, provider session, network, or billing을 절대 암시하지 않는다.

**기술 스택:** Python 3.11+, Typer, Rich, pytest, dataclasses/typing, JSONL stdout events.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | adoption analysis handoff, Pi docs evidence, pending ADR, Intent Sheet, Gate 2 review PASS, Task 0 preflight, Task 1 LLM core, Task 2 CLI commands, Task 3 security/docs alignment |
| 현재 위치 | closeout complete; active plan remains until explicit archive request |
| 다음 단계 | optional archive on user request |
| 완료 신호 | mock provider 기반 CLI/JSONL/redaction tests가 PASS하고 실제 provider approval 없이도 LLM runtime contract가 검증됨 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 실제 provider 계정 없이도 LLM 연결 흐름을 테스트할 수 있는 AgentOS CLI 표면 |
| 누구를 위한 것인가? | 프로젝트 오너, CLI/VS Code 구현자, 보안 리뷰어 |
| 일상 사용에서 무엇이 달라지는가? | `agentos llm status --json --provider mock`와 `agentos run --json --once ...`로 mock LLM 이벤트를 확인할 수 있다. |
| 무엇은 바뀌지 않는가? | 실제 Codex OAuth/account-login, API key 저장, billing, OS credential store, VS Code extension 구현은 아직 바뀌지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. LLM 계약 고정 | AgentOS가 provider-independent message/event/usage/error 타입을 갖는다 | `agentos/llm/types.py`, `agentos/llm/session.py` | `Run:` `pytest tests/test_llm_core.py -q`<br>`Expected:` selected tests pass |
| 2. Mock provider | 실제 credential 없이 mock login/status/logout과 stream event가 동작한다 | `agentos/llm/providers/mock.py`, `agentos/commands/llm.py` | `Run:` `python -m agentos.cli llm status --json --provider mock`<br>`Expected:` JSON contains `"provider":"mock"` |
| 3. JSONL run bridge | `agentos run --json --once`가 sanitized JSONL event를 출력한다 | `agentos/commands/run.py`, `agentos/cli.py` | `Run:` `python -m agentos.cli run --json --once "hello"`<br>`Expected:` JSONL includes `message_delta` and `done` |
| 4. Secret regression | sentinel secret이 stdout/stderr/log/test artifact에 노출되지 않는다 | `agentos/llm/redaction.py`, `tests/test_llm_core.py` | `Run:` `AGENTOS_TEST_SECRET=SENTINEL_SECRET pytest tests/test_llm_core.py -q`<br>`Expected:` selected tests pass and captured output excludes sentinel |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/traces/reviews/2026-07-18-agentos-llm-core-mvp/`, `.agentos/project/exec-plans/README.md`
- durable result surface: `agentos/llm/`, `agentos/commands/llm.py`, `agentos/commands/run.py`, `agentos/cli.py`, `tests/test_llm_core.py`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`
- documentation-only exception: 없음. 이 계획은 code and tests implementation plan이다.

## 의도 근거

- Intent Sheet: `.agentos/project/exec-plans/archive/reference/intent/intent-20260718-agentos-llm-core-mvp.md`
- Adoption analysis: `.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md`
- Pi evidence: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
- Pending ADR: `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`

## 범위 및 비범위

포함:
- provider-independent LLM request/event/usage/error types.
- mock provider with deterministic status/login/logout behavior.
- sanitized JSONL output for single-turn `agentos run --json --once`.
- redaction layer blocking raw token, raw key, raw environment, raw provider stderr, and synthetic sentinel leaks.
- focused pytest coverage.
- unsupported real provider behavior: non-zero sanitized error, no network call, no credential lookup, and recovery text directing users to `--provider mock` or provider approval.
- JSONL failure contract: failure paths emit exactly one stdout JSONL `error` object and exit non-zero. The object includes `type:"error"`, requested `provider`, `mode:"unsupported"` or `mode:"mock"`, `error.code`, sanitized `error.message`, and `recovery`. Stderr may contain only sanitized Typer/CLI diagnostics and must not contain raw secret, raw provider stderr, or raw environment.

제외:
- real Codex OAuth/account-login.
- provider account creation, OAuth client registration, refresh/revocation, or token storage.
- API key input/import/storage or API-key adapter implementation.
- OS credential store persistence.
- VS Code extension source implementation.
- broad provider registry, model catalog, gateway, daemon, marketplace, or automatic failover.
- editing ADR approval fields such as `approval_status`, `approved_date`, `approval_provenance`, `owner`, entitlement, billing, grant/scope/redirect policy, or allowed model policy.

## 의존성 분석

- 외부 의존성: 없음.
- 스캔 기준: 기술 스택, 파일 구조, planned `Run:` commands, runtime assumptions.
- 로컬 baseline: Python/Typer/pytest는 existing project dependency set이다.
- 실제 provider, network, credential, OAuth, and billing calls are out of scope and must not be used.

## File Structure

- 생성: `agentos/llm/__init__.py` - LLM package exports.
- 생성: `agentos/llm/types.py` - provider-independent messages, events, usage, errors, and provider status types.
- 생성: `agentos/llm/redaction.py` - secret/sentinel redaction helpers.
- 생성: `agentos/llm/session.py` - provider selection and simple stream orchestration.
- 생성: `agentos/llm/providers/__init__.py` - provider package exports.
- 생성: `agentos/llm/providers/mock.py` - deterministic mock provider.
- 생성: `agentos/commands/llm.py` - `agentos llm` Typer commands.
- 수정: `agentos/cli.py` - register `llm` subcommands.
- 수정: `agentos/commands/run.py` - add `--json --once` path using mock session.
- 생성: `tests/test_llm_core.py` - focused LLM core and CLI tests.
- 수정: `tests/test_cli.py` - preserve existing run behavior while adding CLI registration expectations if needed.
- 수정: `.agentos/project/03-system-contract.md` - record implemented mock runtime contract.
- 수정: `.agentos/project/04-safety-risk-verification.md` - record fresh verification evidence and redaction gate.
- 수정: `.agentos/project/02-product-scope-and-requirements.md` - record mock-only exception requirement if not already present.

## Task 0: 구현 전 preflight

**파일:**
- 수정: 없음

**사용자에게 보이는 마일스톤:** 현재 checkout에서 mock-only LLM core 구현을 시작해도 외부 provider 호출이 필요 없음을 확인한다.

- [x] **Step 0.1: 현재 CLI와 test baseline을 확인한다.**

Run: `pytest tests/test_cli.py -q`
Expected: tests pass.

Fresh evidence: plain `pytest` used the system Python and failed before collection because `typer` was unavailable there. `.venv/bin/python -m pytest tests/test_cli.py -q` used the project dependency environment and returned `8 passed`.

- [x] **Step 0.2: provider credential/API key 경로가 아직 없음을 확인한다.**

Run: `! rg -q "AGENTOS_LLM_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|refresh_token|access_token" agentos && echo "PASS no-provider-secret-path"`
Expected: `PASS no-provider-secret-path`

Fresh evidence: command returned `PASS no-provider-secret-path`.

## Task 1: provider-independent LLM core 추가

**파일:**
- 생성: `agentos/llm/__init__.py`
- 생성: `agentos/llm/types.py`
- 생성: `agentos/llm/redaction.py`
- 생성: `agentos/llm/session.py`
- 생성: `agentos/llm/providers/__init__.py`
- 생성: `agentos/llm/providers/mock.py`
- 생성: `tests/test_llm_core.py`

**사용자에게 보이는 마일스톤:** AgentOS가 실제 provider 없이도 LLM message/event contract를 테스트할 수 있다.

- [x] **Step 1.1: typed message/event/status 계약을 만든다.**

Run: `pytest tests/test_llm_core.py -q`
Expected: selected tests pass.

Fresh evidence: `.venv/bin/python -m pytest tests/test_llm_core.py -q` returned `8 passed`.

- [x] **Step 1.2: mock provider가 deterministic stream events를 반환하게 한다.**

Run: `pytest tests/test_llm_core.py -q -k "mock_provider or stream_events"`
Expected: selected tests pass.

Fresh evidence: `.venv/bin/python -m pytest tests/test_llm_core.py -q -k "mock_provider or stream_events"` returned `3 passed, 5 deselected`.

- [x] **Step 1.3: redaction layer가 sentinel and raw secret labels를 차단하게 한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET pytest tests/test_llm_core.py -q -k "redaction"`
Expected: selected tests pass and captured output excludes `SENTINEL_SECRET`.

Fresh evidence: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_llm_core.py -q -k "redaction"` returned `2 passed, 6 deselected`.

## Task 2: CLI 명령 연결

**파일:**
- 생성: `agentos/commands/llm.py`
- 수정: `agentos/cli.py`
- 수정: `agentos/commands/run.py`
- 수정: `tests/test_cli.py`
- 수정: `tests/test_llm_core.py`

**사용자에게 보이는 마일스톤:** 사용자는 mock provider 상태와 single-turn JSONL run을 CLI에서 확인할 수 있다.

- [x] **Step 2.1: `agentos llm status --json --provider mock` 명령을 추가한다.**

Run: `python -m agentos.cli llm status --json --provider mock`
Expected: stdout JSON contains `"provider":"mock"`, `"mode":"mock"`, `"credential_present":false`, `"authenticated":false`, and `"persistent_credential":false`.

Fresh evidence: `.venv/bin/python -m agentos.cli llm status --json --provider mock` returned JSON with those fields and values.

- [x] **Step 2.2: `agentos llm login/logout --provider mock` 명령을 mock-only로 추가한다.**

Run: `python -m agentos.cli llm login --provider mock --json && python -m agentos.cli llm logout --provider mock --json`
Expected: both commands return sanitized JSON with `"provider":"mock"`, `"mode":"mock"`, `"authenticated":false`, `"persistent_credential":false`, and no raw secret values; message states no real account, token, provider session, or persistent credential was changed.

Fresh evidence: `.venv/bin/python -m agentos.cli llm login --provider mock --json && .venv/bin/python -m agentos.cli llm logout --provider mock --json` returned sanitized mock JSON for both actions.

- [x] **Step 2.3: `agentos run --json --once`가 mock LLM event를 출력하게 한다.**

Run: `python -m agentos.cli run --json --once "hello"`
Expected: JSONL contains one JSON object per line in deterministic order: `start`, `message_delta`, and `done`. Each success event includes `type`, `provider:"mock"`, `mode:"mock"`, and sanitized text or usage fields. Unsupported providers emit one stdout JSONL `error` object with `type:"error"`, requested `provider`, `mode:"unsupported"`, `error.code`, sanitized `error.message`, and `recovery`; they return non-zero without network or credential lookup.

Fresh evidence: `.venv/bin/python -m agentos.cli run --json --once "hello"` returned JSONL event types `start`, `message_delta`, and `done`; `.venv/bin/python -m agentos.cli run --json --once "hello" --provider codex` returned one `error` JSONL object and exit code `1`.

## Task 3: 보안 회귀와 docs/project 정렬

**파일:**
- 수정: `.agentos/project/02-product-scope-and-requirements.md`
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`
- 수정: `tests/test_llm_core.py`

**사용자에게 보이는 마일스톤:** mock LLM runtime은 secret을 출력하지 않고, 실제 provider 구현은 계속 승인 뒤로 분리되어 있음을 확인할 수 있다.

- [x] **Step 3.1: synthetic sentinel이 CLI output과 JSONL event에 노출되지 않게 검증한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET python -m agentos.cli run --json --once "hello" > /tmp/agentos-llm-jsonl.out 2> /tmp/agentos-llm-jsonl.err && ! rg -q "SENTINEL_SECRET" /tmp/agentos-llm-jsonl.out /tmp/agentos-llm-jsonl.err && echo "PASS secret-redaction-jsonl"`
Expected: `PASS secret-redaction-jsonl`

Fresh evidence: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m agentos.cli run --json --once "hello" > /tmp/agentos-llm-jsonl.out 2> /tmp/agentos-llm-jsonl.err && ! rg -q "SENTINEL_SECRET" /tmp/agentos-llm-jsonl.out /tmp/agentos-llm-jsonl.err && echo "PASS secret-redaction-jsonl"` returned `PASS secret-redaction-jsonl`.

- [x] **Step 3.1b: synthetic sentinel이 전체 신규 CLI surface와 unsupported-provider failure path에 노출되지 않게 검증한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET pytest tests/test_llm_core.py -q -k "secret_redaction_cli_surface or unsupported_provider"`
Expected: selected tests pass and captured stdout/stderr excludes `SENTINEL_SECRET` except explicit verifier labels.

Fresh evidence: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_llm_core.py -q -k "secret_redaction_cli_surface or unsupported_provider"` returned `2 passed, 6 deselected`.

- [x] **Step 3.2: docs/project에 mock-only runtime과 provider approval boundary를 반영한다.**

Run: `rg -q "Mock provider LLM core exception" .agentos/project/03-system-contract.md && rg -q "secret-redaction-jsonl" .agentos/project/04-safety-risk-verification.md && rg -q "REQ-LLM-003" .agentos/project/02-product-scope-and-requirements.md && rg -q "^approval_status: needs_context$" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS llm-core-docs-aligned"`
Expected: `PASS llm-core-docs-aligned`

Fresh evidence: command returned `PASS llm-core-docs-aligned`.

## 검증 및 수용 기준

- [x] `.venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py -q` passes.
- [x] `.venv/bin/python -m agentos.cli llm status --json --provider mock` returns sanitized JSON.
- [x] `.venv/bin/python -m agentos.cli run --json --once "hello"` returns valid JSONL events.
- [x] Mock status/login/logout never claims real credentials, authentication, persistent credential storage, provider session, network, or billing.
- [x] Unsupported providers return non-zero sanitized errors without network or credential lookup.
- [x] JSONL failure paths emit one stdout `error` object with `type`, `provider`, `mode`, `error.code`, sanitized `error.message`, and `recovery`.
- [x] Synthetic sentinel is absent from CLI stdout/stderr, JSONL event, and pytest captured output except explicit verifier labels.
- [x] No real provider, OAuth, API key, network, billing, or persistent credential store path is introduced.

## 세션 재개 체크포인트

- 현재 완료 범위: Gate 2 review, mock-only LLM core, mock provider CLI commands, JSONL run bridge, secret redaction tests, unsupported-provider failure path, docs/project closeout.
- 미완료 작업: 없음. Archive는 사용자가 명시적으로 요청할 때만 수행한다.
- 다음 세션 첫 작업: 사용자가 요청하면 archive lifecycle command를 실행하거나, 별도 승인 계획으로 real provider account-login work를 시작한다.
- 아직 안 한 검증: real provider/OAuth/account-login/API key/persistent credential/billing verification은 이 계획 범위가 아니므로 실행하지 않았다.
- 관련 review evidence: `.agents/traces/reviews/2026-07-18-agentos-llm-core-mvp/`.

## 리뷰 반영 이력

- 초안: `2026-07-18-llm-auth-api-adoption-analysis.md`, `0004-agentos-llm-credential-strategy.md`, and Pi docs evidence를 바탕으로 작성.
- Gate 2 초회: plan-reviewer PASS, principle-auditor FAIL, usability-reviewer FAIL. Evidence: `.agents/traces/reviews/2026-07-18-agentos-llm-core-mvp/`.
- Gate 2 보정: mock-only exception, ADR approval field protection, mock UX contract, JSONL failure schema, and full CLI secret regression scope를 추가.
- Gate 2 최종: principle-auditor re-review PASS and usability-reviewer re-review-2 PASS. `reviewed: true`로 전이.

## 구현 결과

AgentOS에 mock-only LLM runtime surface를 추가했다.

- `agentos/llm/` provider-independent event/status types, redaction helper, session selection, and deterministic mock provider.
- `agentos llm status/login/logout --provider mock --json` commands.
- `agentos run --json --once "..."` JSONL bridge with deterministic `start`, `message_delta`, and `done` events.
- unsupported provider failure path with one sanitized stdout JSONL `error` object and non-zero exit.
- focused tests for mock contracts, JSONL events, unsupported provider behavior, and sentinel redaction.
- docs/project alignment for `REQ-LLM-003`, mock-only exception, and secret verification matrix.

## 사용 방법

```bash
.venv/bin/python -m agentos.cli llm status --json --provider mock
.venv/bin/python -m agentos.cli llm login --provider mock --json
.venv/bin/python -m agentos.cli llm logout --provider mock --json
.venv/bin/python -m agentos.cli run --json --once "hello"
```

실제 provider/OAuth/account-login/API key/persistent credential store/billing path는 구현하지 않았다. 현재 mock status는 `credential_present:false`, `authenticated:false`, and `persistent_credential:false`를 반환한다.

## 완료 증거

- `.venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py -q` -> `16 passed`.
- `.venv/bin/python -m agentos.cli llm status --json --provider mock` -> sanitized mock JSON with `credential_present:false`, `authenticated:false`, `persistent_credential:false`.
- `.venv/bin/python -m agentos.cli run --json --once "hello"` -> JSONL `start`, `message_delta`, `done`.
- `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m agentos.cli run --json --once "hello" > /tmp/agentos-llm-jsonl.out 2> /tmp/agentos-llm-jsonl.err && ! rg -q "SENTINEL_SECRET" /tmp/agentos-llm-jsonl.out /tmp/agentos-llm-jsonl.err && echo "PASS secret-redaction-jsonl"` -> `PASS secret-redaction-jsonl`.
- `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_llm_core.py -q -k "secret_redaction_cli_surface or unsupported_provider"` -> `2 passed, 6 deselected`.
- `! rg -q "AGENTOS_LLM_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|refresh_token|access_token" agentos && echo "PASS no-provider-secret-path"` -> `PASS no-provider-secret-path`.
- `rg -q "Mock provider LLM core exception" .agentos/project/03-system-contract.md && rg -q "secret-redaction-jsonl" .agentos/project/04-safety-risk-verification.md && rg -q "REQ-LLM-003" .agentos/project/02-product-scope-and-requirements.md && rg -q "^approval_status: needs_context$" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS llm-core-docs-aligned"` -> `PASS llm-core-docs-aligned`.

## 아카이브 결정

이 계획은 active에 남아 있으며, 사용자가 명시적으로 archive를 요청할 때에만 lifecycle 명령으로 이동한다.
