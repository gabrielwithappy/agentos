# 제품 범위 및 요구사항

목적: Define user outcomes, requirement scope, acceptance, 추적성, and 비목표.
주요 독자: 프로젝트 오너, 계획 에이전트, 구현 에이전트, 리뷰어/운영자.
가능하게 하는 결정: requirement inclusion, scope-change decision, acceptance 준비 상태, supporting-doc trigger.
에이전트 핵심 정보: requirement IDs, user outcomes, acceptance criteria, 추적성, 비목표, unresolved questions.
현재 증거 / 최신성: update whenever requirement, acceptance, or user priority changes.

## 사용자 결과

- 주요 사용자: AgentOS를 처음 접하는 개발자 및 기여자
- 사용자 워크플로우: 프로젝트 클론 -> setup.sh 실행 -> 시작 가이드 문서를 통한 환경 이해
- 원하는 결과: `agent-harness`에 대한 혼란 없이, 최소한의 AgentOS(portable agentcore) 실행 환경을 셋업하고 agent-harness 기능들이 점진적으로 도입될 것임을 인지하는 것
- 피해야 할 실패 상태: `aha` 등 아직 AgentOS에 완전히 편입되지 않은 명령어를 시도하다 실패하여 이탈하는 것

## 요구사항과 acceptance

| ID | requirement | Priority | acceptance | 추적성 | Evidence link / 검증 근거 | status |
|---|---|---|---|---|---|---|
| REQ-001 | AgentOS 설치 후 기본 확인 가이드 제공 | must | `setup.sh` 및 `verify-public-test-suite.sh` 통과 후의 명확한 상태 안내 제공 | | | 현재 |
| REQ-002 | agent-harness 기능의 점진적 마이그레이션 안내 | must | 향후 agent-harness 기능들이 AgentOS로 통합될 예정임이 가이드에 명시됨 | | | 현재 |
| REQ-003 | AHA CLI 쉘 스크립트 파이썬 이관 및 카탈로그 통일 | must | `aha` 명령어가 `agentos` 서브 커맨드로 100% 이관되고 카탈로그에서 잔재가 제거됨 | 2026-07-17-aha-cli-refactoring.md | `verify-public-test-suite.sh` 통과 | 완료 |

추적성 규칙:

- Do not claim requirement completion without a source doc and 검증 근거 path.
- If the 요구사항 table becomes too large or one requirement maps to multiple implementation/test artifacts, create a registered `reference/implementation/` RTM supporting doc.

## 범위 경계

포함:

- `docs/getting-started.md` 전면 개편
- `README.md` 문맥 교정 (필요시)
- `aha` 잔재 제거를 위한 `catalog/` 마크다운 및 JSON 수정
- `agentos` CLI 서브 커맨드 구현 (agent, skill, harness) 및 쉘 스크립트 폐기

제외:

- 코어 엔진(`harness_loop.py`) 내부의 추론 로직 자체 수정
- 일반적인 대화형 채팅 REPL(챗봇 UI)의 자체 구현 및 고도화 (외부 전문 채널에 위임)

범위 변경 트리거:

- 추가적인 문서(예: SECURITY.md)에서도 혼동을 주는 문구가 발견될 경우

## 미해결 질문

| Question | Owner | Impact | Blocking? |
|---|---|---|---|
|  |  |  |  |

## 지원 문서

이 root doc이 너무 길어지거나 모호해질 때만 requirement brief, user stories, RTM, implementation guide, wireframe-like support note를 `reference/implementation/` 아래 supporting doc으로 만든다. supporting doc은 `00-project-index.md`에 등록되어야 한다.
