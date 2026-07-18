# Codex 벤더 지침

> 이 파일은 Codex 기반 에이전트가 세션을 시작할 때 반드시 인지해야 하는 고유 제약과 규칙을 정의한다.

## 1. 실행 계획(Execution Plan) 생성 경로
- **계획 파일 위치:** 모든 실행/구현 계획 문서는 프로젝트 컨벤션에 따라 워크스페이스 내부인 `.agentos/project/exec-plans/active/` 하위에 직접 마크다운 파일로 생성하고 업데이트해야 한다. 
- 계획 문서를 시스템 내부 임시 경로나 외부로 이탈시키지 않도록 각별히 주의한다.
- 완료된 계획은 `.agentos/project/exec-plans/archive/` 로 이동한다.

## 2. 기타 벤더 특화 제약
- 도구 사용 및 파일 시스템 접근 시 언제나 프로젝트의 SSOT 문서(`00-project-index.md` 등) 및 `AGENTS.md` 지침을 준수한다.
