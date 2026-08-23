---
status: 완료
date: 2026-08-23
reviewed: true
usability_review_required: true
user_request: 로컬 docs/knowledge 데이터를 knowledge-agent GitHub 저장소에 병합하고, 이후 knowledge-agent를 단일 원격 저장소로 사용한다.
active_agent: codex
active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agentos/worktrees/feature-knowledge-agent-remote-only
dashboard_item_id:
implementation_started_at: 2026-08-23T03:32:07Z
implementation_completed_at: 2026-08-23T03:52:05Z
implementation_duration: 19m 58s
---

# Knowledge Agent 단일 원격 이관 구현 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- AgentOS의 로컬 `docs/knowledge` 운영 문서를 `knowledge-agent` 저장소에 병합하고, 앞으로 지식 관리의 canonical 위치를 `https://github.com/gabrielwithappy/knowledge-agent`로 정리한다.

**사용자 결과 요약:**
- 사용자는 새 장기지식을 `knowledge-agent` 저장소에 추가한다. AgentOS의 `docs/knowledge`는 `pointer-only` 안내 표면으로 남아 새 저장소 위치와 검증 절차만 알려준다.

## 의존성 분석

- 외부 의존성: GitHub repository `gabrielwithappy/knowledge-agent`, SSH push 권한
- 검증된 상태: `/tmp/knowledge-agent` is clean on `main...origin/main`
- 현재 AgentOS checkout: isolated worktree `feature/knowledge-agent-remote-only` with only allowed plan-trace changes before implementation

## 장기 적용 표면

- Traceability Surface: this plan, Intent Sheet, `HISTORY.md`, `.agentos/project/exec-plans/README.md`
- Durable Result Surface: `https://github.com/gabrielwithappy/knowledge-agent`, `docs/knowledge/README.md`, `docs/knowledge/index.md`, `.agentos/project/00-project-index.md`

## AgentOS allowed-change list

- `.agentos/project/exec-plans/active/2026-08-23-knowledge-agent-remote-only.md`
- `.agentos/project/exec-plans/archive/reference/intent/intent-20260823-knowledge-agent-remote-only.md`
- `.agentos/project/exec-plans/README.md` (only via `plan_lifecycle.py refresh`)
- `.agents/traces/reviews/2026-08-23-knowledge-agent-remote-only/plan-reviewer.md`
- `.agents/traces/reviews/2026-08-23-knowledge-agent-remote-only/principle-auditor.md`
- `.agents/traces/reviews/2026-08-23-knowledge-agent-remote-only/usability-reviewer.md`
- `docs/knowledge/README.md`
- `docs/knowledge/index.md`
- `.agentos/project/00-project-index.md`
- `HISTORY.md`

No AgentOS runtime, command, test, or `catalog/skills/knowledge-curator/**` file may change in this plan. Existing `.gitkeep` files under `docs/knowledge/**` remain untouched.

## 아키텍처

- `/tmp/knowledge-agent`를 독립 Git checkout으로 사용한다.
- AgentOS `docs/knowledge/README.md`와 `docs/knowledge/index.md` 내용을 새 OKF concept `concepts/agentos-knowledge-lifecycle.md`로 흡수한다.
- `knowledge-agent`에서는 `concepts/index.md`와 `log.md`만 갱신한다.
- Existing `knowledge-agent` files are preserved. No deletion, rename, force push, stash, reset, or history rewrite is allowed.

## 기술 스택

- Git, Markdown, knowledge-curator standalone CLI

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현과 원격 push 완료 |
| 완료됨 | 원격 접근 확인, isolated worktree 준비, 이관 범위 고정, Gate 2 PASS, knowledge-agent push |
| 현재 위치 | 최종 검증 완료 |
| 다음 단계 | 사용자 검토 후 AgentOS branch commit/push 결정 |
| 완료 신호 | `knowledge-agent` main에 이관 문서가 push되고 AgentOS docs가 pointer-only 안내로 바뀜 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 원격 저장소에 AgentOS knowledge 운영 문서 흡수 | `knowledge-agent`에서 AgentOS knowledge lifecycle을 확인할 수 있음 | `/tmp/knowledge-agent/concepts/agentos-knowledge-lifecycle.md`, `/tmp/knowledge-agent/concepts/index.md`, `/tmp/knowledge-agent/log.md` | `test "$(git -C /tmp/knowledge-agent status --short)" = "$(printf ' M concepts/index.md\n M log.md\n?? concepts/agentos-knowledge-lifecycle.md')"` / Expected: exit 0 before commit |
| 2. OKF 검증 | 원격 지식 번들이 구조적으로 유효함 | `/tmp/knowledge-agent` | `python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent` / Expected: `"ok": true` |
| 3. 원격 커밋 생성 | 원격 저장소 이관 변경이 하나의 로컬 커밋으로 고정됨 | `/tmp/knowledge-agent` Git history | `git -C /tmp/knowledge-agent add concepts/agentos-knowledge-lifecycle.md concepts/index.md log.md && git -C /tmp/knowledge-agent commit -m "Add AgentOS knowledge lifecycle"` / Expected: exit 0 |
| 4. 원격 main publish | GitHub `knowledge-agent` main이 새 커밋을 포함함 | `git@github.com:gabrielwithappy/knowledge-agent.git` | `git -C /tmp/knowledge-agent fetch origin main:refs/remotes/origin/main && test "$(git -C /tmp/knowledge-agent branch --show-current)" = "main" && test "$(git -C /tmp/knowledge-agent status --short)" = "" && BEFORE=$(git -C /tmp/knowledge-agent rev-parse origin/main) && AFTER=$(git -C /tmp/knowledge-agent rev-parse HEAD) && test "$BEFORE" != "$AFTER" && test "$(git -C /tmp/knowledge-agent diff --name-status origin/main...HEAD)" = "$(printf 'A\tconcepts/agentos-knowledge-lifecycle.md\nM\tconcepts/index.md\nM\tlog.md')" && git -C /tmp/knowledge-agent push origin main && git -C /tmp/knowledge-agent fetch origin main:refs/remotes/origin/main && test "$(git -C /tmp/knowledge-agent rev-parse HEAD)" = "$(git -C /tmp/knowledge-agent rev-parse origin/main)"` / Expected: exit 0 |
| 5. AgentOS pointer docs 정리 | 사용자가 더 이상 로컬 `docs/knowledge`에 새 지식을 쓰지 않음 | `docs/knowledge/README.md`, `docs/knowledge/index.md`, `.agentos/project/00-project-index.md` | `rg -q "https://github.com/gabrielwithappy/knowledge-agent" docs/knowledge/README.md && rg -q "pointer-only" docs/knowledge/README.md && rg -q "Do not add new knowledge notes here" docs/knowledge/README.md && rg -q "git clone git@github.com:gabrielwithappy/knowledge-agent.git" docs/knowledge/README.md && rg -q "pointer-only" docs/knowledge/index.md && rg -q "knowledge-agent" docs/knowledge/index.md && rg -q "pointer-only" .agentos/project/00-project-index.md && rg -q "knowledge-agent" .agentos/project/00-project-index.md && ! rg -n 'Put drafts in docs/knowledge/inbox|agentos knowledge search|agentos knowledge context' docs/knowledge .agentos/project/00-project-index.md` / Expected: exit 0 |
| 6. AgentOS 범위 검증 | 이관 외 변경이 섞이지 않음 | AgentOS isolated worktree | `test "$(git status --short | sed 's/^...//' | sort)" = "$(printf '.agentos/project/exec-plans/README.md\n.agentos/project/exec-plans/active/2026-08-23-knowledge-agent-remote-only.md\n.agentos/project/exec-plans/archive/reference/intent/intent-20260823-knowledge-agent-remote-only.md\n.agents/traces/reviews/2026-08-23-knowledge-agent-remote-only/plan-reviewer.md\n.agents/traces/reviews/2026-08-23-knowledge-agent-remote-only/principle-auditor.md\n.agents/traces/reviews/2026-08-23-knowledge-agent-remote-only/usability-reviewer.md\n.agentos/project/00-project-index.md\ndocs/knowledge/README.md\ndocs/knowledge/index.md\nHISTORY.md' | sort)"` / Expected: exit 0 |

## 리뷰 반영 이력

- Initial attempt in the main checkout was blocked because unrelated runtime-removal changes were present.
- This plan uses an isolated worktree and explicitly excludes AgentOS runtime/test deletion.
- Gate 2 PASS: plan-reviewer PASS, principle-auditor PASS/CLEAN, usability-reviewer PASS.

## 계획된 사용 방법

After migration, add new knowledge in the canonical repository:

```bash
git clone git@github.com:gabrielwithappy/knowledge-agent.git
cd knowledge-agent
python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project "$PWD"
```

Before publishing a knowledge edit:

```bash
python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project "$PWD"
git diff --name-status origin/main...HEAD
git status --short
git add <markdown-files>
git commit -m "Add knowledge note"
git push origin main
```

Do not add new knowledge notes in AgentOS `docs/knowledge`; it is pointer-only after this migration.

## 복구 경로

| 증상 | 원인 | 안전한 다음 행동 | 명령 |
|---|---|---|---|
| push rejected | 원격 main이 먼저 바뀜 | fetch 후 일반 merge를 시도하고, 충돌이 없을 때만 validate와 push를 다시 실행 | `git -C /tmp/knowledge-agent fetch origin main:refs/remotes/origin/main && git -C /tmp/knowledge-agent merge --no-edit origin/main && python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent && git -C /tmp/knowledge-agent push origin main && git -C /tmp/knowledge-agent fetch origin main:refs/remotes/origin/main && test "$(git -C /tmp/knowledge-agent rev-parse HEAD)" = "$(git -C /tmp/knowledge-agent rev-parse origin/main)"` |
| validation failed | OKF frontmatter 또는 index link 누락 | JSON diagnostics의 `next`를 따른 뒤 재검증 | `python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent` |
| unexpected remote diff | 이관 범위 밖 파일 변경 | push 중단, diff 확인 | `git -C /tmp/knowledge-agent diff --name-status origin/main...HEAD` |
| AgentOS pointer docs stale | 로컬 authoring 안내가 남아 있음 | pointer-only 문구와 canonical URL 확인 | `rg -n "Put drafts|agentos knowledge|knowledge-agent|pointer-only" docs/knowledge .agentos/project/00-project-index.md` |
| credential prompt on HTTPS | HTTPS 자격 증명 없음 | SSH remote를 사용 | `git -C /tmp/knowledge-agent remote set-url origin git@github.com:gabrielwithappy/knowledge-agent.git` |

## 구현 결과

`knowledge-agent` 저장소 main에 AgentOS knowledge lifecycle 문서를 추가했다.

- Remote commit: `a06745d Add AgentOS knowledge lifecycle`
- Added: `concepts/agentos-knowledge-lifecycle.md`
- Updated: `concepts/index.md`
- Updated: `log.md`

AgentOS 쪽은 런타임이나 테스트를 삭제하지 않고, `docs/knowledge/README.md`, `docs/knowledge/index.md`, `.agentos/project/00-project-index.md`만 `knowledge-agent` canonical repository를 가리키는 pointer-only 안내로 바꿨다.

## 완료 증거

- `knowledge-agent` push: `7a20eac..a06745d main -> main`
- OKF validation: JSON result includes `"ok": true`
- Remote post-push verification: `/tmp/knowledge-agent` `HEAD == origin/main`

## 아카이브 결정

사용자 검토 및 PR/병합 결정 전까지 active에 유지한다.
