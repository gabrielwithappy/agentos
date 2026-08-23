---
status: 리뷰 대기
date: 2026-08-23
reviewed: false
usability_review_required: true
user_request: 로컬 docs/knowledge 데이터를 knowledge-agent GitHub 저장소에 병합하고, 이후 knowledge-agent를 단일 원격 저장소로 사용한다.
active_agent: codex
active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: feature/knowledge-agent-migration)
dashboard_item_id:
implementation_started_at:
implementation_completed_at:
implementation_duration:
---

# Knowledge Agent 원격 이관 구현 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- AgentOS의 로컬 `docs/knowledge` 데이터를 `knowledge-agent` 저장소에 병합하고, 앞으로 지식 관리의 canonical 위치를 `https://github.com/gabrielwithappy/knowledge-agent`로 정리한다.

**사용자 결과 요약:**
- 사용자는 장기 지식을 AgentOS 저장소 내부가 아니라 `knowledge-agent` 저장소에서 관리한다. AgentOS 문서는 새 위치를 안내하며, 기존 `knowledge-agent`의 OKF 문서들은 보존된다. 로컬 `docs/knowledge`는 새 지식을 작성하는 canonical 저장소가 아니라 pointer-only 안내 표면이다.

**의존성 분석:**
- 외부 의존성: GitHub repository `gabrielwithappy/knowledge-agent`, SSH push 권한
- 검증된 상태: `git@github.com:gabrielwithappy/knowledge-agent.git`의 `main` branch 접근 가능

**장기 적용 표면:**
- Traceability Surface: 이 active plan, `HISTORY.md`, `.agentos/project/exec-plans/README.md`
- Durable Result Surface: `https://github.com/gabrielwithappy/knowledge-agent`, AgentOS `docs/knowledge` 안내 문서, `.agentos/project/00-project-index.md`

**AgentOS allowed-change list:**
- `.agentos/project/exec-plans/active/2026-08-23-knowledge-agent-remote-migration.md`
- `.agentos/project/exec-plans/archive/reference/intent/intent-20260823-knowledge-agent-remote-migration.md`
- `.agentos/project/exec-plans/README.md` (only via `plan_lifecycle.py refresh`)
- `docs/knowledge/README.md`
- `docs/knowledge/index.md`
- `.agentos/project/00-project-index.md`
- `HISTORY.md`
- No other AgentOS files may change in this plan. Tracked `.gitkeep` files under `docs/knowledge/**` stay untouched unless a separate explicit user request approves their removal.

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기

**아키텍처:**
- `/tmp/knowledge-agent`를 독립 Git checkout으로 사용해 원격 저장소에 직접 병합 커밋을 만든다. AgentOS 저장소에는 지식 원문을 계속 확장하지 않고, `docs/knowledge`와 프로젝트 인덱스가 새 canonical repository를 가리키도록 정리한다.
- 이관 파일 범위는 현재 AgentOS `docs/knowledge/README.md`와 `docs/knowledge/index.md`의 운영 정보를 `knowledge-agent`의 OKF v0.2 concept 문서로 흡수하는 것이다. `.gitkeep` 파일은 내용 없는 디렉터리 placeholder라 원격 지식 문서로 옮기지 않는다.
- `knowledge-agent` 기존 파일은 삭제하지 않는다. `git diff --name-status origin/main...HEAD`에서 `D` 행이 나오면 push 전 중단한다.

**기술 스택:**
- Git, Markdown, knowledge-curator standalone CLI

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 원격 접근 확인, 임시 checkout 준비, 계획 초안 작성, 리뷰어 FAIL 지적 반영 |
| 현재 위치 | Gate 2 리뷰 통과 필요 |
| 다음 단계 | 이관 문서 작성, 원격 커밋/푸시, AgentOS 포인터 정리 |
| 완료 신호 | knowledge-agent 원격 main이 새 병합 커밋을 포함하고 AgentOS 문서가 새 canonical 위치를 가리킴 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 원격 저장소에 AgentOS knowledge 운영 문서 흡수 | `knowledge-agent`에서 AgentOS knowledge lifecycle을 확인할 수 있음 | `/tmp/knowledge-agent/concepts/agentos-knowledge-lifecycle.md`, `/tmp/knowledge-agent/concepts/index.md`, `/tmp/knowledge-agent/log.md` | `python3 catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent` / Expected: `"ok": true` |
| 2. 원격 publish preflight | 기존 원격 내용을 삭제하지 않았고 push 전 기준점이 명확함 | `/tmp/knowledge-agent` Git state | `git -C /tmp/knowledge-agent fetch origin main && ! git -C /tmp/knowledge-agent diff --name-status origin/main...HEAD | awk '$1 ~ /^D/ { found=1 } END { exit found ? 0 : 1 }'` / Expected: exit 0, no deleted tracked files |
| 3. 원격 main에 publish | GitHub `knowledge-agent` main이 새 커밋을 포함함 | `git@github.com:gabrielwithappy/knowledge-agent.git` | `git -C /tmp/knowledge-agent fetch origin main && BEFORE=$(git -C /tmp/knowledge-agent rev-parse origin/main) && AFTER=$(git -C /tmp/knowledge-agent rev-parse HEAD) && test "$BEFORE" != "$AFTER" && ! git -C /tmp/knowledge-agent diff --name-status origin/main...HEAD | awk '$1 ~ /^D/ { found=1 } END { exit found ? 0 : 1 }' && git -C /tmp/knowledge-agent push origin main && git -C /tmp/knowledge-agent fetch origin main && test "$(git -C /tmp/knowledge-agent rev-parse HEAD)" = "$(git -C /tmp/knowledge-agent rev-parse origin/main)"` / Expected: exit 0 |
| 4. AgentOS 문서 포인터 정리 | AgentOS에서 `docs/knowledge`는 새 저장소 안내 표면이 됨 | `docs/knowledge/README.md`, `docs/knowledge/index.md`, `.agentos/project/00-project-index.md` | `rg -q "https://github.com/gabrielwithappy/knowledge-agent" docs/knowledge/README.md && rg -q "pointer-only" docs/knowledge/README.md && rg -q "Do not add new knowledge notes here" docs/knowledge/README.md && rg -q "git clone git@github.com:gabrielwithappy/knowledge-agent.git" docs/knowledge/README.md && rg -q "knowledge-agent" docs/knowledge/index.md && rg -q "knowledge-agent" .agentos/project/00-project-index.md` / Expected: exit 0 |
| 5. AgentOS 변경 기록 | 이관 근거와 검증 증거가 남음 | active plan, `HISTORY.md`, lifecycle board | `git status --short --branch` / Expected: only files in the AgentOS allowed-change list |

## 리뷰 반영 이력
- 1차 plan-reviewer FAIL: publish 검증, 이관 파일 목록, remote mutation safety, AgentOS pointer verification 보강 필요.
- 1차 principle-auditor FAIL: push preflight, 기존 파일 보존 검증, AgentOS local file-change boundary 보강 필요.
- 1차 usability-reviewer FAIL: post-migration 사용법, no-local-authoring 안내, 복구 경로, 검증 문구 보강 필요.
- 반영: 이관 대상 파일, destination path, no deletion, no force push, pre/post hash verification, recovery matrix, pointer-only 문구 검증을 계획에 추가.

## 구현 결과
계획된 구현 결과:
- `knowledge-agent`에는 AgentOS `docs/knowledge`의 운영 흐름을 담은 OKF concept 문서가 추가된다.
- `knowledge-agent`의 기존 OKF 문서와 인덱스는 삭제하지 않고 새 문서 링크만 추가한다.
- AgentOS `docs/knowledge/README.md`와 `docs/knowledge/index.md`는 새 지식 작성 위치가 아니라 canonical repository 안내 표면으로 바뀐다.
- `.agentos/project/00-project-index.md`는 `knowledge-agent`를 장기지식 canonical repository로 설명한다.

## 사용 방법
계획된 사용 방법:
- 새 지식 작성 위치: `https://github.com/gabrielwithappy/knowledge-agent`
- 로컬 checkout:
  ```bash
  git clone git@github.com:gabrielwithappy/knowledge-agent.git
  cd knowledge-agent
  ```
- 구조 검증:
  ```bash
  python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project "$PWD"
  ```
- 문서 추가 후 publish:
  ```bash
  git status --short
  git add <new-or-edited-markdown>
  git commit -m "Add knowledge note"
  git push origin main
  ```
- AgentOS 로컬 `docs/knowledge`에는 새 지식 노트를 추가하지 않는다. 이 디렉터리는 새 canonical repository를 찾기 위한 안내 표면이다.

## 복구 경로

| 증상 | 원인 | 안전한 다음 행동 | 명령 |
|---|---|---|---|
| push rejected | 원격 main이 먼저 바뀜 | 원격을 fetch하고 차이를 확인한 뒤 충돌 없이 병합 | `git -C /tmp/knowledge-agent fetch origin main && git -C /tmp/knowledge-agent status --short --branch` |
| validation failed | OKF frontmatter 또는 index link 누락 | JSON diagnostics의 `next`를 따른 뒤 재검증 | `python3 /home/gabriel/agent/prj-agent/agentos-workspace/agentos/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent` |
| `D` row appears before push | 기존 원격 파일 삭제 발생 | push 중단, 삭제 원인 확인 | `git -C /tmp/knowledge-agent diff --name-status origin/main...HEAD` |
| AgentOS pointer docs stale | AgentOS 문서가 아직 로컬 authoring을 안내함 | README/index와 project index 문구를 canonical repo 기준으로 수정 | `rg -n "local knowledge surface|Put drafts|knowledge-agent" docs/knowledge .agentos/project/00-project-index.md` |
| credential prompt on HTTPS | HTTPS 자격 증명 없음 | SSH remote를 사용 | `git -C /tmp/knowledge-agent remote set-url origin git@github.com:gabrielwithappy/knowledge-agent.git` |

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
