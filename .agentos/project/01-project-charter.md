# 프로젝트 헌장

목적: Explain the value, stakeholder map, constraints, and completion signal for this project.
주요 독자: 프로젝트 오너, 리뷰어/운영자, 계획 에이전트, and 후속 핸드오프 에이전트.
가능하게 하는 결정: start/stop decision, stakeholder routing, value tradeoff, approval need, completion 준비 상태.
에이전트 핵심 정보: value statement, stakeholder map, approval map, constraints, non-negotiables, completion evidence.
현재 증거 / 최신성: update before opening an 실행 계획 and whenever value, stakeholder, approval, or constraints change.

## 가치

- 가치:
- 사용자/비즈니스 문제:
- 아무것도 하지 않을 때의 비용:
- 기대 프로젝트 결과:
- 완료 신호:

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

- 현재 승인 상태: LLM credential strategy approved. `0004-agentos-llm-credential-strategy.md`가 승인 근거다.
- 승인 근거: `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- 완료 이해: provider, billing owner, subscription entitlement, official document URL/check date, grant/scope/redirect policy, and allowed model policy가 승인되었으므로 후속 real provider implementation plan을 작성할 수 있다.
- 남은 소유자 질문: 없음. 실제 provider 구현 범위와 테스트 명령은 별도 계획에서 확정한다.

## 지원 문서

value, stakeholder context, approval evidence, completion criteria를 분명히 할 때만 supporting doc을 여기에 등록한다.

- `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` - approved LLM credential strategy owner approval record.
