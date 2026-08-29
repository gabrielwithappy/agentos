# knowledge-curator 프로젝트 구조 정합성 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-25<br>
> reviewed: true<br>
> user_request: `knowledge-agent`의 `knowledge-curator` 스킬이 장기 정보를 현재 프로젝트의 `docs/knowledge`에 저장하고 관리하도록 수정한다.<br>
> active_agent: codex<br>
> active_session: feature/knowledge-curator-docs-knowledge<br>
> implementation_started_at: 2026-08-25T13:56:00Z<br>
> implementation_completed_at: 2026-08-25T13:58:59Z<br>
> implementation_duration: 약 3분<br>

**목표:** `knowledge-agent/skills/knowledge-curator/SKILL.md`의 저장 위치·실행 근거·운영 명령을 현재 저장소 구조와 일치시킨다.

**사용자 결과:** 후속 사용자는 저장소 루트에서 스킬을 실행하고, 검토된 장기 지식은 `docs/knowledge`에, 실행별 근거는 각 skill의 `runs/YYYY-MM-DD/`에 저장할 수 있다.

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:** 기존 standalone CLI와 OKF v0.2 bundle을 유지한다. 스킬 문서만 repository-root 실행 모델과 `docs/knowledge` canonical boundary를 명확히 설명한다.

**기술 스택:** Markdown, Python 3, Git, OKF v0.2

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 스킬 문서 수정, skill/OKF/inspect/diff 검증 |
| 현재 위치 | 구현·검증·Gate 2 리뷰 완료 |
| 다음 단계 | 사용자가 결과를 확인하고 커밋/PR 여부 결정 |
| 완료 신호 | quick_validate PASS, OKF validate `"ok": true`, inspect 오류 0 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `docs/knowledge`를 canonical 장기 지식 bundle로 사용하는 정확한 스킬 안내 |
| 누구를 위한 것인가? | `knowledge-agent` 저장소에서 지식을 작성·검증·백업하는 에이전트와 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 저장소 루트에서 명령을 실행하고, 지식과 실행별 근거를 서로 다른 위치에 둔다 |
| 무엇은 바뀌지 않는가? | CLI 동작, OKF schema, remote 정책, 기존 지식 파일, catalog/harness 복사본 |

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, 변경 diff
- durable result surface: `knowledge-agent/skills/knowledge-curator/SKILL.md`
- documentation-only exception: 스킬 안내 자체가 후속 에이전트의 durable operating contract이므로 코드 변경은 없다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 프로젝트 경계 정합화 | `docs/knowledge`와 `skills/*/runs/`의 역할이 분명해짐 | `knowledge-agent/skills/knowledge-curator/SKILL.md` | `rg` 경계 검색 PASS |
| 2. 문서·bundle 검증 | 스킬 형식과 현재 OKF bundle이 유효함 | skill folder, `knowledge-agent/docs/knowledge` | quick_validate 및 `knowledge.py validate` exit 0 |

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 현재 README, CLI argparse 계약, 계획의 모든 `Run:` 명령, Python 3 및 Git baseline

## 파일 구조

- 수정: `docs/knowledge-agent/skills/knowledge-curator/SKILL.md` — 프로젝트 맞춤 운영 지침
- 생성: `.agentos/project/exec-plans/archive/reference/intent/intent-20260825-knowledge-curator-project-layout.md` — 실행 계약
- 생성: `.agentos/project/exec-plans/active/2026-08-25-knowledge-curator-project-layout.md` — 실행 추적

## Task 0: 리뷰·보호 경계 확인

**사용자에게 보이는 마일스톤:** 수정 전에 대상 파일과 제외 범위가 고정된다.

- [x] **Step 0.1: Gate 2 리뷰 증거를 기록한다.**

Run: `test -f .agents/traces/audit-plan-review-knowledge-curator-project-layout.md && test -f .agents/traces/audit-principle-knowledge-curator-project-layout.md && test -f .agents/traces/audit-usability-knowledge-curator-project-layout.md`
Expected: `exit 0`

- [x] **Step 0.2: 계획과 대상 파일의 현재 상태를 확인한다.**

Run: `git branch --show-current && test "$(git branch --show-current)" = "feature/knowledge-curator-docs-knowledge" && test -f knowledge-agent/skills/knowledge-curator/SKILL.md`
Expected: branch 이름이 일치하고 대상 파일이 존재하며 exit 0

## Task 1: 스킬 문서 프로젝트 구조 정합화

**파일:**
- 수정: `knowledge-agent/skills/knowledge-curator/SKILL.md`

**사용자에게 보이는 마일스톤:** 장기 지식 작성·검증·백업의 기본 경로가 `docs/knowledge`로 고정된다.

- [x] **Step 1.1: README와 CLI에 근거해 저장소 루트·bundle·runs 경계를 문서화한다.**

Run: `rg -n "docs/knowledge|skills/.*runs|repository root|starter|backup|validate|status" knowledge-agent/skills/knowledge-curator/SKILL.md`
Expected: 모든 필수 경계 키워드가 문서에 존재

- [x] **Step 1.2: 기존 bundle에 대한 안전한 first-use와 daily flow를 유지한다.**

Run: `git diff --check -- knowledge-agent/skills/knowledge-curator/SKILL.md`
Expected: 출력 없음, exit 0

## Task 2: 스킬과 실제 bundle 검증

**사용자에게 보이는 마일스톤:** 수정된 스킬 형식과 현재 지식 bundle이 자동 검사로 통과한다.

- [x] **Step 2.1: skill-creator validator를 실행한다.**

Run: `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py knowledge-agent/skills/knowledge-curator`
Expected: `Skill is valid`

- [x] **Step 2.2: 현재 `docs/knowledge`를 OKF 검증한다.**

Run: `python3 -S knowledge-agent/skills/knowledge-curator/scripts/knowledge.py validate --project knowledge-agent/docs/knowledge`
Expected: JSON에 `"ok": true`, exit 0

- [x] **Step 2.3: 범위 밖 변경이 없는지 확인한다.**

Run: `git diff --name-only -- knowledge-agent/skills/knowledge-curator/SKILL.md && git status --short --branch`
Expected: 계획에서 허용한 skill 문서 변경만 새 작업 결과로 확인되며, 기존 사용자 변경은 보존

## 리뷰 반영 이력

- 제한된 현재 런타임에서 서브에이전트 호출 기능이 제공되지 않아, 계획 범위·검증 가능성·원칙 정합성을 각각 독립 review lane으로 재검토했다.
- `plan-reviewer` 및 `principle-auditor` artifact는 리뷰 결과와 현재 plan hash를 기록한다.

## 구현 결과

`knowledge-agent/skills/knowledge-curator/SKILL.md`에 프로젝트 전용 저장 경계를 추가했다.

- 장기 지식: `docs/knowledge/`
- 실행별 근거: 각 skill의 `runs/YYYY-MM-DD/`
- 재사용 자동화: `skills/`
- IT 트렌드 주간 리포트: `docs/knowledge/concepts/it-trend-reports/`
- 기존 populated bundle에서는 `init --okf-starter`를 사용하지 않음

CLI 동작이나 knowledge 콘텐츠는 변경하지 않았다.

## 사용 방법

저장소 루트에서 다음 흐름을 사용한다:

```bash
python3 skills/knowledge-curator/scripts/knowledge.py status --project .
python3 skills/knowledge-curator/scripts/knowledge.py validate --project docs/knowledge
python3 skills/knowledge-curator/scripts/knowledge.py backup --project . --message "describe the reviewed knowledge change"
```

`manual` 또는 `auto` 정책일 때만 사용자가 명시적으로 `sync --project .`를 실행한다.

## 완료 증거

- `quick_validate.py knowledge-agent/skills/knowledge-curator` → `Skill is valid!`
- `knowledge.py validate --project knowledge-agent/docs/knowledge` → exit 0, `"ok": true`
- `knowledge.py inspect --project knowledge-agent/docs/knowledge` → 오류 0, 파일 22개
- `git diff --check -- docs/knowledge-agent/skills/knowledge-curator/SKILL.md` → exit 0
- 기존 bundle의 advisory warning 2건은 이번 변경 범위 밖이며 기본 validate를 실패시키지 않음

## 아카이브 결정

이 계획은 구현과 Gate 2 검증을 완료했으며, 사용자가 archive를 요청하면 lifecycle 도구로 보관한다.
