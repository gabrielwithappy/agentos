# 제품 범위 및 요구사항

목적: Define user outcomes, requirement scope, acceptance, 추적성, and 비목표.
주요 독자: 프로젝트 오너, 계획 에이전트, 구현 에이전트, 리뷰어/운영자.
가능하게 하는 결정: requirement inclusion, scope-change decision, acceptance 준비 상태, supporting-doc trigger.
에이전트 핵심 정보: requirement IDs, user outcomes, acceptance criteria, 추적성, 비목표, unresolved questions.
현재 증거 / 최신성: update whenever requirement, acceptance, or user priority changes.

## 사용자 결과

- 주요 사용자: AgentOS를 처음 접하는 개발자 및 기여자
- 사용자 워크플로우: 독립 설치 -> `agentos setup` -> `agentos` 대화형 세션 또는 `agentos run --once` 자동화 -> `agentos doctor`로 복구/진단
- 원하는 결과: source checkout이나 별도 프론트엔드 없이 일관된 AgentOS command, 대화형 입력, session, hook 관리와 복구 안내를 사용한다.
- 피해야 할 실패 상태: 현재 디렉터리에 따라 명령이 달라지거나, hook 실패·입력 취소·provider 오류에서 사용자가 다음 행동을 알 수 없는 상태.

## 요구사항과 acceptance

| ID | requirement | Priority | acceptance | 추적성 | Evidence link / 검증 근거 | status |
|---|---|---|---|---|---|---|
| REQ-001 | AgentOS 설치 후 기본 확인 가이드 제공 | must | `setup.sh` 및 `verify-public-test-suite.sh` 통과 후의 명확한 상태 안내 제공 | | | 현재 |
| REQ-002 | agent-harness 기능의 점진적 마이그레이션 안내 | must | 향후 agent-harness 기능들이 AgentOS로 통합될 예정임이 가이드에 명시됨 | | | 현재 |
| REQ-003 | AHA CLI 쉘 스크립트 파이썬 이관 및 카탈로그 통일 | must | `aha` 명령어가 `agentos` 서브 커맨드로 100% 이관되고 카탈로그에서 잔재가 제거됨 | 2026-07-17-aha-cli-refactoring.md | `verify-public-test-suite.sh` 통과 | 완료 |
| REQ-LLM-001 | LLM credential strategy 승인 입력 고정 | must | provider, credential type, subscription entitlement, billing owner, official document URL/check date, grant/scope/redirect policy, allowed model policy가 ADR에 승인 근거와 함께 기록됨 | `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` | `PASS owner-subscription-auth-input-recorded` | 현재 |
| REQ-LLM-002 | API key adapter를 1차 구현 경로에서 제외 | must | ADR과 후속 handoff가 API key 입력, import, 저장, API-key adapter 구현 제외를 명시함 | `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` | `PASS subscription-implementation-scope-separated` | 현재 |
| REQ-LLM-003 | Mock-only LLM runtime contract 추가 | must | 실제 provider 호출, OAuth, API key, persistent credential store, billing 없이 mock provider와 sanitized JSONL event contract가 CLI에서 검증됨 | `.agentos/project/exec-plans/active/2026-07-18-agentos-llm-core-mvp.md` | `pytest tests/test_cli.py tests/test_llm_core.py -q`; `PASS secret-redaction-jsonl`; `PASS llm-core-docs-aligned` | 현재 |
| REQ-CLI-001 | 독립 대화형 AgentOS CLI | must | isolated install 후 source checkout 밖에서도 `agentos --help`, `agentos setup`, `agentos doctor`, TTY 대화형 세션, `run --once`가 명시된 exit/output contract로 동작 | `0005-agentos-independent-interactive-cli.md` | `PASS cli-focused-suite`; `PASS agentos-cli-isolated-install`; `PASS interactive-cli-acceptance`; `PASS agentos-independent-cli-suite` | 완료 |
| REQ-CLI-002 | 안전하고 관측 가능한 hook/input lifecycle | must | hook ordering/timeout/failure/cancel/redaction이 typed event와 tests로 검증되고, hook이 JSONL stdout과 credential boundary를 침범하지 않음 | `0005-agentos-independent-interactive-cli.md` | `PASS cli-hook-registry-contract`; `PASS cli-hook-secret-regression`; `PASS interactive-cli-acceptance` | 완료 |

추적성 규칙:

- Do not claim requirement completion without a source doc and 검증 근거 path.
- If the 요구사항 table becomes too large or one requirement maps to multiple implementation/test artifacts, create a registered `reference/implementation/` RTM supporting doc.

## 범위 경계

포함:

- `docs/getting-started.md` 전면 개편
- `README.md` 문맥 교정 (필요시)
- `aha` 잔재 제거를 위한 `catalog/` 마크다운 및 JSON 수정
- 독립 설치 가능한 `agentos` CLI command family와 대화형 session surface
- typed event stream, user input normalization, opt-in hook lifecycle, session/history UX
- `README`와 `docs/getting-started.md`의 설치·대화·자동화·복구 안내

제외:

- 코어 엔진(`harness_loop.py`) 내부의 추론 로직 자체 수정
- pi의 TypeScript/Bun/TUI runtime 직접 이식, Hermes gateway/메신저/백업 등 대규모 운영 command 복제
- arbitrary third-party code hook 또는 승인 없는 project-local hook 실행
- LLM API key 입력, import, 저장, API-key adapter 구현
- provider session 호출, OAuth client 등록, credential persistence, or billing-affecting actions before a separate reviewed implementation plan

허용된 예외:

- `REQ-LLM-003`의 mock-only LLM runtime contract는 provider credential strategy 승인 전에도 구현할 수 있다. 이 예외는 실제 provider 호출, OAuth/account-login, API key path, persistent credential store, billing-affecting behavior, or approved credential status claim을 만들 수 없다.

범위 변경 트리거:

- 추가적인 문서(예: SECURITY.md)에서도 혼동을 주는 문구가 발견될 경우

## 미해결 질문

| Question | Owner | Impact | Blocking? |
|---|---|---|---|
| 실제 Codex account-login provider adapter의 구현 파일, runtime command surface, and verification sequence는 무엇인가? | implementation owner | 후속 구현 계획 범위 결정 | Yes, for real provider implementation |
| 첫 CLI MVP의 hook 선언 형식과 session 보존 기간은 무엇인가? | implementation owner | REQ-CLI-002 API 및 migration 범위 | Yes, for CLI implementation plan |

## 지원 문서

이 root doc이 너무 길어지거나 모호해질 때만 requirement brief, user stories, RTM, implementation guide, wireframe-like support note를 `reference/implementation/` 아래 supporting doc으로 만든다. supporting doc은 `00-project-index.md`에 등록되어야 한다.

- `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md` - LLM auth_strategy_evidence and current credential gap.
- `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` - approved LLM credential strategy approval record.
- `.agentos/project/reference/decisions/0005-agentos-independent-interactive-cli.md` - independent interactive CLI and hook/input direction.
