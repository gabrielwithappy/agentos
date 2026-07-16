# Decision 지원 문서

이 카테고리는 ADR, 아키텍처 판단 근거, 장기 전략, audit/review, experiment note, handoff-sized context를 담는다. `reference/`는 `implementation`, `operations`, `decisions` 세 category만 유지하므로 review note, audit evidence, handoff pack, long-lived rationale는 별도 legacy category를 다시 만들지 말고 여기로 접는다. root project 문서, active execution plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, human approval requirements를 override하지 않는다.

## 사용할 때

- decision 맥락, 검토한 옵션, 결과가 `06-decisions-progress-change-log.md`를 너무 길게 만들 때.
- architecture rationale나 review/audit 결과를 장기 보존해야 할 때.
- future reviewer나 agent를 위해 결정의 영속적인 evidence가 필요할 때.
- 승인된 tradeoff나 closeout/handoff context를 requirements, risks, verification과 연결해야 할 때.

## 필수 필드

모든 파일에는 Expansion Trigger, parent root doc, reason for creation, owner, freshness rule, status, source evidence, requirements/decisions/risks/verification으로 되돌아가는 링크, does not override statement가 있어야 한다.

각 doc은 `00-project-index.md` 또는 그 root index에 연결된 category list에 등록한다.
