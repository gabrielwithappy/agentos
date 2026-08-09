# AgentOS LLM 구독 로그인·연결 전략 수립 계획

> **상태:** 완료
> **작성일:** 2026-07-18<br>
> reviewed: true<br>
> usability_review_required: true (후속 계획이 CLI 명령·오류 메시지·VS Code 흐름을 변경하므로)<br>
> implementation_started_at: 2026-07-18T21:41:52+0900<br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `references`의 인증·자격증명·LLM 호출 경계를 비교하여, CLI 의존만으로 동작하는 현재 AgentOS에 안전하고 단계적인 **구독 계정(account-login) 기반** LLM 연결 방식을 결정하기 위한 승인 입력을 만든다. 단일 provider API-key 구현은 채택하지 않는다.

**사용자 결과:** 프로젝트 오너는 구독 account-login, OAuth 브라우저 로그인, device-code 로그인, 기존 CLI 위임의 특징·장단점과 권장 적용 순서를 한 문서에서 검토하고, 다음 구현 계획의 범위를 승인할 수 있다. API key 방식은 비교 항목일 뿐 구현 후보가 아니다.

**진행 상태:** 참조 프로젝트와 현재 CLI/VS Code 경계를 조사했고, 구현 전 전략 선택과 보안 게이트를 root docs/ADR로 handoff했다. 실제 provider approval은 `NEEDS_CONTEXT`로 남아 있으며, provider 승인 없이 진행 가능한 mock 기반 LLM Core MVP는 별도 구현계획으로 분리한다.

**아키텍처:** 인증 UI와 비밀값 보관·provider session 호출을 분리한다. VS Code Webview는 로그인 시작·상태·취소만 요청하고, Extension Host 또는 Python CLI가 credential reference를 해석해 provider adapter를 호출한다. 결과와 진단은 JSONL 이벤트로 역방향 전달하되, key·token·raw environment·raw stderr는 어느 UI 이벤트에도 넣지 않는다.

**기술 스택:** Python, Typer, 제공자 공식 CLI/app-server 또는 공식 SDK(승인 후 선택), OS credential store adapter, OAuth 2.1 Authorization Code + PKCE 또는 device authorization grant(제공자 지원 시), Codex OAuth/account-login provider adapter, TypeScript/VS Code Extension API.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | NEEDS_CONTEXT |
| 완료됨 | 참조 프로젝트와 AgentOS CLI/Extension 경계 조사, Pi docs 근거 보강, root docs/ADR handoff, Gate 2 리뷰 PASS |
| 현재 위치 | 분석 handoff 완료, Task 1.1 provider approval 입력 대기 |
| 다음 단계 | provider approval 없이 진행 가능한 `2026-07-18-agentos-llm-core-mvp.md` 구현계획을 Gate 2에 올림 |
| 완료 신호 | 인증 방식 비교, 권장안, 비범위, provider approval gate, mock 기반 후속 구현계획 handoff가 모두 문서화됨 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 구독 LLM 연결을 위한 우선순위와 안전한 구현 순서를 담은 의사결정 가능한 계획 |
| 누구를 위한 것인가? | 프로젝트 오너, 구현 담당자, 보안·운영 리뷰어 |
| 일상 사용에서 무엇이 달라지는가? | 장기적으로 사용자는 VS Code 또는 CLI에서 인증 후 AgentOS를 통해 모델 요청을 실행할 수 있다. 이번 계획은 이를 구현하지 않는다. |
| 무엇은 바뀌지 않는가? | 현재 CLI 실행 경로, VS Code Webview, provider 계정·키, 네트워크 설정, 비용 청구는 이 계획으로 변경하지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 근거 고정 | 참조 구현에서 확인한 인증·보관·호출 패턴을 재현 가능하게 확인 | `reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md` | `Run:` `test -f .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md && rg -q "auth_strategy_evidence" .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md && echo "PASS evidence-note-present"`<br>`Expected:` `PASS evidence-note-present` |
| 2. 선택지 평가 | 네 가지 연결 방식의 장단점과 채택 기준이 문서화됨 | 본 계획 및 후속 ADR | `Run:` `rg -q "LLM credential strategy" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "credential_type: account-login" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS credential-strategy-recorded"`<br>`Expected:` `PASS credential-strategy-recorded` |
| 3. 단계적 채택 | 1차 Codex account-login adapter, 2차 credential store, 3차 provider 확장을 분리한 후속 작업 범위 | 별도 active implementation plan | `Run:` `rg -q "handoff_account_login_mvp: single provider plus mock provider" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS handoff-mvp-scope"`<br>`Expected:` `PASS handoff-mvp-scope` |
| 4. 비밀 보호 설계 | UI·로그·JSONL에서 비밀값을 제외하는 검증 의무가 다음 계획에 인계됨 | 후속 CLI/Extension security tests | `Run:` `rg -q "handoff_secret_regression: synthetic sentinel across stdout/stderr, JSONL, logs, DOM, console, test artifacts" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS secret-regression-handoff"`<br>`Expected:` `PASS secret-regression-handoff` |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/traces/reviews/2026-07-18-llm-auth-api-adoption-analysis/`, `.agentos/project/exec-plans/README.md`
- durable result surface: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`, `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, 그리고 별도 구현 계획의 코드·테스트
- documentation-only exception: 이 문서는 분석·채택 계획만 제공한다. provider session 호출, credential 저장, OAuth client 등록은 오너 승인 뒤 별도 계획에서만 수행한다.

## 현재 근거와 선택지 분석

### 참조 구현에서 확인한 경계

| 참조 | 확인한 방식 | 장점 | 단점·AgentOS 적용 시 주의점 |
|---|---|---|---|
| Codex Python SDK | browser 로그인과 device-code 로그인 시작, 완료 대기, 취소를 typed handle로 분리 | headless 환경까지 포괄하고 취소·상태를 명시할 수 있음 | 특정 서비스 계정 로그인과 일반 API 호출을 같은 credential으로 가정하면 안 됨; 제공자 약관·SDK 지원을 사전 확인해야 함 |
| Codex VS Code 경로 | VS Code 설정이 CLI executable을 지정하고 app-server는 `stdio://` 및 `vscode` session source를 사용 | IDE가 UI·실행경로를 담당하고 login/turn runtime을 host에 둘 수 있음 | app-server protocol 전체를 MVP에 도입하면 현재 extension보다 범위가 커짐 |
| leaked-claude-code IDE 경로 | structured I/O·VS Code MCP capability allowlist, OAuth 401 단일 refresh/retry | IDE의 capability와 OAuth lifecycle을 분리해 secret 노출·무한 retry를 줄임 | remote bridge, MCP, trusted-device는 서비스 종속적이며 AgentOS의 구독 account-login MVP에 도입하지 않음 |
| OpenCodex | provider별 OAuth/API-key login을 CLI가 소유하고, proxy는 갱신된 설정만 소비 | UI가 key를 직접 다루지 않고, OAuth·key 방식을 같은 provider 경계에 둘 수 있음 | 설정 파일에 raw key를 저장하는 방식은 AgentOS의 기본안으로 채택하지 않음; OS credential store 또는 외부 secret reference가 필요 |
| AionUi | renderer가 제한된 IPC만 호출하고 main/preload가 host 경계를 소유 | Webview가 process·secret에 접근하지 못함 | Electron IPC를 그대로 이식하지 않고 VS Code Extension Host 메시지 검증으로 등가 경계를 구현 |
| Continue / Aider | provider별 API key와 모델 설정을 런타임에서 해석 | OpenAI-compatible API MVP를 빠르게 시작할 수 있음 | 환경변수만 의존하면 CI·headless에는 편하지만 개인 데스크톱의 지속적 보관과 key 회전 UX가 약함 |
| Hermes / Pi / Ouroboros | provider capability, 모델 선택, stream 이벤트를 실행 protocol과 분리 | provider 추가·fallback이 CLI/UI를 오염시키지 않음 | 첫 단계부터 registry·gateway·다중 provider를 만들면 과도한 일반화가 됨 |

### 연결 방식 비교

| 방식 | 특징 | 장점 | 단점 | AgentOS 적합도 |
|---|---|---|---|---|
| A. 외부 CLI만 실행 | 현재처럼 설치된 Codex 등 CLI subprocess에 위임 | 제공자 인증·업데이트를 upstream이 관리, 초기 개발 비용이 낮음 | AgentOS가 모델/비용/오류/세션을 제어하지 못하고, CLI 설치·TTY 계약에 결합 | 유지용 fallback으로 적합, 직접 API 기능의 주 경로로는 부적합 |
| B. API key 환경변수/일회 입력 | provider API key로 직접 HTTPS 호출 | mock HTTP 테스트가 쉽고 OpenAI-compatible endpoint를 넓게 지원 | 구독 계정 사용자가 기대하는 인증·비용 모델과 다르고 key 회전·다중 계정·데스크톱 저장 UX가 필요 | 비교·mock transport 검증 패턴으로만 참고하며, AgentOS의 구현 경로에서는 제외 |
| C. OS credential store의 API key | setup/login 명령이 key를 검증 후 keyring에 저장하고 런타임은 reference로 조회 | 편리한 재사용, 파일·UI 노출을 줄이고 logout/rotate를 제공 가능 | OS별 adapter와 headless fallback, keyring 잠김/복구 UX가 필요 | B가 안전하게 검증된 다음의 권장 개인 개발환경 경로 |
| D. OAuth browser + PKCE 또는 device-code | provider가 지원하는 사용자 계정 OAuth를 CLI가 시작·대기·취소·갱신 | API key 없이 구독/account-login 기반 연결을 모델링 가능; device code는 GUI 없는 환경을 지원 | provider별 scope·redirect·refresh 정책·약관에 강하게 결합, token 보호·revocation·callback 충돌을 구현해야 함 | 공식 API를 쓰지 않는 AgentOS의 1차 후보. 첫 대상은 Codex OAuth/account-login으로 제한 |

### 스킬·에이전트 선택 토론 결론

이 계획은 새 코드 구현이나 신규 실행계획 작성이 아니라, 참조 조사 결과를 바탕으로 구독 LLM 인증·연결 채택 전략의 문맥·범위·검증 기준을 정렬하는 분석 계획이다. 따라서 현재 분석 계획의 lead skill은 `brain`이다. 후속 구현 범위가 제품 요구와 승인 항목으로 쪼개질 때 `pm` 관점을 보조로 사용한다. `qa`는 보안 회귀·secret redaction·transport 검증 조건을 정의하는 보조 관점으로 사용하되, 이 문서의 lead skill로 두지 않는다. `principle-auditor`는 구현 전 Gate 2와 Simplicity Gate를 막는 거버넌스 관점이며, reviewer PASS artifact 없이는 `reviewed: true`로 전이하지 않는다.

상반된 두 관점의 결론은 다음과 같다.

| 관점 | 주장 | 반대 관점의 제약 | 채택 결론 |
|---|---|---|---|
| delivery/PM 관점 | Codex OAuth/account-login adapter와 mock provider를 먼저 고정해야 VS Code 실제 응답으로 이어질 수 있다. | provider registry, gateway, OS credential store, 다중 OAuth provider를 첫 구현에 넣으면 계획이 실행 불가능하게 커진다. | `brain`이 현재 분석 결론을 정렬하고, `pm`은 후속 ADR과 implementation plan에서 task decomposition 보조로만 사용한다. |
| risk/QA·principle 관점 | 인증·토큰·billing·공식 약관은 보안·운영 리스크이므로 오너 승인 전 구현을 막아야 한다. | 과도한 차단은 현재 CLI gap 분석을 멈추게 하므로, 분석 문서는 승인 입력까지만 만든다. | `qa`와 `principle-auditor`는 Gate 2와 후속 보안 검증의 필수 검토 관점으로 둔다. |

최종 선택은 `brain` 주도, `pm` 보조, `qa` 보안 검증 보조, `principle-auditor` Gate 2 검토다. 이 결론은 스킬 실행 권한을 우회하지 않으며, 실제 후속 구현 계획은 `plan-reviewer`, `principle-auditor`, 그리고 user-facing 변경 때문에 `usability-reviewer`의 PASS artifact가 있어야 한다.

### 권장 적용 전략

1. **1차 — 단일 Codex account-login adapter.** `agentos llm login codex`는 제공자가 공식적으로 허용한 기존 Codex CLI account session 위임 또는 AgentOS 자체 browser/device-code login 중 오너가 승인한 하나만 수행한다. API key 입력·import·저장은 제공하지 않는다. `agentos run --json`은 credential의 존재 여부만 보고하고, request/response는 provider-independent JSONL envelope로 다룬다. 이 단계는 실제 Codex subscription credential이 없어도 mock account-login credential과 mock provider로 완결 검증한다.
2. **2차 — credential store와 운영 명령.** `status`, `logout`, `rotate` 또는 `refresh`를 추가한다. 상태 출력은 provider/model/credential-present boolean과 account label만 반환한다. token raw value, raw environment, raw stderr는 출력하지 않는다.
3. **3차 — 다른 제공자별 OAuth 또는 account-login adapter.** 공식 문서와 앱 등록 권한이 확보된 제공자 한 곳에 한해 PKCE, device code, paste-code의 채택 여부를 결정한다. callback listener, state·PKCE verifier, timeout·cancel·logout·refresh/revocation은 채택된 경우의 후속 구현·검증 범위다.
4. **4차 — 다중 provider는 capability contract 이후.** 첫 adapter의 request/stream/error/cancel/usage contract가 tests로 고정된 뒤에만 Anthropic, cloud-hosted 또는 account-login provider를 추가한다. gateway, marketplace, 자동 failover는 별도 결정 없이는 도입하지 않는다.

## 범위 및 비범위

- 포함: 참조 기반 비교, 선택 기준, credential lifecycle, provider session 호출 경계, VS Code/CLI 보안 경계, 후속 구현·검증 순서.
- 제외: 실제 provider 계정 생성, OAuth client 등록, **API key 입력·import·저장 및 API-key adapter 구현**, 비용 발생, Chat API 전환, gateway/daemon, provider marketplace, 자동 model failover.
- Simplicity Gate: 첫 구현은 단일 account-login adapter와 단일 모델 선택만 허용한다. provider registry와 장기 실행 서버는 근거가 생길 때까지 추가하지 않는다.

## 의존성 분석

- 외부 의존성: 이번 분석 문서 작성에는 없음. 실제 provider session/OAuth/credential store는 구현 전 별도 계획의 의존성 게이트에서 선언한다.
- 분석 전제: 제공자별 API, OAuth grant, scope, redirect URI, token refresh/revocation, billing·약관은 현재 문서만으로 확정하지 않는다.
- 스캔 기준: Python CLI/VS Code Extension 경계, credential 저장 위치, repository-local reference source, root project 문서의 현재 제약.

## 실행 단계

### Task 0: 의사결정에 필요한 현재 근거를 고정

**파일:**
- 생성: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`

**사용자에게 보이는 마일스톤:** 현재 AgentOS 제약과 참조 구현의 차이를 인용 가능한 근거로 확인한다.

- [x] **Step 0.1: 현재 CLI가 credential을 소유하지 않고, VS Code extension source는 이 checkout에 아직 없음을 확인한다.**

Run: `rg -q "Prompt.ask" agentos/commands/run.py && test ! -f vscode-extension-mvp/src/agentos-runner.ts && ! rg -q "AGENTOS_LLM_API_KEY" agentos && echo "PASS current-credential-gap-confirmed"`
Expected: `PASS current-credential-gap-confirmed`

- [x] **Step 0.2: 참조 source path가 네 가지 전략의 근거를 제공함을 확인한다.**

Run: `test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/codex/sdk/python/src/openai_codex/_login.py && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/codex/codex-rs/app-server/src/main.rs && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/leaked-claude-code/cli/print.ts && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/leaked-claude-code/bridge/bridgeApi.ts && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/opencodex/src/oauth/login-cli.ts && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/AionUi/packages/desktop/src/preload/main.ts && echo "PASS auth-strategy-evidence-present"`
Expected: `PASS auth-strategy-evidence-present`

- [x] **Step 0.3: 조사 근거 supporting doc이 필수 메타데이터와 참조 경계를 포함하는지 확인한다.**

Run: `test -f .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md && for field in 'Expansion Trigger:' 'parent root doc:' 'reason for creation:' 'owner:' 'freshness rule:' 'status:' 'source evidence:' 'links back to:' 'does not override:' 'auth_strategy_evidence'; do rg -q "$field" .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md || exit 1; done && echo "PASS implementation-evidence-doc-registered"`
Expected: `PASS implementation-evidence-doc-registered`

### Task 1: 오너 승인 입력과 root SSOT 정렬

**파일:**
- 수정: `.agentos/project/01-project-charter.md`
- 수정: `.agentos/project/02-product-scope-and-requirements.md`
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`
- 수정: `.agentos/project/06-decisions-change-log.md`
- 수정: `.agentos/project/00-project-index.md`
- 생성: `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`

**사용자에게 보이는 마일스톤:** 실제 구현 전, 제공자·billing owner·허용 credential type·보관·복구 책임이 오너 승인으로 확정된다.

- [ ] **Step 1.1: 오너가 제공자와 credential lifecycle을 결정한다.**

ADR에는 다음 필드를 모두 기록한다: `Expansion Trigger:`, `parent root doc:`, `reason for creation:`, `owner:`, `freshness rule:`, `status:`, `source evidence:`, `links back to:`, `does not override:`, `approval_status: approved`, `approved_date:`, `approval_provenance:`, `approval_recorded_by:`, `provider:`, `credential_type: account-login`, `subscription_entitlement_policy:`, `billing_owner:`, `official_document_url:`, `official_document_checked_date:`, `grant_scope_redirect_policy:`, `allowed_model_policy:`. 이 입력이 하나라도 비어 있거나 `approval_status`가 `approved`가 아니면 `NEEDS_CONTEXT`로 중단하고 구현 계획을 만들지 않는다. `approval_provenance`는 현재 implementer가 스스로 만든 값이 아니라 사용자 승인 메시지, 외부 승인 문서, 또는 지정 approver 기록의 위치를 가리켜야 한다. `subscription_entitlement_policy`는 구독이 해당 로그인·모델 호출을 공식적으로 허용하는지와 별도 API 과금 여부를 명시해야 한다.

Run: `test -f .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && for field in 'Expansion Trigger:' 'parent root doc:' 'reason for creation:' 'owner:' 'freshness rule:' 'status:' 'source evidence:' 'links back to:' 'does not override:' '^approval_status: approved$' '^approved_date: [0-9]{4}-[0-9]{2}-[0-9]{2}$' '^approval_provenance: (user-message|external-approval|approver-record): .+' '^approval_recorded_by: .+' '^provider: .+' '^credential_type: account-login$' '^subscription_entitlement_policy: .+' '^billing_owner: .+' '^official_document_url: https?://.+' '^official_document_checked_date: [0-9]{4}-[0-9]{2}-[0-9]{2}$' '^grant_scope_redirect_policy: .+' '^allowed_model_policy: .+'; do rg -q "$field" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md || exit 1; done && ! rg -qi 'needs_context|owner-needed|owner 필요|pending|placeholder|tbd|todo|unknown|미정|대기|확인 필요' .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS owner-subscription-auth-input-recorded"`
Expected: `PASS owner-subscription-auth-input-recorded`

- [ ] **Step 1.2: 영향받는 5개 root SSOT와 index를 승인 결과에 정렬한다.**

`01`에는 owner/constraint, `02`에는 requirement·acceptance·비목표, `03`에는 runtime/credential boundary, `04`에는 OAuth·token·cost 위험, `06`에는 수용된 결정을 기록한다. `00`에는 새 ADR의 discoverability·freshness를 등록한다. `05-agent-operating-contract.md`는 에이전트 행동 계약이므로 이번 제품·인증 결정의 변경 대상이 아니다. persistent credential store 또는 OAuth가 승인되지 않으면 현재의 workspace-env/no-persistence 계약을 유지한다.

Run: `rg -q "LLM credential strategy" .agentos/project/01-project-charter.md && rg -q "REQ-LLM-001" .agentos/project/02-product-scope-and-requirements.md && rg -q "credential boundary" .agentos/project/03-system-contract.md && rg -q "token lifecycle" .agentos/project/04-safety-risk-verification.md && rg -q "0004-agentos-llm-credential-strategy" .agentos/project/06-decisions-change-log.md && rg -q "0004-agentos-llm-credential-strategy" .agentos/project/00-project-index.md && echo "PASS llm-ssot-aligned"`
Expected: `PASS llm-ssot-aligned`

- [ ] **Step 1.3: root SSOT와 ADR이 보안 민감 경계를 명시하는지 확인한다.**

`03`과 ADR에는 prompt/data boundary, credential boundary, raw stderr/stdout redaction, raw environment 금지를 기록한다. `04`와 ADR에는 token lifecycle, prompt injection handling, destructive/no-side-effect boundary, secret leakage 검증, environment filtering을 기록한다.

Run: `rg -q "prompt/data boundary" .agentos/project/03-system-contract.md .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "raw environment forbidden" .agentos/project/03-system-contract.md .agentos/project/04-safety-risk-verification.md .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "prompt injection handling" .agentos/project/04-safety-risk-verification.md .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "destructive side effect: none in analysis plan" .agentos/project/04-safety-risk-verification.md .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS security-sensitive-boundary-recorded"`
Expected: `PASS security-sensitive-boundary-recorded`

### Task 2: 후속 구현 계획 handoff 의무를 고정

**파일:**
- 수정: `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`

**사용자에게 보이는 마일스톤:** 실제 provider session 호출은 승인된 provider의 계약을 사용하고, synthetic sentinel 기반의 비밀 누출 검증을 포함하는 별도 계획에서만 시작된다는 인계 조건이 결정 기록에 남는다.

- [ ] **Step 2.1: ADR에 구독 account-login 후속 계획 분리 조건을 기록한다.**

첫 계획은 승인된 단일 provider의 account-login adapter와 mock provider만 포함한다. API key adapter는 어떤 단계에도 포함하지 않는다. OS credential store와 provider-approved OAuth/device code는 해당 provider의 subscription entitlement, security·cancel·error contract가 검증된 뒤 별도 계획으로 둔다.

Run: `rg -q "handoff_account_login_mvp: single provider plus mock provider" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "handoff_api_key_adapter: excluded" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "handoff_oauth: separate approved plan after subscription-entitlement verification" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS subscription-implementation-scope-separated"`
Expected: `PASS subscription-implementation-scope-separated`

- [ ] **Step 2.2: 후속 계획의 secret regression contract를 점검한다.**

synthetic sentinel을 credential resolution, HTTP authorization, CLI stdout/stderr, JSONL event, exception/log capture, Webview DOM·console·test artifact에 주입하고 전부 부재를 검사하는 테스트를 요구한다. 실제 secret은 어떠한 테스트에도 사용하지 않는다.

Run: `rg -q "handoff_secret_regression: synthetic sentinel across stdout/stderr, JSONL, logs, DOM, console, test artifacts" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS secret-regression-handoff"`
Expected: `PASS secret-regression-handoff`

- [ ] **Step 2.3: 후속 계획이 UX·transport 보안 경계를 명시하는지 확인한다.**

후속 계획은 CLI 명령·오류·VS Code 상태를 바꾸므로 usability-reviewer PASS artifact를 요구한다. 또한 HTTPS endpoint allowlist/TLS 검증, OAuth redirect URI binding, token storage owner를 승인된 provider별 계약으로 명시해야 한다.

Run: `rg -q "handoff_usability_review: required" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "handoff_transport: HTTPS allowlist and TLS verification" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "handoff_oauth_security: redirect URI binding and token-storage owner" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && echo "PASS ux-transport-handoff"`
Expected: `PASS ux-transport-handoff`

## 검증 및 수용 기준

- [ ] 현재 CLI/extension의 credential gap과 references source evidence를 local command로 재현한다.
- [ ] 오너가 provider별 account-login credential과 구독 entitlement를 승인하고, 공식 문서 URL·확인 날짜·billing owner를 ADR에 남긴다.
- [ ] 영향받는 5개 root SSOT와 `00-project-index.md`가 승인된 scope·acceptance·architecture·risk·decision 및 ADR discoverability와 정렬된다.
- [ ] 스킬 선택 결론은 `brain` 주도, `verification-before-completion` 완료 전 검증, `plan-reviewer`·`principle-auditor` 반대 관점 검토로 기록되어 있으며 reviewer PASS를 대체하지 않는다.
- [ ] 후속 구현 계획은 synthetic sentinel을 stdout/stderr, JSONL, logs, DOM, console, test artifacts 전체에 주입·검사하는 보안 회귀를 Gate 0에 포함한다.
- [ ] 실제 provider 호출은 후속 계획에서 provider-specific subscription entitlement·credential·network·terms preflight가 PASS일 때에만 수행한다.

## 세션 재개 체크포인트

- 현재 완료 범위: 참조 기반 인증 방식 비교, Pi 구조 근거 보강, root docs/ADR handoff, secret/security handoff 조건 기록.
- 미완료 작업: 오너의 Codex OAuth/account-login credential lifecycle approval, 실제 provider/OAuth/credential-store preflight, 실제 provider adapter 구현.
- 다음 세션 첫 작업: `2026-07-18-agentos-llm-core-mvp.md`를 Gate 2 리뷰한 뒤 mock provider 기반 LLM runtime surface를 구현한다.
- 아직 안 한 검증: 실제 provider/OAuth/credential-store preflight와 provider terms/entitlement 검증.
- 관련 trace checkpoint: `.agents/traces/reviews/2026-07-18-llm-auth-api-adoption-analysis/`, archived plan `.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md`, follow-up plan `.agentos/project/exec-plans/active/2026-07-18-agentos-llm-core-mvp.md`.

## 리뷰 반영 이력

- 초안: references의 Codex/OpenCodex/AionUi/Continue/Aider/Hermes/Pi/Ouroboros 경계와 현재 AgentOS CLI scaffold를 비교해 작성함.
- 초안 Gate 2 원칙: plan-reviewer 및 principle-auditor의 분리된 PASS artifact가 생성되기 전까지 `reviewed: false`를 유지한다.
- 후속 implementation plan은 user-facing CLI/VS Code 흐름을 바꾸므로 usability-reviewer PASS artifact까지 있어야 한다.
- 2026-07-18 Gate 2 1차: `plan-reviewer=FAIL`, `principle-auditor=REVISE`, `usability-reviewer=PASS`. 반영: nonexistent VS Code path와 root `HISTORY.md` 참조 제거, supporting doc 생성 Step 추가, ADR 필수 필드와 approval provenance 검증 강화, 보안 민감 root SSOT 검증 Step 추가.
- 2026-07-18 Gate 2 최신: `plan-reviewer=PASS`, `principle-auditor=PASS_FOR_ANALYSIS_ONLY`, `usability-reviewer=PASS`. Owner approval remains `NEEDS_CONTEXT` and provider calls remain blocked until approval. Current plan hash and reviewer evidence are stored in `.agents/traces/reviews/2026-07-18-llm-auth-api-adoption-analysis/`.
- 2026-07-18 handoff 정리: Pi docs evidence를 supporting implementation note에 추가하고, provider approval 없이 진행 가능한 mock 기반 LLM Core MVP를 별도 active implementation plan으로 분리한다. 이 분석 계획은 완료 archive 대상이 아니라 `NEEDS_CONTEXT (분석 handoff 완료)` 상태로 유지한다.

### 스킬 선택 토론 결과 (2026-07-18)

**토론 질문:** `2026-07-18-llm-auth-api-adoption-analysis` 계획을 계속 보강할 때 어떤 하네스 스킬·관점이 주도해야 하는가?

| 관점 | 주장 | 반론·제약 | 수렴 결론 |
|---|---|---|---|
| 전달·제품 관점 | 이미 참조 조사와 채택 전략은 문서화되어 있으므로 새 구현 계획을 다시 작성하기보다 의사결정 문서로 최소 보강해야 한다. | 스킬을 과하게 추가하면 분석 문서가 구현 실행처럼 변하고 Gate 2 의미가 흐려진다. | 주도 스킬은 `brain`으로 한정해 라우팅·문맥·검증 기준만 잡는다. |
| 원칙·리스크 관점 | LLM 인증은 secret, OAuth, billing, VS Code UX를 건드리므로 `principle-auditor` 성격의 단순성·보안 경계가 계속 반대편에서 검문해야 한다. | 이 토론은 공식 Gate 2 PASS artifact가 아니며 `reviewed: true`로 전이할 수 없다. | 반대 검토 축은 `plan-reviewer`와 `principle-auditor` 역할로 유지하되, 후속 구현 전 fresh PASS artifact를 별도로 만든다. |

**선택:** 현재 분석 계획의 주도 스킬은 `brain`이다. 이유는 이 작업이 코드 구현이 아니라 하네스 라우팅, 문맥 로딩, 계획 품질, 검증 조건을 정렬하는 문서 작업이기 때문이다.

**보조 사용:** 완료 보고 직전에는 `verification-before-completion`을 적용해 문서 변경과 핵심 문자열을 fresh command로 확인한다.

**사용하지 않음:** `writing-plans`는 이미 active plan이 존재하므로 새 계획 생성을 위해 재호출하지 않는다. `executing-plans`는 실제 API/OAuth 구현을 시작하지 않으므로 사용하지 않는다. `qa`는 후속 구현의 보안·회귀 테스트 설계 때 사용하고, 이번 스킬 선택 토론의 주도 스킬로 삼지 않는다. `principle-auditor` 스킬은 `.agents/` 구조 변경이 없으므로 스킬로 호출하지 않고, 반대 관점 역할만 유지한다.

## 구현 결과

분석 handoff 문서다. 실제 provider 호출 구현은 오너가 제공자·비용·credential 정책을 승인한 뒤 별도 실행 계획에서 기록한다. provider approval 없이 가능한 mock 기반 runtime surface는 `2026-07-18-agentos-llm-core-mvp.md`에서 다룬다.

## 사용 방법

프로젝트 오너는 먼저 “Codex OAuth/account-login MVP 승인 여부”와 기존 Codex CLI token import 허용 여부를 결정한다. 승인된 root SSOT와 ADR을 근거로 별도 implementation plan을 Gate 2 리뷰에 제출한다.

## 아카이브 결정

분석 결과는 후속 implementation plan의 근거로 보존한다. 2026-07-18 사용자 요청에 따라 active에서 archive로 이동했다.
