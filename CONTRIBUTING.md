# 프로젝트 기여 가이드라인 (CONTRIBUTING)

AgentOS 프로젝트에 기여해 주셔서 감사합니다! 이 문서는 프로젝트의 안정성을 유지하면서 효과적으로 협업하기 위한 규칙을 안내합니다.

## 🌿 기본 기여 원칙 (Basic Guidelines)

Create a feature branch, run the focused test and public suite, run the public
boundary verifier, then open a pull request. Do not add profiles, runtime data,
credentials, host paths, or private operational documents. Failed checks are
safe to rerun after a fix.

## 🚀 브랜칭 및 PR 전략 (`main` 브랜치 보호)

우리 프로젝트는 **안정적인 `main` 브랜치 유지**를 최우선으로 합니다.

1. **`main` 직접 푸시 금지**: `main` 브랜치에는 언제나 배포 가능하고 안정적인 코드만 유지되어야 합니다. 직접적인 푸시는 금지됩니다.
2. **이슈(Issue) 생성**: 작업 시작 전, 먼저 GitHub Issue를 생성하여 논의를 시작하는 것을 권장합니다.
3. **기능 브랜치 생성 및 작업**: 새로운 기능 추가나 계획 수립 시 반드시 새로운 브랜치를 생성하세요. (예: `feature/새-기능`, `bugfix/버그`)
4. **Pull Request (PR) 제출**: 작업 완료 후 `main` 브랜치를 향해 PR을 제출합니다. 제출 시 프로젝트의 **PR 템플릿**에 맞춰 구현 계획과 변경 사항을 명확히 작성해 주세요.
5. **리뷰 및 자동화 검증**: 다른 기여자의 리뷰를 받고 모든 상태 검사(CI)가 통과해야만 병합할 수 있습니다.
