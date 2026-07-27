# AgentOS Observability 설정 가이드

AgentOS는 백그라운드 태스크와 CLI 런타임 이벤트(상태 변경, 타임아웃, 예외 발생 등)를 외부 대시보드와 연동할 수 있는 내장 플러그인(Observability Notifier)을 제공합니다. 

현재 GitHub Projects 어댑터를 내장 지원합니다.

## GitHub Projects 연동 설정

GitHub Projects **v2**(GraphQL 기반) 연동을 위해서는 아래 4개의 환경 변수를 설정해야 합니다. GitHub이 Classic Projects REST API를 신규 계정/리포에서 은퇴시켰기 때문에, Classic Projects는 지원하지 않습니다.

1. `OBSERVABILITY_ENABLED`: 알림 기능을 활성화하려면 `1`로 설정합니다.
2. `GITHUB_TOKEN`: `project` scope가 있는 GitHub Personal Access Token (Classic 또는 Fine-grained). `gh auth refresh -s project`로 스코프를 추가할 수 있습니다.
3. `OBSERVABILITY_GITHUB_OWNER`: Projects v2 보드 소유자의 GitHub 로그인 (예: `gabrielwithappy`)
4. `OBSERVABILITY_GITHUB_PROJECT_NUMBER`: 대상 Projects v2 보드의 프로젝트 번호 (예: `6` — 보드 URL `https://github.com/users/<owner>/projects/<number>`의 숫자, 또는 `gh project list --owner <owner>`로 확인)

대상 보드에는 `Status` 단일 선택 필드가 있어야 하며, `Todo` / `In Progress` / `Done` 옵션이 있으면 이벤트 종류에 따라 자동으로 매핑됩니다. 옵션이 없으면 상태 갱신은 건너뛰고 draft item 생성만 됩니다.

## `agentos dashboard sync-plan` — exec-plan 문서 동기화

런타임 이벤트 알림과 별개로, `.agentos/project/exec-plans/` 아래의 exec-plan 문서를 GitHub Projects v2 보드 카드로 직접 동기화하는 커맨드도 제공합니다.

```bash
# 파일 하나만 동기화
agentos dashboard sync-plan <exec-plan-file> --owner <owner> --project-number <번호>

# active/ 디렉토리 전체를 한 번에 동기화
agentos dashboard sync-plan --all --owner <owner> --project-number <번호>
```

### Status 컬럼 6종 — 용도 분리

exec-plan 동기화는 런타임 이벤트와 **다른 5단계**로 Status를 매핑하므로, 대상 보드의 Status 필드에는 최종적으로 6개 옵션이 있어야 합니다:

| 옵션 | 용도 | 판단 조건 | 사용 주체 |
|---|---|---|---|
| `Todo` | 런타임 이벤트(`CLI_INTERRUPT` 등) 전용 | — | `OBSERVABILITY_ENABLED=1` 알림 경로만 사용, exec-plan 동기화는 이 옵션을 쓰지 않음 |
| `Backlog` | exec-plan이 아직 Gate 2 리뷰를 통과하지 못함 | `reviewed: false` | `sync-plan` 전용 |
| `Ready` | Gate 2 리뷰는 통과했지만 아직 "완료"로 표시되지 않음 | `reviewed: true` + 주 상태 문구에 "완료" 없음 | `sync-plan` 전용 |
| `In Progress` | 구현이 진행 중이며 자동 검증도 아직 안 끝남 | `reviewed: true` + "완료" 포함하지만 "완료"로 시작 안 함 + `"사용자 실사용 확인 대기"` 문구 없음(예: "구현 완료") | `sync-plan` 전용 |
| `Awaiting Verification` | 구현·자동 검증은 끝났고 사람의 수동 확인(브라우저 로그인, 실제 보드 조회 등)만 남음 | `reviewed: true` + "완료" 포함하지만 "완료"로 시작 안 함 + 상태 문구에 정확한 부분 문자열 `"사용자 실사용 확인 대기"` 포함(예: "구현 및 전체 검증 완료 (사용자 실사용 확인 대기)") | `sync-plan` 전용 |
| `Done` | 계획 문서 상태가 "완료"로 시작 | 주 상태 문구가 "완료"로 시작 | `sync-plan` 전용, 런타임 이벤트도 일부 공유 |

새 보드를 만들었다면 기본으로 Todo/In Progress/Done 3개만 있으므로, `Backlog`/`Ready`/`Awaiting Verification` 옵션을 웹 UI(Project 설정 → Status 필드 → 옵션 추가)나 `gh api graphql`의 `updateProjectV2Field` mutation으로 추가해야 `sync-plan`이 이 단계들을 정확히 반영할 수 있습니다. 옵션이 없는 상태에서 `sync-plan`을 실행하면 카드는 생성/갱신되지만 Status는 바뀌지 않고, 콘솔에 `Status option '...' not found on board` 경고가 뜹니다(카드가 만들어졌는데 상태가 안 바뀌어서 성공했다고 착각하지 않도록).

`Awaiting Verification` 판단은 exec-plan 파일에 새 메타 필드를 추가하지 않고, 계획 작성자가 상태 문구에 붙이는 관용구(`"(사용자 실사용 확인 대기)"`)를 그대로 재해석합니다 — TEMPLATE.md에 이 관용구 사용 안내가 있습니다.

**주의**: 기존 Status 옵션 목록을 `updateProjectV2Field`로 통째로 교체하면(옵션 추가 시 GitHub API가 이렇게 동작합니다) 이미 카드에 설정된 Status 값이 초기화됩니다. 옵션을 추가한 직후에는 `sync-plan --all`을 한 번 더 실행해 모든 카드의 Status를 다시 채워 넣으세요.

### 1. 대화형 마법사 (추천)
단순히 `OBSERVABILITY_ENABLED=1` 환경변수만 설정하고 `agentos` 명령어를 실행하면, **대화형 마법사(Interactive Wizard)**가 나타나 필요한 정보를 물어보고 자동으로 현재 디렉토리의 `.env` 파일에 설정해 줍니다. 

또한 터미널에 `gh auth login`이 되어있다면, `GITHUB_TOKEN`은 백그라운드에서 자동으로 가져오므로 일일이 발급받아 입력할 필요가 없습니다!

```bash
export OBSERVABILITY_ENABLED=1
agentos run
```
*(실행 시 `OBSERVABILITY_GITHUB_OWNER`와 `OBSERVABILITY_GITHUB_PROJECT_NUMBER`를 물어보고 자동 저장합니다.)*

### 2. 수동 설정 (환경 변수 또는 `.env` 파일)
직접 `.env` 파일에 기록하거나 환경 변수로 다음과 같이 지정할 수도 있습니다.
```bash
export OBSERVABILITY_ENABLED=1
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE" # (gh auth가 설정된 경우 생략 가능)
export OBSERVABILITY_GITHUB_OWNER="gabrielwithappy"
export OBSERVABILITY_GITHUB_PROJECT_NUMBER="6"
```

## 자동 복구 (Self-healing)

`.env` 파일이 실수로 지워지거나 새 환경에서 프로젝트를 클론받은 경우에도, `agentos run` 실행 시 대화형 마법사가 뜨기 전에 `gh` CLI 인증 정보를 바탕으로 프로젝트 이름이 `AgentOS:`로 시작하는 프로젝트를 찾아내어 자동으로 설정 복구를 수행합니다. 이를 통해 설정 번거로움과 오류가 대폭 줄어듭니다. 만약 자동 탐지에 실패하더라도 기존의 수동 대화형 마법사가 호출되어 복구를 진행할 수 있습니다.

## 에러 복구(Error Recovery) 메커니즘
네트워크 단절이나 토큰 만료(401) 등 통신에 실패하더라도 AgentOS 메인 프로세스는 절대 중단되지 않습니다. 실패 시엔 CLI 콘솔과 `agentos.log`에 `[Observability Warning]` 경고 메시지만 출력됩니다.
