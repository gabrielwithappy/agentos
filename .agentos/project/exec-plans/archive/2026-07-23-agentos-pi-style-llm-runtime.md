# AgentOS pi-style LLM runtime 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-23<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-23T13:00:00Z<br>
> implementation_completed_at: 2026-07-23T13:14:43Z<br>
> implementation_duration: 14m 43s<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `pi` 스타일의 LLM runtime 핵심만 먼저 도입해, AgentOS가 provider registry와 auth store 기반 구조를 갖추면서도 현재 `codex` 사용 경로는 안전한 external-CLI compatibility path로 유지한다.

**사용자 결과 요약:** 사용자는 `agentos llm status/login/logout`와 `agentos run --json --once`를 기존처럼 계속 사용할 수 있고, 구현자는 이후 native OAuth/transport를 얹을 수 있는 runtime 뼈대를 얻게 된다. 이번 범위에서는 browser login, device-code login, AgentOS-owned live token refresh, native WebSocket/SSE transport는 구현하지 않는다.

**의존성 분석:**
- 외부 의존성: root docs/ADR/supporting note 업데이트, 기존 Codex CLI compatibility path, local filesystem auth store file.
- live network/OAuth: 없음. 이번 범위는 real OAuth endpoint, browser callback, device-code polling, native Responses transport를 직접 호출하지 않는다.
- 보안 의존성: raw token, raw key, raw environment, raw provider stderr는 UI/JSONL/stdout/stderr/log/test artifact에 노출하지 않는다.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, Gate 2 review artifacts.
- Durable Result Surface: `agentos/llm/`, `agentos/commands/llm.py`, `agentos/commands/run.py`, `tests/`, `docs/cli-reference.md`, root project docs, `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`, `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- documentation-only exception: 없음. 코드와 문서가 함께 바뀐다.

**진행 상태:** core foundation 범위로 축소한 revision을 기준으로 구현과 검증을 완료했다. Codex는 external-CLI compatibility path를 canonical path로 유지한다.

**아키텍처:** `pi`의 shape 중 provider registry, auth type/store 분리, provider-independent session resolution만 먼저 가져온다. 실사용 `codex` provider는 계속 외부 Codex CLI delegation을 사용하고, 새 auth store는 mock/future provider foundation으로 추가한다.

**기술 스택:** Python 3.12+, Typer, Textual, pytest, local JSON file store, existing sanitized JSONL event contract.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 완료 |
| 완료됨 | docs/project 정렬, provider registry, auth store foundation, CLI compatibility 유지, focused/public verification, manifest check |
| 현재 위치 | active completed plan closeout 작성 완료 |
| 다음 단계 | 사용자 요청 시 archive 또는 후속 native OAuth/transport 계획으로 진행 |
| 완료 신호 | focused suite 38 PASS, public suite 125 PASS, manifest check PASS, docs scope checks PASS |

## 세션 인계 체크포인트

- 현재 완료 범위: core foundation 구현과 검증 완료.
- 미완료 작업: 없음. 후속 native OAuth/transport는 별도 계획 필요.
- 다음 세션 첫 작업: 사용자가 원하면 이 active completed plan을 archive하거나, 후속 native path 계획을 새로 작성.
- 아직 안 한 검증: 없음. 이번 범위의 focused/public verification은 완료.
- 관련 HISTORY checkpoint: 2026-07-23 core foundation closeout checkpoint 예정.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 문서 경계 정렬 | 사용자는 이번 작업이 “runtime core foundation만 구현하고, 실사용 Codex는 계속 Codex CLI 경로를 쓴다”는 사실을 문서에서 바로 확인할 수 있다 | root docs, ADR `0004`, supporting note | `PASS docs-llm-core-scope-aligned` |
| 1. runtime registry 도입 | `mock`와 `codex`가 ad-hoc `if` 분기 대신 registry 기반으로 resolve된다 | `agentos/llm/registry.py`, `agentos/llm/session.py`, providers, tests | focused registry tests PASS |
| 2. auth store foundation | 구현자는 provider-independent auth type/file store를 재사용할 수 있고, 사용자 표면에는 secret leak 없이 유지된다 | `agentos/llm/auth/*`, tests | auth store tests PASS |
| 3. CLI contract 유지 | 사용자는 기존 `status/login/logout/run --json` 동작을 유지한 채 내부 runtime core가 교체된 결과를 얻는다 | `agentos/commands/llm.py`, `agentos/commands/run.py`, tests | CLI/provider tests PASS |
| 4. 문서와 회귀 검증 | 사용자는 지금 가능한 것과 아직 deferred인 범위를 문서로 구분해 이해한다 | docs/project, `docs/cli-reference.md`, tests | focused suite + public suite PASS |

## 사용자 여정

1. 상태 확인: 사용자는 `agentos llm status --provider codex --json` 또는 `agentos llm status --provider mock --json`으로 현재 provider 상태를 확인한다.
2. 로그인: 이번 범위에서 `codex`는 계속 external CLI compatibility path다. 사용자는 `agentos llm login --provider codex`를 실행하면 AgentOS가 Codex CLI login 흐름을 위임 호출한다. 브라우저/device-code 선택은 AgentOS가 새로 구현하지 않고 Codex CLI가 소유한다.
3. 실행: 사용자는 `agentos run --json --once "..." --provider codex|mock`로 동일한 sanitized JSONL event stream을 받는다.
4. 로그아웃: 사용자는 `agentos llm logout --provider codex`로 Codex CLI logout을 호출한다. unauthenticated 또는 missing CLI 상태의 다음 안전 행동은 `agentos llm login --provider codex` 또는 Codex CLI 설치다.

## 리뷰 반영 이력

- 2026-07-23 `usability-reviewer` FAIL 반영:
  - login → status → run → logout 1회 사용자 여정을 한 섹션으로 모았다.
  - browser/device-code 기본 선택 규칙 혼란을 제거하기 위해, 이번 범위에서 그 선택은 Codex CLI가 소유한다고 고정했다.
  - unauthenticated/missing CLI 상태의 다음 안전 행동을 명시했다.
- 2026-07-23 `plan-reviewer` FAIL 반영:
  - 템플릿 필수 섹션(`리뷰 반영 이력`, `구현 결과`)을 복원했다.
  - live OAuth/network gate를 제거하고 local-only core scope로 단순화했다.
  - 보안 negative check와 supporting note refresh를 별도 Task/검증에 추가했다.
- 2026-07-23 `principle-auditor` REVISE 반영:
  - Codex native transport/OAuth를 이번 범위에서 제외하고 `codex_cli` compatibility path를 canonical path로 고정했다.
  - root docs, ADR, supporting note의 구 계약 supersede 검증을 Task 0에 추가했다.
- 2026-07-23 Gate 2 재검토 PASS:
  - `plan-reviewer` PASS, `principle-auditor` PASS/CLEAN, `usability-reviewer` PASS artifact를 `.agents/traces/reviews/2026-07-23-agentos-pi-style-llm-runtime/`에 기록했다.

## 파일 구조

- 생성: `agentos/llm/registry.py` — provider 등록/조회, duplicate validation, canonical provider list.
- 생성: `agentos/llm/auth/types.py` — credential metadata, auth record, sanitized summary dataclasses.
- 생성: `agentos/llm/auth/store.py` — provider별 JSON file store, 0600 permission, serialized modify/delete.
- 수정: `agentos/llm/session.py` — registry 기반 resolution으로 전환.
- 수정: `agentos/llm/providers/mock.py` — registry-compatible provider.
- 수정: `agentos/llm/providers/codex_cli.py` — canonical external-CLI compatibility provider로 유지, provider protocol에 맞춤.
- 수정: `agentos/commands/llm.py` — registry 경유 status/login/logout.
- 수정: `agentos/commands/run.py` — registry/session consumer 유지.
- 생성: `tests/test_auth_store.py` — auth store focused tests.
- 수정: `tests/test_llm_core.py`, `tests/test_codex_provider.py`, `tests/test_cli_contract.py` — registry/auth store/compatibility contract tests.
- 수정: `.agentos/project/{01,02,03,04,06}-*.md`, `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`, `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`, `docs/cli-reference.md`

## 구현 작업

### Task 0: root docs / ADR / supporting note를 core scope에 맞게 정렬

**파일:**
- 수정: `.agentos/project/01-project-charter.md`
- 수정: `.agentos/project/02-product-scope-and-requirements.md`
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`
- 수정: `.agentos/project/06-decisions-change-log.md`
- 수정: `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- 수정: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`

**사용자에게 보이는 마일스톤:** 문서가 “이번 구현은 core foundation만, Codex 실사용은 external CLI compatibility path 유지”라는 현재 진실을 일관되게 보여준다.

- [x] **Step 1: charter / requirements / contract / risk / decisions에 core foundation scope와 deferred native OAuth/transport를 명시한다.**

Run: `rg -q "core foundation" .agentos/project/01-project-charter.md && rg -q "REQ-LLM-004" .agentos/project/02-product-scope-and-requirements.md && rg -q "external CLI compatibility path" .agentos/project/03-system-contract.md && rg -q "native OAuth/transport remains deferred" .agentos/project/04-safety-risk-verification.md && rg -q "2026-07-23" .agentos/project/06-decisions-change-log.md && echo "PASS docs-llm-core-scope-aligned"`
Expected: `PASS docs-llm-core-scope-aligned`

- [x] **Step 2: 기존 delegation-only 또는 no-storage 금지 문구가 이번 core foundation scope와 충돌하지 않도록 supersede 문구로 갱신한다.**

Run: `! rg -q "no AgentOS token parsing or storage is allowed" .agentos/project/03-system-contract.md && ! rg -q "AgentOS only delegates CLI commands" .agentos/project/04-safety-risk-verification.md && rg -q "future native OAuth/transport requires a separate reviewed plan" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS old-boundary-superseded"`
Expected: `PASS old-boundary-superseded`

- [x] **Step 3: supporting implementation note를 현재 credential boundary와 runtime foundation 상태에 맞게 refresh한다.**

Run: `rg -q "provider registry" .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md && rg -q "auth store foundation" .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md && echo "PASS llm-supporting-note-refreshed"`
Expected: `PASS llm-supporting-note-refreshed`

### Task 1: provider registry와 provider protocol 도입

**파일:**
- 생성: `agentos/llm/registry.py`
- 수정: `agentos/llm/session.py`
- 수정: `agentos/llm/providers/mock.py`
- 수정: `agentos/llm/providers/codex_cli.py`
- 수정: `tests/test_llm_core.py`

**사용자에게 보이는 마일스톤:** 사용자 명령은 그대로지만 내부에서 provider resolution이 registry 기반으로 일관화된다.

- [x] **Step 1: provider registry, registration helper, duplicate/unknown provider 검증을 추가한다.**

Run: `uv run pytest tests/test_llm_core.py -k "registry or provider_resolution or unsupported_provider" -q`
Expected: pytest PASS

- [x] **Step 2: `mock`와 `codex` provider를 registry에 등록하고 session lookup을 교체한다.**

Run: `uv run pytest tests/test_llm_core.py tests/test_codex_provider.py -k "mock or codex or unsupported_provider" -q`
Expected: pytest PASS

### Task 2: auth type / file store foundation 추가

**파일:**
- 생성: `agentos/llm/auth/types.py`
- 생성: `agentos/llm/auth/store.py`
- 생성: `tests/test_auth_store.py`

**사용자에게 보이는 마일스톤:** 새 auth foundation이 생기지만, 사용자 출력에서는 raw secret이 여전히 노출되지 않는다.

- [x] **Step 1: provider-independent auth record, sanitized metadata summary 타입을 정의한다.**

Run: `uv run pytest tests/test_auth_store.py -k "types or metadata" -q`
Expected: pytest PASS

- [x] **Step 2: provider별 JSON file store와 0600 permission, serialized write/delete를 구현한다.**

Run: `uv run pytest tests/test_auth_store.py -k "file_store or permissions or modify_serialized or delete" -q`
Expected: pytest PASS

- [x] **Step 3: secret/env redaction negative check를 auth store 경로에 추가한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_auth_store.py -k "secret or redact" -q`
Expected: pytest PASS and no raw sentinel in pytest captures

### Task 3: CLI compatibility path를 registry 경유로 유지

**파일:**
- 수정: `agentos/commands/llm.py`
- 수정: `agentos/commands/run.py`
- 수정: `tests/test_codex_provider.py`
- 수정: `tests/test_cli_contract.py`

**사용자에게 보이는 마일스톤:** 사용자는 기존 `codex`/`mock` 명령 계약을 유지하고, `codex`는 여전히 Codex CLI compatibility path를 쓴다.

- [x] **Step 1: `llm status/login/logout`가 registry를 통해 provider를 resolve하도록 바꾼다.**

Run: `uv run pytest tests/test_llm_core.py tests/test_codex_provider.py -k "status or login or logout" -q`
Expected: pytest PASS

- [x] **Step 2: `run --json --once`가 registry/session 경유 event stream을 계속 소비하도록 유지한다.**

Run: `uv run pytest tests/test_cli_contract.py tests/test_codex_provider.py -k "run_json or jsonl or codex" -q`
Expected: pytest PASS

- [x] **Step 3: compatibility path의 secret/env/provider-stderr negative check를 고정한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_codex_provider.py tests/test_cli_contract.py -k "redaction or env or stderr or secret" -q`
Expected: pytest PASS and no raw sentinel/raw provider stderr/raw env dump in captures

### Task 4: 문서와 전체 회귀 검증

**파일:**
- 수정: `docs/cli-reference.md`
- 수정: `HISTORY.md`

**사용자에게 보이는 마일스톤:** 사용자는 지금 가능한 경로와 deferred 범위를 CLI 문서에서 바로 구분할 수 있다.

- [x] **Step 1: CLI reference에 core foundation scope와 current Codex compatibility path를 문서화한다.**

Run: `rg -q "external CLI compatibility path" docs/cli-reference.md && rg -q "native OAuth/transport is deferred" docs/cli-reference.md && echo "PASS cli-reference-core-scope"`
Expected: `PASS cli-reference-core-scope`

- [x] **Step 2: focused suite와 public suite를 실행한다.**

Run: `uv run pytest tests/test_auth_store.py tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py -q`
Expected: pytest PASS

Run: `uv run pytest tests/ -q`
Expected: pytest PASS

- [x] **Step 3: manifest check와 closeout checkpoint를 남긴다.**

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: PASS

## 구현 결과

- `agentos/llm/registry.py`를 추가해 provider resolution을 registry 기반으로 통일했다.
- `agentos/llm/auth/`에 provider-independent auth record/file store foundation을 추가했다.
- `agentos/llm/session.py`는 registry를 통해 `mock`/`codex`를 resolve하도록 바뀌었고, `codex`는 external CLI compatibility path를 그대로 유지한다.
- root docs, ADR, supporting implementation note, CLI reference를 현재 core scope에 맞게 정렬했다.

## 사용 방법

- 상태 확인: `agentos llm status --provider mock --json` 또는 `agentos llm status --provider codex --json`
- 로그인: `agentos llm login --provider codex`
- 단발 실행: `agentos run --json --once "hello" --provider codex`
- 현재 범위 설명: `codex`는 여전히 external CLI compatibility path이며, native OAuth/transport는 아직 구현하지 않았다.

## 완료 증거

- `PASS docs-llm-core-scope-aligned`
- `PASS old-boundary-superseded`
- `PASS llm-supporting-note-refreshed`
- `PASS cli-reference-core-scope`
- `uv run pytest tests/test_auth_store.py tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py -q` → `38 passed`
- `uv run pytest tests/ -q` → `125 passed`
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → `PASS`

## 아카이브 결정

이 계획은 아직 active에 남아 있으며, 사용자가 명시적으로 archive를 요청하면 `plan_lifecycle.py archive <plan-path> --status 완료`로 이동한다.
