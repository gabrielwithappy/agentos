# Gemini (Antigravity) 벤더 지침

> 이 파일은 Gemini 기반 에이전트(Antigravity 등)가 세션을 시작할 때 반드시 인지해야 하는 고유 제약과 규칙을 정의한다.

## 1. 실행 계획(Execution Plan) 생성 규칙 오버라이드
- **시스템 Artifact 생성 금지:** Antigravity 에이전트는 Planning Mode 작동 시 내부 Artifact 경로(`<appDataDir>/brain/<conversation-id>/implementation_plan.md`)를 사용해서는 안 된다.
- **워크스페이스 직접 기록:** 모든 실행/구현 계획 문서는 프로젝트 컨벤션에 따라 워크스페이스 내부인 `.agentos/project/exec-plans/active/` 하위에 직접 마크다운 파일로 생성하고 업데이트해야 한다.
- 완료된 계획은 `.agentos/project/exec-plans/archive/` 로 이동한다.

## 2. 기타 벤더 특화 제약
- 도구 사용 시 언제나 프로젝트의 SSOT 문서(`00-project-index.md` 등) 및 `AGENTS.md`의 우선순위를 자신의 시스템 기본 지침보다 높게 둔다.
