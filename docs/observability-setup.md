# AgentOS Observability 설정 가이드

AgentOS는 백그라운드 태스크와 CLI 런타임 이벤트(상태 변경, 타임아웃, 예외 발생 등)를 외부 대시보드와 연동할 수 있는 내장 플러그인(Observability Notifier)을 제공합니다. 

현재 GitHub Projects 어댑터를 내장 지원합니다.

## GitHub Projects 연동 설정

GitHub Projects (Classic 또는 New) 연동을 위해서는 아래 4개의 환경 변수를 설정해야 합니다.

1. `OBSERVABILITY_ENABLED`: 알림 기능을 활성화하려면 `1`로 설정합니다.
2. `GITHUB_TOKEN`: 권한이 있는 GitHub Personal Access Token (Classic 또는 Fine-grained).
3. `OBSERVABILITY_GITHUB_REPO`: 대상 레포지토리 (예: `gabrielwithappy/agentos`)
4. `OBSERVABILITY_GITHUB_PROJECT_ID`: 이벤트를 전송할 GitHub Project ID

### 환경 변수 설정 예시
```bash
export OBSERVABILITY_ENABLED=1
export GITHUB_TOKEN="ghp_your_token_here"
export OBSERVABILITY_GITHUB_REPO="gabrielwithappy/agentos"
export OBSERVABILITY_GITHUB_PROJECT_ID="1"
```

## 에러 복구(Error Recovery) 메커니즘
네트워크 단절이나 토큰 만료(401) 등 통신에 실패하더라도 AgentOS 메인 프로세스는 절대 중단되지 않습니다. 실패 시엔 CLI 콘솔과 `agentos.log`에 `[Observability Warning]` 경고 메시지만 출력됩니다.
