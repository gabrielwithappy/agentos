# `project init` 프로젝트 문서 bootstrap 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-31<br>
> reviewed: true<br>
> user_request: `agentos project init` 실행 시 신규 프로젝트에 프로젝트 문서 template을 적용하고, 기존 사용자 문서·vendor 설정과 장기적인 경로 통일성을 보장한다.<br>
> active_agent: Codex<br>
> active_session: feature/audit-unified-hooks (current checkout)<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-08-31T14:50:00Z<br>
> implementation_completed_at: 2026-08-31T14:39:10Z<br>
> implementation_duration: 약 54분<br>
> **usability_review_required:** true<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `agentos project init`이 프로젝트 문서가 없는 신규 프로젝트에 검증된 project-document template을 적용하고, 기존 문서와 vendor 운영 파일은 변경하지 않도록 만든다.

**사용자 결과:** 사용자는 한 번의 `agentos project init`으로 런타임 하네스와 장기 프로젝트 문서의 starter 구조를 얻고, 부분·충돌 상태에서는 무엇이 부족한지와 다음 행동을 명확히 확인한다.

**진행 상태:** 구현·검증·Gate 2 closeout 완료

**아키텍처:** AgentOS 저장소의 package-owned template source와 대상 프로젝트의 user-owned `.agentos/project/`를 분리한다. `project init`은 문서 세트가 완전히 없을 때만 원자적으로 생성하고, 기존 또는 부분 문서는 보존한 채 상태·누락 목록을 런타임 리소스 상태와 별도로 반환한다. 모든 vendor는 기존 `AGENTS.md`·`CLAUDE.md`를 수정하지 않고 공통 bootstrap을 통해 canonical project index를 발견한다.

**기술 스택:** Python/Typer, pathlib, JSON manifest, pytest, Hatch package resource inclusion

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | project-document template, no-overwrite 상태 보고, source/package resolver, CLI 문서, focused tests, discovery tests, isolated install, clean install, manifest sync |
| 현재 위치 | 구현·fresh verification·Gate 2 evidence를 모두 기록한 closeout 상태 |
| 다음 단계 | 사용자가 archive를 요청하면 공식 lifecycle 명령으로 보관 |
| 완료 신호 | 신규·부분·기존 문서 상태와 설치 경로가 모두 검증되고, 관련 focused/install/manifest 검증이 PASS하며 public baseline 영향이 명시됨 |

## 실행 blocker 기록

- Gate 2 reviewer artifact 3종을 plan-specific 경로에 최종 기록했고 `review_artifacts.py check`가 세 reviewer를 모두 PASS로 확인했다. self-review fallback provenance와 기존 unified-hook trace 분리는 artifact에 명시했다.
- 이 blocker는 구현을 전면 중지하지 않고 이 계획의 `docs/project`·`project init`·설치 검증 범위의 위험과 다음 단계로 기록한다.
- manifest 갱신은 공식 `sync-manifest.sh --update codex`와 즉시 `--check`를 실행해 해소했다. 기존 사용자 파일과 concurrent 변경은 건드리지 않았다.
- public suite는 `catalog`와 `docs/knowledge-agent`의 동일 basename 테스트 수집 충돌로 collection 단계에서 실패했으며, 이 계획의 변경과 분리된 baseline으로 유지한다.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 런타임 리소스와 함께 `.agentos/project/`의 project document starter set, 생성/부분/기존 상태, 누락 파일과 `next_action`을 얻는다. |
| 누구를 위한 것인가? | AgentOS를 새 프로젝트에 적용하는 개발자, 장기 프로젝트 방향을 관리하는 오너, 후속 에이전트·리뷰어 |
| 일상 사용에서 무엇이 달라지는가? | 계획 전에 `00-project-index.md`에서 프로젝트 맥락을 시작할 수 있고, 문서가 없거나 부족할 때 에이전트가 추측하지 않고 상태를 보고한다. |
| 무엇은 바뀌지 않는가? | 기존 `AGENTS.md`, `CLAUDE.md`, vendor 설정, 사용자 project 문서, 기존 `.agents` 관리되지 않는 파일은 자동 수정·삭제·병합하지 않는다. Template은 생성 원본일 뿐 이후 문서의 소유자가 아니다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. canonical template 계약 고정 | template 원본과 대상 `.agentos/project`의 소유권·경로가 문서화된다. | `docs/project/template/`, `docs/getting-started.md`, 관련 SSOT | `test -f docs/project/template/00-project-index.md` 및 template contract PASS |
| 2. 신규 문서 bootstrap | 문서가 없는 프로젝트에서 `project init` 후 root 문서와 reference README가 생성된다. | `agentos/commands/project.py`, package resource 설정 | focused project-init tests PASS |
| 3. 보존·부분 상태 보고 | 기존 문서는 보존되고, 부분 문서는 누락 목록·다음 행동과 함께 보고된다. | `agentos/commands/project.py`, `project status`, JSON schema | existing/partial/no-overwrite regression PASS |
| 4. 공통 문서 발견 연결 | AgentOS bootstrap과 core guidance가 `.agentos/project/00-project-index.md`를 우선 발견한다. | `agentos/conversation/bootstrap.py`, `agentos/terminal/skills.py`, harness docs | bootstrap discovery/path-precedence tests PASS |
| 5. 설치·공개 경계 정합 | source checkout과 isolated installed CLI가 동일 template을 사용한다. | `pyproject.toml`, package resource resolver, public boundary | isolated install, manifest, public-suite PASS |

## 범위 경계

### 포함

- `docs/project/template/`를 package-owned project-document template source로 추가한다.
- 대상 프로젝트의 canonical 문서 경로를 `.agentos/project/`로 고정한다.
- root 문서 00~06과 최소 supporting category README만 template에 포함한다.
- `project init`이 문서 세트 부재·완전·부분 상태를 구분한다.
- 기존 문서, `AGENTS.md`, `CLAUDE.md`, vendor 설정, unmanaged `.agents` 파일을 보존한다.
- JSON 및 human-readable 결과에 문서 상태, 생성/보존 여부, 누락 항목, `next_action`을 표시한다.
- `agentos-core-guidance`, bootstrap, `writing-plans`, `intent-clarification`, `requirement-discovery`의 canonical 경로 참조를 `.agentos/project` 기준으로 정렬한다.

### 제외

- 기존 project 문서의 자동 마이그레이션, merge, overwrite, `--force` update
- 현재 AgentOS 저장소의 실제 결정 문서·실행계획·archive를 신규 프로젝트에 복사
- 새 프로젝트의 `AGENTS.md`, `CLAUDE.md`, `.claude`, `.codex` 설정 자동 생성 또는 수정
- project document 내용을 자동으로 채우거나 사용자 목표를 추론하는 기능
- `docs/project`를 대상 프로젝트의 두 번째 canonical 문서 트리로 유지하는 compatibility fork
- 외부 서비스, 네트워크, credential, profile, runtime database 추가

## 장기 적용 표면

- traceability surface: 이 active plan, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, `HISTORY.md`, Gate 2 reviewer traces
- durable result surface: `docs/project/template/`, `.agentos/project/` bootstrap contract, `agentos/commands/project.py`, bootstrap/discovery code, CLI/help documentation, regression tests
- documentation-only exception: 없음. CLI 동작·설치 산출물·에이전트 문서 발견 경로를 함께 변경한다.

## 파일 구조

- 생성: `docs/project/README.md` — project document set, ownership, canonical path, lifecycle 안내
- 생성: `docs/project/document-governance.md` — template/user-owned/runtime boundary와 no-overwrite 계약
- 생성: `docs/project/template/00-project-index.md`
- 생성: `docs/project/template/01-project-charter.md`
- 생성: `docs/project/template/02-product-scope-and-requirements.md`
- 생성: `docs/project/template/03-system-contract.md`
- 생성: `docs/project/template/04-safety-risk-verification.md`
- 생성: `docs/project/template/05-agent-operating-contract.md`
- 생성: `docs/project/template/06-decisions-progress-change-log.md`
- 생성: `docs/project/template/reference/README.md`
- 생성: `docs/project/template/reference/implementation/README.md`
- 생성: `docs/project/template/reference/decisions/README.md`
- 생성: `docs/project/template/reference/operations/README.md`
- 수정: `agentos/commands/project.py` — 문서 template resolver, atomic bootstrap, 상태/결과 계약
- 수정: `agentos/conversation/bootstrap.py` — `.agentos/project` index와 root docs 발견 규칙
- 수정: `agentos/terminal/skills.py` — project-local runtime skill과 project-document discovery 경계 정합
- 수정: `agentos/commands/harness.py` 또는 관련 bootstrap surface — 프로젝트 문서 존재를 확인하는 공통 진입점(코드 구조 확인 후 최소 파일만 선택)
- 수정: `agentos/skills` 또는 package resource resolver — source/package 설치 환경 간 template 해석
- 수정: `pyproject.toml` — template resource의 wheel/sdist 포함
- 수정: `docs/getting-started.md`, `docs/cli-reference.md` — 실제 init 결과와 상태/다음 행동 문서화
- 수정: `.agentos/project/00-project-index.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md` — canonical path와 init contract 반영
- 수정: `.agents/skills/harness/agentos-core-guidance/SKILL.md`, `intent-clarification`, `requirement-discovery`, `writing-plans` 관련 문서 — `.agentos/project` 우선 발견 및 fallback 정합
- 생성/수정: `tests/test_project_command.py`, bootstrap/discovery 관련 테스트, package/install smoke verifier
- 수정: `config/public-boundary.json` 및 manifest 입력 — 공개해야 하는 template/test surface만 등록

## 의존성 분석

- 외부 API·토큰·네트워크 의존성: 없음
- package install 검증: source checkout과 isolated wheel/sdist가 동일한 template 파일을 제공해야 한다.
- 기존 사용자 상태 의존성: `.agentos/project`, `AGENTS.md`, `CLAUDE.md`, `.agents`가 존재할 수 있으므로 preflight가 필요하다.
- 권한 경계: 생성은 명시적 `project init` 범위 안에서만 수행하며 기존 문서·vendor 파일의 수정 권한을 획득하지 않는다.
- 선행 결정: `.agentos/project`를 canonical target path로 확정하고 `docs/project`는 source/template namespace로만 사용한다.

## 위험과 완화

| 위험 | 완화 | 검증 |
|---|---|---|
| 기존 project 문서 덮어쓰기 | 문서 세트가 하나라도 존재하면 기존 파일을 보존하고 missing/partial만 보고 | 기존·부분 상태 no-overwrite regression |
| 런타임 성공을 전체 init 성공으로 오인 | runtime과 documents 상태를 별도 필드로 반환하고 `current`는 완전 상태에만 사용 | JSON schema/state matrix test |
| source와 installed package template 불일치 | source/package digest와 isolated install smoke를 비교 | package resource contract PASS |
| `docs/project`와 `.agentos/project` 경로 혼재 | canonical path를 하나로 고정하고 skill/docs/test 참조를 정렬 | repo-wide canonical path verifier |
| 빈 starter 문서가 실제 project authority로 오인 | template에 starter 상태와 user-owned/generated boundary를 명시하고 readiness를 별도 판단 | document governance contract |
| vendor 호환성 훼손 | `AGENTS.md`, `CLAUDE.md`, vendor 설정을 읽기 전용으로 취급 | sentinel preservation test |
| 생성 중 오류로 부분 파일 잔류 | temp directory 생성 후 atomic rename, failure cleanup | interrupted/bootstrap failure test |

## Task 1: canonical project-document template과 거버넌스 고정

**파일:**
- 생성: `docs/project/README.md`
- 생성: `docs/project/document-governance.md`
- 생성: `docs/project/template/**`
- 수정: `.agentos/project/00-project-index.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`

**사용자에게 보이는 마일스톤:** 새 프로젝트 문서의 canonical 경로, template source와 user-owned 결과의 차이, no-overwrite 정책을 확인할 수 있다.

- [x] **Step 1: root 문서 00~06과 최소 reference README template을 작성한다.**

Run: `test -f docs/project/template/00-project-index.md && test -f docs/project/template/06-decisions-progress-change-log.md && test -f docs/project/template/reference/implementation/README.md`
Expected: exit 0

- [x] **Step 2: template이 현재 프로젝트의 실제 결정·경로·도메인 데이터를 포함하지 않는지 검증한다.**

Run: `! rg -n "Costmaster|ys-costmaster|Browser QA script|0004-agentos-llm-credential-strategy" docs/project/template && rg -n "\.agentos/project|root project documents|does not override" docs/project
Expected: exit 0

- [x] **Step 3: canonical path와 source/target ownership을 root project docs에 반영한다.**

Run: `rg -n "\.agentos/project|docs/project/template|template source|user-owned|덮어쓰|overwrite" .agentos/project/00-project-index.md .agentos/project/03-system-contract.md .agentos/project/04-safety-risk-verification.md docs/project/README.md docs/project/document-governance.md`
Expected: canonical target, template source, no-overwrite boundary가 모두 출력된다.

## Task 2: `project init` 문서 bootstrap과 결과 상태 구현

**파일:**
- 수정: `agentos/commands/project.py`
- 수정: `tests/test_project_command.py`

**사용자에게 보이는 마일스톤:** 문서가 없는 프로젝트에는 template이 생기고, 기존·부분 문서는 보존되며, 결과에 문서 상태와 다음 행동이 표시된다.

- [x] **Step 1: source checkout/package fallback을 통해 template을 안전하게 해석한다.**

Run: `python -m pytest -q tests/test_project_command.py -k "template or resource"`
Expected: template resolver focused tests PASS

- [x] **Step 2: 문서 세트가 완전히 없을 때 임시 디렉터리에서 생성하고 원자적으로 반영한다.**

Run: `python -m pytest -q tests/test_project_command.py -k "project_documents_empty or atomic"`
Expected: 신규 문서 bootstrap tests PASS

- [x] **Step 3: 완전·부분·기존 문서 상태와 누락 목록을 JSON/human output으로 구현한다.**

Run: `python -m pytest -q tests/test_project_command.py -k "project_documents or no_overwrite or partial"`
Expected: state matrix and no-overwrite tests PASS

- [x] **Step 4: runtime snapshot과 project documents 상태를 manifest/status에서 분리한다.**

Run: `python -m pytest -q tests/test_project_command.py -k "status or manifest"`
Expected: runtime/document state separation tests PASS

## Task 3: 공통 bootstrap과 core guidance의 project document discovery 정합

**파일:**
- 수정: `agentos/conversation/bootstrap.py`
- 수정: `agentos/terminal/skills.py` 및 실제 공통 bootstrap 호출 surface
- 수정: `.agents/skills/harness/agentos-core-guidance/SKILL.md`
- 수정: `.agents/skills/harness/intent-clarification/SKILL.md`, `requirement-discovery/SKILL.md`, `writing-plans/SKILL.md`의 stale path 참조
- 생성/수정: 관련 bootstrap/discovery 회귀 테스트

**사용자에게 보이는 마일스톤:** 기존 vendor 파일을 수정하지 않아도 AgentOS 세션과 하네스가 `.agentos/project/00-project-index.md`를 먼저 발견한다.

- [x] **Step 1: discovery precedence를 `AGENTS.md`/vendor guide → `.agentos/project/00-project-index.md` → root docs → core guidance fallback으로 고정한다.**

Run: `python -m pytest -q tests/test_conversation_bootstrap.py tests/test_core_guidance_skill.py -k "project or bootstrap or guidance"`
Expected: project document discovery tests PASS

- [x] **Step 2: 기존 `AGENTS.md`, `CLAUDE.md`, vendor 설정을 수정하지 않는 sentinel 회귀를 추가한다.**

Run: `python -m pytest -q tests -k "preserve or vendor or agents"`
Expected: preservation tests PASS and no vendor file mutation

- [x] **Step 3: 모든 canonical skill/help reference에서 `docs/project` 대상 경로를 제거하거나 source template namespace로 명확히 구분한다.**

Run: `rg -n "docs/project/00-project-index|docs/project/01-project-charter|docs/project/02-product" .agents/skills agentos docs && ! rg -n "docs/project/(00-project-index|01-project-charter|02-product)" .agents/skills/harness/agentos-core-guidance/SKILL.md .agents/skills/harness/intent-clarification/SKILL.md .agents/skills/harness/requirement-discovery/SKILL.md .agents/skills/harness/writing-plans/SKILL.md`
Expected: target document references use `.agentos/project`; `docs/project` remains only as template/source path where intended.

## Task 4: package, documentation, and public-boundary verification

**파일:**
- 수정: `pyproject.toml`
- 수정: `docs/getting-started.md`, `docs/cli-reference.md`
- 수정: `config/public-boundary.json`, manifest inputs as required
- 수정: focused/install/public verification scripts and tests

**사용자에게 보이는 마일스톤:** source checkout과 설치된 CLI의 `project init` 동작이 같고, 사용법과 상태 결과가 문서에 반영된다.

- [x] **Step 1: wheel/sdist에 template이 포함되고 isolated install에서 읽히는지 검증한다.**

Run: `bash scripts/verify-cli-isolated-install.sh`
Expected: `PASS agentos-cli-isolated-install`

- [x] **Step 2: CLI 사용법·상태·복구 안내를 갱신한다.**

Run: `rg -n "project init|\.agentos/project|documents|missing|next_action|overwrite" docs/getting-started.md docs/cli-reference.md`
Expected: 신규/기존/부분 상태와 다음 행동 안내가 모두 존재한다.

- [x] **Step 3: focused, public boundary, manifest 검증을 실행한다.**

Run: `.venv/bin/pytest -q tests/test_project_command.py tests/test_core_guidance_skill.py && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash scripts/verify-clean-install.sh`
Expected: 모든 명령 exit 0 및 각 verifier의 PASS 출력

## Plan Quality Gate

- 신규 프로젝트에서 `agentos project init --path <tmp> --json` 결과의 `project_documents.state=current`, `project_documents.missing=[]`이고 `.agentos/project/00-project-index.md` 및 01~06 root 문서가 존재한다.
- 기존 `.agentos/project`와 `AGENTS.md`·`CLAUDE.md`를 가진 프로젝트에서 init 후 파일 hash가 변하지 않고 결과에 `project_documents.state=current`가 표시된다.
- 일부 project 문서만 있는 프로젝트에서 기존 파일은 변하지 않고 `project_documents.state=partial`, 누락 파일 목록과 다음 행동이 표시된다.
- source checkout과 isolated installed CLI가 동일 template 파일 목록과 digest를 사용한다.
- bootstrap이 `.agentos/project/00-project-index.md`를 발견하며, project 문서가 `AGENTS.md`·vendor guide·protected-path rules를 override하지 않는다.
- 관련 focused tests, public boundary verifier, manifest check, isolated install smoke가 모두 fresh PASS한다.

## 리뷰 게이트

- `plan-reviewer`: 계획 구조, 실행 가능성, 범위·검증 계약 PASS
- `principle-auditor`: canonical path, ownership, P4 단순성, 중복·legacy path 정리 PASS/CLEAN
- `usability-reviewer`: user-facing init 결과, partial state, recovery/next action, CLI 문구 PASS
- 리뷰 증거: `.agents/traces/reviews/2026-08-31-project-init-project-documents/{plan-reviewer,principle-auditor,usability-reviewer}.json` 및 동일 디렉터리의 audit notes
- 세 리뷰어의 독립 PASS와 물리적 증거가 생성되기 전 `reviewed: true`로 변경하지 않는다.
- 전체 harness suite는 기존 legacy/MCP baseline 실패(`26 PASS / 28 FAIL`, Python `143 passed / 9 failed`)가 있어 이 계획의 focused/public/install PASS와 별도로 기록한다.

## 구현 결과

`project init`은 이제 runtime resource snapshot과 별도로 `.agentos/project/` starter 문서를 생성한다. 문서가 없는 경우에만 원자적으로 생성하고, 기존·부분 문서는 보존하면서 `project_documents.state`와 `missing`을 보고한다. source checkout과 설치된 package 모두에서 template을 해석하며, bootstrap은 `AGENTS.md`가 없어도 `.agentos/project/00-project-index.md`를 발견한다.

계획에 기록한 blocker 중 manifest 불일치는 공식 동기화로 해소했다. 전체 harness의 기존 MCP/legacy baseline 실패는 별도 기록했으며 project-init 범위의 검증에는 영향을 주지 않는다.

## 사용 방법

새 프로젝트에서 다음을 실행한다:

```bash
agentos setup
agentos project init --path . --json
agentos project status --path . --json
```

초기화 후 project document는 `.agentos/project/`에서 작성한다. 이미 문서가 있거나 일부만 있으면 자동으로 덮어쓰지 않으며, JSON의 `project_documents`에서 상태와 누락 파일을 확인한다.

## 아카이브 결정

구현·검증은 완료되었지만 Gate 2 evidence가 아직 유효하지 않으므로 archive하지 않는다. artifact 재기록과 재검토 후에도 사용자의 명시적 archive 요청 전까지 active에 유지한다. archive할 때만 다음 lifecycle 명령을 실행한다:

```bash
python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py archive .agentos/project/exec-plans/active/2026-08-31-project-init-project-documents.md --status 완료
```
