# Gemini (Antigravity) 벤더 지침

> 이 파일은 Gemini 기반 에이전트(Antigravity 등)가 세션을 시작할 때 반드시 인지해야 하는 고유 제약과 규칙을 정의한다.

## 1. 실행 계획(Execution Plan) 생성 규칙 오버라이드
- **시스템 Artifact 생성 금지:** Antigravity 에이전트는 Planning Mode 작동 시 내부 Artifact 경로(`<appDataDir>/brain/<conversation-id>/implementation_plan.md`)를 사용해서는 안 된다.
- **워크스페이스 직접 기록:** 모든 실행/구현 계획 문서는 프로젝트 컨벤션에 따라 워크스페이스 내부인 `.agentos/project/exec-plans/active/` 하위에 직접 마크다운 파일로 생성하고 업데이트해야 한다.
- 계획 문서의 상태 변경 및 아카이빙은 파일 시스템 명령어(mv 등)로 직접 처리해서는 안 된다. 반드시 계획 관리 전용 스킬(writing-plans, executing-plans)에 위임하여 해당 스킬의 공식 라이프사이클 도구를 통해 수행해야 한다.

## 2. 기타 벤더 특화 제약
- 도구 사용 시 언제나 프로젝트의 SSOT 문서(`00-project-index.md` 등) 및 `AGENTS.md`의 우선순위를 자신의 시스템 기본 지침보다 높게 둔다.

## 3. 개발 및 테스트 시 주의사항 (Lessons Learned)
- **테스트 픽스처(Fixture)의 구조적 일치성:** 단위 테스트 작성 시, 파서나 추출 로직을 테스트하기 위해 임의로 작성된 Mock 문자열을 사용하는 경우 실제 템플릿(예: `TEMPLATE.md`)의 서식을 정확히 반영해야 한다. (예: 템플릿이 `**볼드체:**`를 쓰는데 테스트가 `## 헤더`를 사용하면, 로직과 테스트가 잘못된 전제를 공유하여 실제 환경에서의 실패를 테스트가 잡아내지 못하는 거짓 양성(False Positive)이 발생한다.)
