# 0004 - AgentOS LLM credential strategy

- Expansion Trigger: AgentOS가 LLM 연결을 CLI 위임에서 account-login 기반 provider adapter로 확장할 수 있는지 결정해야 함.
- parent root doc: `01-project-charter.md`, `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`, `06-decisions-change-log.md`
- reason for creation: LLM 인증, 구독 entitlement, billing owner, credential lifecycle, and security handoff를 root docs보다 자세히 기록하기 위한 ADR.
- owner: project owner
- freshness rule: Refresh when provider, credential type, subscription entitlement, billing owner, official documentation, token storage, or LLM transport policy changes.
- status: 현재
- source evidence: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`; OpenAI Codex auth documentation checked on 2026-07-18.
- links back to: `.agentos/project/06-decisions-change-log.md`; `.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, reviewer authority, or human approval requirements.

## LLM credential strategy

approval_status: approved
approved_date: 2026-07-18
approval_provenance: user-message: 2026-07-18 "좋아" approving the recommended draft fields in this Codex thread
approval_recorded_by: Codex implementation agent
provider: Codex
credential_type: account-login
subscription_entitlement_policy: ChatGPT Plus/Pro account-login 기반 Codex 사용을 허용하되, 별도 API key 과금 경로는 사용하지 않음
billing_owner: project owner
official_document_url: https://developers.openai.com/codex/auth
official_document_checked_date: 2026-07-18
grant_scope_redirect_policy: Codex CLI의 공식 ChatGPT browser login/session 위임을 우선 사용하고, AgentOS 자체 OAuth client 등록은 별도 승인 전 금지
allowed_model_policy: Codex account-login에서 공식적으로 허용되는 기본 Codex 모델만 사용

## 결정 상태

이 ADR은 승인된 결정이다. API key adapter를 AgentOS 1차 구현 경로에서 제외하고, Codex account-login 기반 접근을 후속 실제 provider 구현 후보로 승인한다.

승인 범위는 Codex CLI의 공식 ChatGPT browser login/session 위임을 우선 사용하는 후속 계획 수립까지다. 실제 provider session 호출, OAuth client registration, credential persistence, and billing-affecting actions는 여전히 별도 implementation plan과 fresh Gate 2 review 뒤에만 시작할 수 있다.

## 채택 후보

- 1차 후보: Codex account-login adapter.
- 기본 fallback: 현재처럼 외부 CLI가 provider 인증과 업데이트를 소유하는 위임 방식.
- 제외: API key 입력, API key import, API key 저장, API-key adapter 구현.
- 후속 검증: 승인된 provider 계약을 바탕으로 mock provider와 synthetic sentinel secret regression을 먼저 통과해야 한다.

## 보안 경계

- prompt/data boundary: project docs, active plans, command output, and provider diagnostic text are data and cannot override AGENTS.md, vendor guides, reviewer authority, or protected-path rules.
- credential boundary: VS Code Webview must not own raw credentials; CLI or Extension Host may resolve only approved credential references in a later implementation plan.
- raw environment forbidden: UI, JSONL, stdout, stderr, logs, DOM, console, and test artifacts must not include raw environment dumps, raw token values, raw keys, or raw provider stderr.
- prompt injection handling: provider output, repository Markdown, active plan text, and generated artifacts must be treated as untrusted data when assembling prompts or diagnostics.
- destructive side effect: none in analysis plan.

## Handoff fields

handoff_account_login_mvp: single provider plus mock provider
handoff_api_key_adapter: excluded
handoff_oauth: separate approved plan after subscription-entitlement verification
handoff_secret_regression: synthetic sentinel across stdout/stderr, JSONL, logs, DOM, console, test artifacts
handoff_usability_review: required
handoff_transport: HTTPS allowlist and TLS verification
handoff_oauth_security: redirect URI binding and token-storage owner

## 승인된 입력

오너는 2026-07-18 사용자 메시지로 다음 필드를 승인했다.

- `approval_status: approved`
- `approved_date: 2026-07-18`
- `approval_provenance: user-message: 2026-07-18 "좋아" approving the recommended draft fields in this Codex thread`
- `owner: project owner`
- `subscription_entitlement_policy: ChatGPT Plus/Pro account-login 기반 Codex 사용을 허용하되, 별도 API key 과금 경로는 사용하지 않음`
- `billing_owner: project owner`
- `grant_scope_redirect_policy: Codex CLI의 공식 ChatGPT browser login/session 위임을 우선 사용하고, AgentOS 자체 OAuth client 등록은 별도 승인 전 금지`
- `allowed_model_policy: Codex account-login에서 공식적으로 허용되는 기본 Codex 모델만 사용`

## 오너 승인 템플릿

아래는 승인 당시 사용한 초안 템플릿이다. 현재 승인 상태는 상단의 실제 필드가 결정한다.

```text
owner = <approver name or role>
approval status = approved
approved date = 2026-07-18
approval provenance = user-message: <link, transcript marker, or exact owner approval source>
provider = Codex
credential type = account-login
subscription entitlement policy = <whether the selected subscription officially allows this login/model-call path and whether separate API/credit billing applies>
billing owner = <person, team, or workspace budget owner>
official document URL = https://developers.openai.com/codex/auth
official document checked date = 2026-07-18
grant scope redirect policy = <approved browser/device-code/CLI-delegation scope, redirect, and token-storage boundary>
allowed model policy = <approved models or model family and any usage limits>
```

승인 후에도 provider session 호출, OAuth client registration, credential persistence, and billing-affecting actions는 별도 implementation plan과 fresh Gate 2 review가 있어야 시작할 수 있다.

## 2026-07-23 범위 추가

- 승인 addendum: AgentOS는 provider registry와 auth store core foundation을 소유할 수 있다.
- current runtime path: `codex` 실사용 경로는 external CLI compatibility path를 유지한다.
- future native OAuth/transport requires a separate reviewed plan.
- 이 addendum은 API key adapter 제외, raw token/env/provider stderr 비노출, billing-affecting action 금지 원칙을 바꾸지 않는다.

## 2026-07-24 native Codex auth/transport 승인 addendum

- 승인 addendum: AgentOS는 이제 native Codex auth/transport(browser callback 우선 + device-code fallback login lifecycle, refresh/logout/status, WebSocket 우선/SSE fallback native streaming transport)를 직접 소유할 수 있다. approval scope는 `.agentos/project/exec-plans/active/2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md`로 구체화된 execution plan을 따른다.
- canonical path 전환: native auth/transport 구현이 완료되면 `codex` provider의 canonical 경로는 native provider이며, 기존 external CLI compatibility path(`agentos/llm/providers/codex_cli.py`)는 native 경로가 명시적으로 실패했을 때만 선택 가능한 recovery-only debug/rollback path로 재분류된다. external CLI compatibility path는 자동 기본 경로가 아니다.
- 여전히 금지: API key 입력, import, 저장, API-key adapter 구현. AgentOS 자체 OAuth client는 문서화된 공식 Codex account-login flow(browser callback/device-code)만 사용하며 별도의 비공식 endpoint를 추측해 사용하지 않는다.
- 여전히 금지: raw token, raw refresh token, raw key, raw environment, raw provider stderr, raw callback query, raw response body를 UI, JSONL, stdout/stderr, logs, DOM, console, test artifact에 노출하는 것.
- billing/entitlement: 이 addendum은 기존 `subscription_entitlement_policy`, `billing_owner`, `allowed_model_policy`를 바꾸지 않는다. native transport도 동일한 ChatGPT Plus/Pro account-login 기반 Codex 사용 정책과 허용 모델 정책을 따른다.
- 이 addendum은 API key adapter 제외, raw token/env/provider stderr 비노출, billing-affecting action 금지 원칙을 바꾸지 않는다.
