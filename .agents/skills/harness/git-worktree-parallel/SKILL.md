---
name: git-worktree-parallel
description: >
  Use when the agent needs to create, reuse, inspect, or clean up a git worktree for isolated work that
  should not touch the current checkout. Treat this as an exception workflow for checkout protection,
  review branches, hotfixes, or bounded experiments, not as the default execution model.
---

# git-worktree-parallel

하네스의 canonical git worktree isolation workflow다.
기본 실행 모델은 단일 세션 + 단일 workspace이며, 이 skill은 main checkout 보존이나 예외적 격리가 필요할 때만 사용한다.

## When to Use

- 현재 checkout을 유지한 채 새 feature나 실험을 다른 디렉터리에서 시작할 때
- main checkout을 건드리지 않고 review, spike, hotfix를 격리해야 할 때
- 이미 별도 owner가 있는 worktree를 안전하게 재사용하거나 점검해야 할 때
- review, spike, hotfix를 별도 worktree로 분리할 때
- 종료된 worktree를 안전하게 정리해야 할 때

## When NOT to Use

- 단순 브랜치 전환만 필요할 때
- 단순 구현 작업을 기본 흐름으로 바로 수행할 수 있을 때
- 병렬 실행 자체를 정당화하기 위해 worktree를 먼저 도입하려 할 때
- 사용자가 파괴적 cleanup을 요청하지 않았는데 강제 삭제가 필요한 흐름일 때
- git 저장소가 아니거나 worktree 사용이 불가능한 상태일 때

## Read First

- generic safety SSOT는 [references/worktree-safety.md](references/worktree-safety.md)를 따른다
- 반복되는 생성 절차는 [scripts/create-worktree.sh](scripts/create-worktree.sh)를 우선 사용한다

## Core Workflow

### 1. Preflight

먼저 아래를 확인한다:

```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git worktree list
```

확인 포인트:
- 현재 저장소 루트
- 미커밋 변경 존재 여부
- 현재 기준 브랜치
- 기존 worktree 충돌 여부

미커밋 변경이 있으면 worktree 생성 전에 그대로 진행할지, commit/stash가 필요한지 명시적으로 정리한다.

### 2. Naming Rules

- worktree 디렉터리는 목적이 드러나게 짧게 짓는다
- 브랜치는 목적과 종류가 드러나게 짓는다
  - 예: `feature/<topic>`
  - 예: `spike/<topic>`
  - 예: `hotfix/<topic>`
- 같은 이름이 이미 있으면 재사용 여부를 먼저 확인하고 임의로 덮어쓰지 않는다

### 3. Create a New Worktree

기본 흐름:

```bash
git fetch origin
git worktree add -b <new-branch> <path> <base-ref>
```

base-ref가 불명확하면 현재 브랜치에서 이어갈지, 메인라인 기준으로 분기할지 먼저 확인한다.

반복 실수를 줄이려면 helper script를 우선 사용한다:

```bash
bash .agents/skills/harness/git-worktree-parallel/scripts/create-worktree.sh \
  --path <path> \
  --branch <new-branch> \
  --base <base-ref>
```

생성 후 바로 확인:

```bash
git -C <path> status --short
git -C <path> branch --show-current
git worktree list
```

### 4. Reuse or Enter an Existing Worktree

```bash
git worktree list
git -C <path> status --short
git -C <path> branch --show-current
```

다른 세션이나 에이전트가 이미 사용 중인 흔적이 있으면 사용자 결정 전까지 건드리지 않는다.

### 5. Isolation Rules

- 한 worktree = 한 브랜치 = 한 목적을 기본 규칙으로 둔다
- 서로 다른 실험을 같은 worktree에 섞지 않는다
- 병렬 실행은 예외다. 관측성과 ownership 계약이 없으면 worker 수를 늘리지 않는다
- cleanup은 worktree remove와 branch deletion을 분리해 다룬다
- worktree를 만든 뒤 즉시 다음 행동 하나를 제안한다

충돌 가능성이 높으면 아래를 먼저 보여준다:

```bash
git diff --name-only
git -C <path> diff --name-only
```

### 6. Worktree Tracking

여러 worktree를 동시에 운영할 때는 각 worktree마다 아래 항목을 섞지 않게 관리한다:

- `path`
- `branch`
- `base`
- `purpose`

최소 규칙:
- 새 worktree를 만들거나 재사용할 때 위 4가지를 바로 보고한다
- 다른 worktree로 이동해 작업을 이어갈 때도 같은 4가지를 다시 확인한다
- 같은 branch나 목적을 여러 worktree에 걸쳐 애매하게 나누지 않는다
- 기본값은 worktree 1개 추가까지다. 다중 worker 병렬 실행은 별도 운영 계약이 있을 때만 확장한다

### 7. Merge Back Workflow

개발 완료 후 통합이 필요하면 아래 순서를 따른다:

1. 대상 브랜치가 checkout된 checkout/worktree로 이동한다
2. 대상 브랜치를 최신 상태로 맞춘다
3. 사용자가 merge 방식을 지정하지 않으면 `merge`와 `rebase` 중 무엇을 원하는지 먼저 확인한다
4. 통합 후 필요한 검증을 실행한다
5. `push`는 사용자가 명시적으로 요청한 경우에만 다음 행동으로 제안한다

예시 확인 흐름:

```bash
git status --short
git branch --show-current
git pull --ff-only
git merge <feature-branch>
```

### 8. Done / Cleanup After Merge

정리 전에는 반드시 아래를 확인한다:

```bash
git -C <path> status --short
git -C <path> branch --show-current
git worktree list
```

규칙:
- 검증이 끝나기 전에는 cleanup으로 넘어가지 않는다
- merge 완료 후에만 worktree 제거를 진행한다
- 미커밋 변경이 있으면 바로 삭제하지 않는다
- 브랜치 삭제는 사용자가 명시적으로 원할 때만 수행한다
- 안전한 기본값은 status를 보여주고 확인받는 것이다

worktree만 제거할 때:

```bash
git worktree remove <path>
```

## Report Back

항상 아래를 짧게 보고한다:
- 기준 브랜치
- 생성 또는 사용한 worktree 경로
- 연결된 브랜치 이름
- 기준 base ref
- 현재 목적 (`purpose`)
- 현재 변경 상태 (`clean` 또는 modified)
- 다음 추천 행동 1개
