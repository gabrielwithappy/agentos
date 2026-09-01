# AgentOS 프로젝트 문서

이 디렉터리는 `agentos project init`이 새 프로젝트에 복사하는 프로젝트 문서 템플릿 패키지의 원본이다. It defines the project document set.

- 원본 template: `docs/project/template/`
- 대상 프로젝트의 canonical 문서 경로: `.agentos/project/`
- 대상 프로젝트 문서는 사용자가 소유하며, `project init`은 기존 파일을 덮어쓰지 않는다.

이 문서는 프로젝트의 방향·요구사항·시스템 계약·위험·운영 계약·결정 로그를 기록하는 starter set이다. 실제 프로젝트에 적용한 뒤 내용을 채우고, active execution plan과 구현의 SSOT로 사용한다.

Supporting categories: `reference/implementation/`, `reference/decisions/`, `reference/operations/`.

이 문서는 root project documents, active plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, 또는 human approval requirements를 override하지 않는다.
