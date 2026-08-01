# AgentOS Observability 설정 가이드

AgentOS는 백그라운드 태스크와 CLI 런타임 이벤트(상태 변경, 타임아웃, 예외 발생 등)를 외부 대시보드와 연동할 수 있는 내장 플러그인(Observability Notifier)을 제공합니다. 

현재 GitHub Projects 어댑터를 내장 지원합니다.

## GitHub Projects 연동 설정

GitHub Projects **v2**(GraphQL 기반) 연동을 위해서는 아래 4개의 환경 변수를 설정해야 합니다. GitHub이 Classic Projects REST API를 신규 계정/리포에서 은퇴시켰기 때문에, Classic Projects는 지원하지 않습니다.

1. `OBSERVABILITY_ENABLED`: 알림 기능을 활성화하려면 `1`로 설정합니다.
2. `GITHUB_TOKEN`: `project` 및 `read:project` scope가 포함된 GitHub Personal Access Token 또는 GitHub CLI 인증. GitHub CLI를 새로 로그인하거나 권한을 추가할 때 처음부터 `gh auth login -s project,read:project` 또는 `gh auth refresh -s project,read:project`를 실행하여 프로젝트 관리 권한을 부여하세요.
3. `OBSERVABILITY_GITHUB_OWNER`: Projects v2 보드 소유자의 GitHub 로그인 (예: `gabrielwithappy`)
4. `OBSERVABILITY_GITHUB_PROJECT_NUMBER`: 대상 Projects v2 보드의 프로젝트 번호 (예: `6` — 보드 URL `https://github.com/users/<owner>/projects/<number>`의 숫자, 또는 `gh project list --owner <owner>`로 확인)

대상 보드에는 `Status` 단일 선택 필드가 있어야 하며, `Todo` / `In Progress` / `Done` 옵션이 있으면 이벤트 종류에 따라 자동으로 매핑됩니다. 옵션이 없으면 상태 갱신은 건너뛰고 draft item 생성만 됩니다.

### 추천하는 Project 보드 이름 (Naming Convention)

GitHub에서 새 Project를 생성하실 때, 직관적인 관리를 위해 다음과 같은 명명 규칙을 권장합니다:
* **`AgentOS Observability - [프로젝트/리포지토리명]`**
  * 예시: `AgentOS Observability - agentos`
* 이렇게 생성해 두시면 여러 프로젝트를 관리할 때 런타임 이벤트와 실행 계획이 어디에 연동되는지 쉽게 식별할 수 있습니다.

## `agentos dashboard sync-plan` — exec-plan 문서 동기화

런타임 이벤트 알림과 별개로, `.agentos/project/exec-plans/` 아래의 exec-plan 문서를 GitHub Projects v2 보드 카드로 직접 동기화하는 커맨드도 제공합니다.

```bash
# 파일 하나만 동기화
agentos dashboard sync-plan <exec-plan-file> --owner <owner> --project-number <번호>

# active/ 디렉토리 전체를 한 번에 동기화
agentos dashboard sync-plan --all --owner <owner> --project-number <번호>

# 커스텀 설정 파일 또는 등록된 어댑터 기반 동기화
agentos dashboard sync-plan --all --config <config-file-path>
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

## 계획 문서 저장 시 자동 동기화

`.claude`/`.codex`/`.gemini` 중 어느 벤더에서 `active/` 하위 계획 파일을 Edit/Write해도 PostToolUse 훅이 자동으로 `sync-plan --all`을 시도합니다.
- **전제조건**: `OBSERVABILITY_ENABLED=1`(`.env` 또는 셸 환경변수 둘 다 인식).
- **보드가 안 바뀔 때 확인할 것**: 
  1. `~/.agentos/logs/agentos.log`에서 `[Observability Warning] 자동 dashboard sync-plan 실패` 검색
  2. 위 기존 `## agentos dashboard sync-plan` 섹션의 수동 명령 `agentos dashboard sync-plan --all`로 즉시 재시도 (자동 동기화가 막혀도 수동 경로는 항상 열려 있습니다).
- 자동 동기화는 fail-open으로 동작하므로, 동기화에 실패해도 파일 편집 자체를 막지 않습니다.
## agentos dashboard pull-plan — 보드 Status 되읽기

목적: 사람이 보드에서 드래그한 카드 Status를 로컬 계획 문서로 되읽어옵니다(관찰용).
이 기능은 카드의 Status만 확인하며, 계획 문서의 공식 `> **상태:**`나 `reviewed:` 필드를 **절대 자동으로 변경하지 않습니다**.
댓글/라벨 읽기, 웹훅 기반 실시간 반영, 자동 Gate 2 승인은 이 범위에 없습니다.

사용 예:
```bash
agentos dashboard pull-plan <exec-plan-file>
agentos dashboard pull-plan --all
```

명령을 실행하면 파일 헤더에 아래 두 가지 메타 필드가 추가/갱신됩니다:
- `remote_board_status`: 마지막으로 확인한 원격 Status 값
- `remote_board_synced_at`: 마지막 pull 시각 (UTC)

### 실패 시 동작 (Error Recovery)
`pull-plan` 실행 시 발생할 수 있는 4가지 문제 상황과 다음 행동(해결책)입니다. 실패하더라도 프로세스가 중단되거나 문서가 손상되지 않습니다:

| 콘솔 메시지 | 원인 및 다음 행동 |
|---|---|
| `dashboard_item_id가 없습니다` | 보드에 연동된 카드가 없습니다. 먼저 `sync-plan`을 실행해 카드를 생성하세요. |
| `원격 상태 조회 실패` | 네트워크 오류이거나 인증 토큰 만료. 인터넷 연결 및 `GITHUB_TOKEN`을 확인하세요. |
| `보드에서 Status 값을 찾지 못했습니다` | 카드가 삭제되었거나, Status 필드가 비어 있습니다. 보드에서 카드를 확인하세요. |
| `대시보드가 설정되어 있지 않아...` | `.env`나 셸 환경변수, 또는 `--config`가 누락되었습니다. 설정을 확인하세요. |

### 1. 대시보드 설정 마법사 (추천)
단순히 `OBSERVABILITY_ENABLED=1` 환경변수만 설정하고 `agentos` 명령어를 실행하면, **대화형 마법사(Interactive Wizard)**가 나타나 필요한 정보를 물어보고 자동으로 현재 디렉토리의 `.env` 파일에 설정해 줍니다. 

또한 터미널에 `gh auth login -s project,read:project` (또는 기존 인증 상태에서 `gh auth refresh -s project,read:project`)로 프로젝트 관리 권한이 미리 부여되어 있다면, `GITHUB_TOKEN`은 백그라운드에서 자동으로 가져오므로 일일이 발급받아 입력할 필요가 없습니다!

```bash
# 처음 로그인 시 프로젝트 관리 권한 포함
gh auth login -s project,read:project

# 또는 기존 로그인에 프로젝트 권한 추가
gh auth refresh -s project,read:project

export OBSERVABILITY_ENABLED=1
agentos run
```
*(실행 시 `OBSERVABILITY_GITHUB_OWNER`와 `OBSERVABILITY_GITHUB_PROJECT_NUMBER`를 물어보고 자동 저장합니다.)*

### 2. 수동 설정 (환경 변수 또는 `.env` 파일)
직접 `.env` 파일에 기록하거나 환경 변수로 다음과 같이 지정할 수도 있습니다.
```bash
export OBSERVABILITY_ENABLED=1
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE" # (gh auth -s project,read:project 설정 시 생략 가능)
export OBSERVABILITY_GITHUB_OWNER="gabrielwithappy"
export OBSERVABILITY_GITHUB_PROJECT_NUMBER="6"
```

## 자동 복구 (Self-healing)

`.env` 파일이 실수로 지워지거나 새 환경에서 프로젝트를 클론받은 경우에도, `agentos run` 실행 시 대화형 마법사가 뜨기 전에 `gh` CLI 인증 정보를 바탕으로 프로젝트 이름이 `AgentOS:`로 시작하는 프로젝트를 찾아내어 자동으로 설정 복구를 수행합니다. 이를 통해 설정 번거로움과 오류가 대폭 줄어듭니다. 만약 자동 탐지에 실패하더라도 기존의 수동 대화형 마법사가 호출되어 복구를 진행할 수 있습니다.

## 에러 복구(Error Recovery) 메커니즘
네트워크 단절이나 토큰 만료(401) 등 통신에 실패하더라도 AgentOS 메인 프로세스는 절대 중단되지 않습니다. 실패 시엔 CLI 콘솔과 `agentos.log`에 `[Observability Warning]` 경고 메시지만 출력됩니다.
수동 동기화(`agentos dashboard sync-plan`) 도중 어댑터에서 오류가 발생하더라도 계획 실행 흐름을 차단하지 않으며, 아래와 같은 형태의 non-blocking 경고 메시지만 출력됩니다.
```
[WARNING] GitHub Dashboard sync 실패: <오류 요약>.
수동 재동기화: agentos dashboard sync-plan <plan-path>
```

## 옵저버빌리티 이벤트 기반 아키텍처

AgentOS의 대시보드 동기화는 이벤트 기반(Event-driven) 아키텍처로 동작합니다.
- `PLAN_STATUS_CHANGED`, `PLAN_WRITING_STARTED` 등 단일 이벤트가 발생하면, 등록된 **여러 어댑터로 팬아웃(Fan-out)**됩니다.
- GitHub이 아닌 **새로운 대시보드(예: Linear, Jira) 연동을 추가**하려면, `DashboardAdapter` 프로토콜을 구현하는 새 클래스를 만들고 `send_notification(payload)` 메서드만 구현하면 됩니다. 코어 CLI 로직이나 이벤트 발송 코드를 수정할 필요가 없습니다.
- 대시보드 환경변수가 설정되어 있지 않으면 어댑터가 0개 등록되므로, 모든 알림 전송 호출은 **지연이나 에러 없이 즉시 안전하게 통과(no-op)**합니다. 따라서 대시보드를 사용하지 않는 환경에서도 AgentOS 런타임 성능 저하나 실패 위험이 없습니다.

### `PLAN_WRITING_STARTED` 이벤트
에이전트가 계획 작성(`writing-plans`)을 시작하는 즉시 발생하는 이벤트입니다.
- **발생 시점:** 계획 문서 파일이 생성되거나 제목이 확정된 직후
- **Payload 필드:** `user_request`(사용자 요청 요약), `agent`, `session`, `plan_path`, `plan_title`
- **동작:** 즉시 카드를 생성하고 상태를 `Backlog`로 강제 설정합니다. 본문에는 에이전트 정보와 사용자의 요청 문맥이 포함됩니다.
- **`user_request` 활용:** 계획 문서 헤더 영역에 `> user_request: <요청 요약 1-2문장>` 메타 필드를 기록하면 대시보드 카드의 `## 사용자 요청` 섹션에 반영되어 어떤 의도로 작성 중인 계획인지 대시보드에서 바로 파악할 수 있습니다.
- **명시적 비목표:** Gate 2 리뷰를 통과하지 못해 계획이 폐기될 경우, 이미 대시보드에 발행된 "작성 중" (Backlog) 고아 카드를 시스템이 자동으로 찾아 지워주지 않습니다. 이 카드는 사용자가 대시보드에서 직접 삭제해야 합니다.
