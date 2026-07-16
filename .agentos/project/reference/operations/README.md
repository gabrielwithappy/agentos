# Operations 지원 문서

이 카테고리는 deployment, runtime, recovery, credential, operator runbook을 담는다. `reference/`는 `implementation`, `operations`, `decisions` 세 category만 유지하므로 운영 절차, 복구 단계, runtime assumption evidence는 별도 legacy category를 다시 만들지 말고 여기로 접는다. root project 문서, active execution plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, human approval requirements를 override하지 않는다.

## 사용할 때

- deployment, restart, recovery, credential, operational procedure에 지속적인 단계가 필요할 때.
- operator action에 side effect가 있거나 승인이 필요할 때.
- reviewer/operator checks를 위해 runtime assumption을 보존해야 할 때.

## 필수 필드

모든 파일에는 Expansion Trigger, parent root doc, reason for creation, owner, freshness rule, status, source evidence, requirements/decisions/risks/verification으로 되돌아가는 링크, does not override statement가 있어야 한다.

각 doc은 `00-project-index.md` 또는 그 root index에 연결된 category list에 등록한다.
