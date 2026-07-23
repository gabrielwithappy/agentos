# 프로젝트 헌장

목적: Explain the value, stakeholder map, constraints, and completion signal for this project.
주요 독자: 프로젝트 오너, 리뷰어/운영자, 계획 에이전트, and 후속 핸드오프 에이전트.
가능하게 하는 결정: start/stop decision, stakeholder routing, value tradeoff, approval need, completion 준비 상태.
에이전트 핵심 정보: value statement, stakeholder map, approval map, constraints, non-negotiables, completion evidence.
현재 증거 / 최신성: update before opening an 실행 계획 and whenever value, stakeholder, approval, or constraints change.

## 가치

- 가치: 개발자가 별도 프론트엔드 없이도 AgentOS를 설치, 대화, 자동화, 진단할 수 있는 독립 터미널 경험을 제공한다.
- 사용자/비즈니스 문제: 현재 CLI는 최소 명령군은 있으나 source checkout/CWD에 의존하고 대화형 입력과 hook lifecycle의 계약이 없어 일관된 사용자 워크플로우를 제공하지 못한다.
- 아무것도 하지 않을 때의 비용: 사용자는 command semantics와 상태 복구를 추측해야 하며, harness 개선에 유용한 입력·hook 관측을 안전하게 축적할 수 없다.
- 기대 프로젝트 결과: TTY 대화형 CLI, 명시적 command family, JSONL automation mode, 안전한 hook/input lifecycle, session·diagnostic UX를 갖춘 AgentOS CLI.
- 완료 신호: reviewed implementation plan의 focused tests, isolated-install smoke, pseudo-TTY interaction checks, secret-redaction regression, public suite가 모두 통과한다.

## 이해관계자 맵

| Role | Owner | Decision 권한 기준 | Contact/channel | Status |
|---|---|---|---|---|
| 프로젝트 오너 |  |  |  | owner 필요 |
| approver |  |  |  | owner 필요 |
| 리뷰어/운영자 |  |  |  | owner 필요 |
| implementation owner |  |  |  | owner 필요 |

## 제약과 비협상 경계

- 일정:
- 예산/자원:
- 정책/보안: LLM credential strategy는 account-login 후보만 검토한다. API key 입력, import, 저장, API-key adapter 구현은 현재 승인 범위가 아니다.
- 의존성: Codex account-login strategy는 `0004-agentos-llm-credential-strategy.md`에서 승인됨. Provider session 호출 구현은 별도 implementation plan과 fresh Gate 2 review 뒤에만 시작한다.
- 되돌리기 어려운 작업:
- 비협상 경계: raw token, raw key, raw environment, raw provider stderr는 UI, JSONL, stdout/stderr, logs, DOM, console, test artifacts에 노출하지 않는다.

## 승인과 완료

- 현재 승인 상태: 독립 대화형 CLI와 hook/input lifecycle 방향이 승인됨. LLM runtime은 2026-07-23 기준으로 provider registry + auth store core foundation 구현이 승인되었고, `codex` 실사용 경로는 external CLI compatibility path를 유지한다.
- 승인 근거: `.agentos/project/reference/decisions/0005-agentos-independent-interactive-cli.md`, `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- 완료 이해: 새 CLI 구현 계획이 command/event/hook/session/test 계약을 확정하고 Gate 2를 통과하면 구현을 시작할 수 있다.
- 남은 소유자 질문: hook의 첫 MVP에서 사용자 설정 hook을 어떤 선언형 형식으로 제공할지와 session 보존 기간은 실행 계획에서 안전한 기본값과 함께 확정한다.

## 지원 문서

value, stakeholder context, approval evidence, completion criteria를 분명히 할 때만 supporting doc을 여기에 등록한다.

- `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` - approved LLM credential strategy owner approval record.
- `.agentos/project/reference/decisions/0005-agentos-independent-interactive-cli.md` - approved independent interactive CLI and hook/input direction.
