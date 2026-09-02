# Worktree Safety

이 문서는 `git-worktree-parallel`의 generic safety SSOT다.
project-specific naming, ownership, base ref 운영 규칙은 각 프로젝트 overlay skill이 별도로 정의한다.

## Safety Checklist

worktree 생성/재사용/정리 전마다 아래를 먼저 확인한다:

```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git worktree list
```

## Create Rules

- 새 worktree는 새 목적이 있을 때만 만든다
- 같은 브랜치를 여러 worktree에 붙이는 시도는 피한다
- helper의 기본 경로는 ignored `<repo>/.agentos/worktrees/<branch-slug>`다. 이 directory가 symlink면 fail-closed한다
- `--path`를 명시한 경우에는 기존 호환대로 repo 밖 경로도 사용할 수 있지만, 존재하는 경로는 덮어쓰지 않는다
- 기존 경로가 존재하면 덮어쓰지 말고 먼저 상태를 확인한다
- 충돌이면 `git worktree list`로 확인한 뒤 새 `--branch`/`--path`를 선택하거나 기존 worktree를 명시적으로 재사용한다

## Cleanup Rules

- cleanup은 merge 성공 및 필요한 검증 이후에만 진행한다
- `git -C <path> status --short`가 비어 있지 않으면 즉시 삭제하지 않는다
- `git worktree remove` 전에 현재 브랜치와 변경 상태를 다시 확인한다
- 브랜치 삭제는 worktree 제거와 분리해서 다룬다
- focused regression의 runtime-created `/tmp/tmp.*` root만은 primary worktree 하나와 canonical-root 일치가 확인된 뒤 `rm -rf -- <temp-root>`로 정리할 수 있다. 이 test-only 예외는 project/worktree 경로에는 적용하지 않는다

## Never Do This By Default

- `git reset --hard`
- `git clean -fd`
- `git branch -D`
- `rm -rf <worktree-path>`
- 사용자가 요청하지 않은 `git push`
- 사용자가 요청하지 않은 `merge` / `rebase`

## Parallel Use Guidance

- 각 worktree에 역할을 하나만 부여한다
- 여러 worktree를 동시에 다루면 worktree별 목적과 브랜치 대응을 분명히 유지한다
- 여러 에이전트가 동시에 작업하면 각자 다른 worktree를 쓰게 한다
- 메인 checkout과 worktree가 같은 파일을 동시에 수정할 수 있으면 먼저 경고한다
- 통합은 대상 브랜치가 checkout된 checkout/worktree에서만 수행한다
- 종료 시에는 "정리만 할지", "브랜치까지 삭제할지"를 분리해서 확인한다
