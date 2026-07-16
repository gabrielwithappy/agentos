# Implementation 지원 문서

이 카테고리는 root system contract나 requirements/risk 문서에 비해 너무 상세한 implementation supporting note를 담는다. 최소 구조에서는 requirement discovery package, contracts, schemas, traceability, verification evidence도 여기로 함께 모은다. `reference/`는 `implementation`, `operations`, `decisions` 세 category만 유지하므로 RTM, API example, visual support note, verification note도 별도 legacy category를 다시 만들지 말고 여기로 접는다. root project 문서, active execution plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, human approval requirements를 override하지 않는다.

## 사용할 때

- requirement brief, user stories, RTM, implementation guide를 별도 package로 남겨야 할 때.
- module decomposition, migration plan, data flow 세부가 `03-system-contract.md`를 너무 길게 만들 때.
- API example, schema, validation note, artifact manifest를 별도 evidence로 남겨야 할 때.
- implementation alternatives 또는 cross-cutting technical design에 reviewable evidence가 필요할 때.
- future implementation agent를 위해 ownership이나 sequencing을 보존해야 할 때.

## 필수 필드

모든 파일에는 Expansion Trigger, parent root doc, reason for creation, owner, freshness rule, status, source evidence, requirements/decisions/risks/verification으로 되돌아가는 링크, does not override statement가 있어야 한다.

각 doc은 `00-project-index.md` 또는 그 root index에 연결된 category list에 등록한다.
