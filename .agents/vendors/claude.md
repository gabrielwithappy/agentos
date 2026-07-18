# Claude Code 벤더 지침

> 이 파일은 Claude Code 기반 에이전트가 세션을 시작할 때 반드시 인지해야 하는 고유 제약과 규칙을 정의한다.

## 1. 실행 계획(Execution Plan) 생성 경로
- **계획 파일 위치:** 모든 실행/구현 계획 문서는 시스템의 임시 경로나 별도의 아티팩트가 아닌, 프로젝트 컨벤션에 따라 워크스페이스 내부인 `.agentos/project/exec-plans/active/` 하위에 직접 마크다운 파일로 생성하고 업데이트해야 한다.
- 완료된 계획은 `.agentos/project/exec-plans/archive/` 로 이동한다.

## 2. 기타 벤더 특화 제약
- `AGENTS.md` Rule 6에 명시된 바와 같이 Claude Code 환경(Task 도구 사용 가능)에서는 자기검토(self-review) fallback이 허용되지 않는다. 반드시 다른 서브에이전트나 명시적인 검토 게이트를 통과해야 한다.
