# `agentos dashboard sync-plan --all` 일괄 동기화 옵션 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 2종 PASS, 증거: `.agents/traces/reviews/2026-07-27-dashboard-sync-plan-all-option/{plan-reviewer,principle-auditor}.md`)<br>
> active_agent: Claude Code (claude-sonnet-5)<br>
> active_session: 5b17931b-4ac1-4a97-9600-9b13d78e9f7f<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0OQyg<br>
> implementation_started_at: 2026-07-27T11:00:00Z<br>
> implementation_completed_at: 2026-07-27T11:20:00Z<br>
> implementation_duration: 약 20분<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `agentos dashboard sync-plan <파일>`(2026-07-27 구현·검증 완료, `2026-07-27-exec-plan-dashboard-sync-command.md`)은 현재 파일 하나만 동기화한다. 사용자가 "왜 active 계획 3개 중 1개만 카드로 안 올라갔냐"고 확인한 뒤(2026-07-27 대화), 매번 파일명을 하나씩 지정해야 하는 번거로움을 없애기 위해 `.agentos/project/exec-plans/active/` 디렉토리 전체를 한 번의 명령으로 동기화하는 `--all` 옵션을 추가한다.

**사용자 결과 요약:**
- 최종 결과: `agentos dashboard sync-plan --all`을 실행하면 `.agentos/project/exec-plans/active/` 아래 모든 `.md` 파일 각각에 대해 기존 `sync_plan` 로직(파싱 → 카드 검색 → 생성/갱신 → 상태 반영)을 순서대로 수행하고, 끝에 성공/실패 요약을 출력한다.
- 대상 독자: 여러 exec-plan을 GitHub Projects 보드로 한 번에 반영하고 싶은 저장소 오너(현재 1인).
- 일상 사용의 변화: 지금까지는 계획마다 `agentos dashboard sync-plan <파일>`을 반복 실행해야 했다. 이후에는 `agentos dashboard sync-plan --all` 한 줄로 active 계획 전체를 동기화할 수 있다. 기존 단일 파일 동기화(`agentos dashboard sync-plan <파일>`)는 그대로 유지되며 동작이 바뀌지 않는다.
- 바뀌지 않는 경계: `archive/` 디렉토리는 이번 스코프에서 다루지 않는다(완료된 계획까지 매번 재동기화하면 archive 개수(현재 20개 이상)만큼 GraphQL 호출이 늘어나 실질 이득 없이 API 부하만 커진다 — 사용자 확인 결과 active만으로 충분). 카드 식별 키(H1 제목), on-demand 실행 방식(자동 폴링 없음), GraphQL 전파 지연 제약은 선행 계획과 동일하게 유지된다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 선행 계획(`2026-07-27-exec-plan-dashboard-sync-command.md`)과 동일 — GitHub GraphQL API, `project` scope 토큰. 신규 의존성 없음.
- 선행 계획의 실사용 검증에서 확인된 GraphQL 쓰기-후-읽기 전파 지연 리스크가 `--all`에서는 **여러 파일을 연속 처리하는 루프 안에서 더 자주 발생할 잠재적 위험**이 있다(특히 서로 다른 계획이 우연히 같은 제목을 가질 가능성은 낮지만, 같은 계획을 이미 방금 만든 직후 --all을 또 실행하는 경우 등). 이번 계획은 이 리스크를 없애지는 않고(선행 계획에서도 미해결로 남김), "실패해도 나머지는 계속 진행"하는 방식으로 영향 범위만 국소화한다.

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| GitHub GraphQL API 도달성 | network | 실사용 검증 시 필수 | `Run:` `gh api graphql -f query='query { viewer { login } }'` / `Expected:` 정상 응답 | 단위 테스트는 mock으로 전부 수행 | 실사용 검증만 보류 |

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서의 완료 증거, Gate 2 리뷰 증거(`.agents/traces/reviews/2026-07-27-dashboard-sync-plan-all-option/`)
- Durable Result Surface: `agentos/commands/dashboard.py`(`--all` 옵션 및 디렉토리 순회 로직 추가), `tests/test_dashboard_command.py`(신규 케이스 추가)

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:**
- 기존 `sync_plan` 커맨드 함수의 시그니처를 확장: `plan_path` 인자를 optional로 바꾸고, `--all` 플래그를 추가한다. `--all`이 지정되면 `plan_path`는 무시하고 `.agentos/project/exec-plans/active/*.md`를 정렬된 순서(파일명 오름차순 — 날짜 프리픽스라 자연스럽게 시간순)로 순회한다. `plan_path`와 `--all`을 동시에 주지 않은 경우(둘 다 없음)는 기존처럼 에러로 종료.
- 기존 단일 파일 처리 로직(파싱 → `find_item_by_title` → 생성/갱신 → 상태 반영)을 내부 헬퍼 함수 `_sync_one(path, owner, project_number, token) -> bool`(성공 시 True)로 추출해, 단일 파일 모드와 `--all` 모드가 동일한 헬퍼를 공유하게 한다(중복 로직 방지).
- `--all` 모드에서 개별 파일 처리 중 예외(`ValueError` 등 어댑터가 던지는 에러, 제목 파싱 실패 등)가 발생하면 해당 파일만 건너뛰고 콘솔에 실패 사유를 출력한 뒤 다음 파일로 진행한다(사용자 확인: 부분 실패 시 전체 중단 대신 계속 진행). 마지막에 "N개 성공, M개 실패" 요약을 출력하고, 1개 이상 실패가 있으면 종료 코드 1로 끝난다(실패가 조용히 묻히지 않도록 — 신뢰성 원칙).
- `archive/`는 다루지 않는다(사용자 확인 완료 — 이번 스코프에서 명시적으로 제외).
- `active/` 안의 **모든** `.md` 파일이 대상이다 — 이 기능과 무관한 이미 완료된 다른 계획(예: `2026-07-27-claude-oauth-provider.md`, Claude OAuth 로그인 기능, 이 계획과 전혀 다른 주제)이라도 `active/`에 있으면 동기화 대상에 포함된다. `--all`은 "이 계획과 관련된 파일"이 아니라 "active 디렉토리 전체"를 대상으로 하는 것이 명시적 스코프이며, 계획 내용을 보고 관련성을 판단해 선별하는 로직은 만들지 않는다(단순성 — 그런 판단 로직 자체가 새로운 복잡도이자 이번 계획 범위 밖).

**기술 스택:**
- 기존 `agentos/commands/dashboard.py`, `pathlib.Path.glob`.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | Gate 2 리뷰 PASS(2종), Milestone 1-4 전부 구현·검증 완료 |
| 현재 위치 | 사용자 실사용 확인 대기 |
| 다음 단계 | 사용자가 실제 운영 환경에서 확인 후 아카이브 결정 |
| 완료 신호 | `agentos dashboard sync-plan --all` 실행 시 실제 테스트 보드(project 6)에 `.agentos/project/exec-plans/active/`의 모든 계획이 카드로 존재하고, 의도적으로 깨뜨린 1개 파일이 있어도 나머지가 정상 처리됨을 수동 확인(달성) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 단일 파일 로직을 공유 헬퍼로 추출 | 기존 `sync-plan <파일>` 동작이 그대로 유지된다(회귀 없음) | `agentos/commands/dashboard.py`의 `_sync_one()` | `Run:` `uv run pytest tests/test_dashboard_command.py -q` / `Expected:` 기존 4개 테스트 전부 계속 PASS(리팩터링만, 동작 변경 없음) |
| 2. `--all` 옵션 추가 | `agentos dashboard sync-plan --all`로 active 디렉토리 전체를 한 번에 동기화한다 | `agentos/commands/dashboard.py`의 `sync_plan()` | `Run:` `uv run pytest tests/test_dashboard_command.py -q -k all_option` / `Expected:` PASS — active 디렉토리에 mock 파일 2-3개를 만들어 모두 처리되는지, `plan_path`와 `--all` 둘 다 없을 때 에러로 종료하는지 검증 |
| 3. 부분 실패 처리 | 파일 하나가 실패해도 나머지는 계속 처리되고, 종료 시 성공/실패 요약과 비정상 종료 코드(1개 이상 실패 시 exit 1)를 보여준다 | `agentos/commands/dashboard.py` | `Run:` `uv run pytest tests/test_dashboard_command.py -q -k partial_failure` / `Expected:` PASS — 2개 중 1개가 예외를 던지도록 mock한 케이스에서 나머지 1개는 정상 처리되고 exit code가 1임을 확인 |
| 4. 실사용 검증 | 실제 테스트 보드에서 active 디렉토리의 모든 계획이 한 번에 카드로 반영됨을 확인 | — (검증 전용) | `Run:` `ls .agentos/project/exec-plans/active/*.md \| wc -l` 로 실행 시점의 실제 파일 개수 N을 먼저 확인한 뒤, `OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 uv run agentos dashboard sync-plan --all` 실행 → `gh project item-list 6 --owner gabrielwithappy --format json` / `Expected:` 그 N개 파일의 제목이 모두 카드로 존재(이 계획 문서 자신을 포함해 N은 실행 시점마다 달라질 수 있으므로 고정 숫자로 단언하지 않는다) |

## 리뷰 반영 이력
- 2026-07-27 (Gate 2 1차 리뷰): `principle-auditor` PASS/CLEAN (신뢰성·단순성·Rule 1 스코프 준수 모두 확인, typer 레벨에서 `plan_path`/`--all` 둘 다 없을 때의 정확한 에러 경로가 산문에서 약간 불명확하다는 non-blocking 지적만 있음 — Milestone 2가 이미 이를 테스트로 커버). `plan-reviewer` FAIL — Milestone 4가 "active 3개 계획"이라고 단언했으나 실제로는 이 계획 문서 자신이 `active/`에 추가되며 4개가 되어 있어 검증 기준이 실행 시점 사실과 어긋남. 또한 `claude-oauth-provider.md`(이 기능과 무관한, 이미 완료된 다른 계획)를 `--all`이 포함해야 하는지에 대한 판단이 명시되지 않았다는 지적(archive/ 제외 결정만큼 명확한 근거가 없었음). 반영: Milestone 4를 "실행 시점의 실제 파일 개수를 먼저 `ls`로 확인 후 그 개수만큼 존재하는지 검증"하는 방식으로 고쳐 고정 숫자 단언을 제거, 아키텍처 섹션에 "active/ 안의 모든 .md 파일이 대상이며 완료된 무관 계획도 포함, 관련성 판단 로직은 만들지 않는다(단순성)"는 원칙을 명시.
- 2026-07-27 (Gate 2 2차 리뷰, 수정본 재검토): `plan-reviewer` PASS — Milestone 4가 고정 숫자를 더 이상 단언하지 않음을 확인, 아키텍처 섹션의 "무관한 완료 계획도 포함" 명시를 확인, `active/` 디렉토리를 직접 재조회해 4개 파일 구성이 수정된 계획의 실행 시점 도출 방식과 일치함을 검증(드리프트 재발 없음), 1차 PASS 항목(`_sync_one()` 리팩터링 타당성, 기존 4개 테스트 유지, README.md 충돌 없음, TEMPLATE 준수) 모두 유지 확인. 두 서브에이전트 PASS/CLEAN 합의 완료 → `reviewed: true` 전이.

## 구현 결과
- `agentos/commands/dashboard.py`: 기존 단일 파일 로직을 `_sync_one(adapter, path)` 헬퍼로 추출(파싱→카드 검색→생성/갱신→상태 반영). `sync_plan()`은 `plan_path`를 optional로 바꾸고 `--all` 플래그를 추가했다. `--all`이면 `ACTIVE_PLANS_DIR`(`.agentos/project/exec-plans/active/`) 아래 `*.md`를 정렬된 순서로 순회하며 각각 `_sync_one()`을 호출하고, 개별 파일에서 예외가 나면 해당 파일만 건너뛰고 콘솔에 실패 사유를 출력한 뒤 나머지는 계속 진행한다. 끝에 "N succeeded, M failed" 요약을 출력하고, 실패가 1개 이상이면 종료 코드 1로 끝난다(신뢰성 — 실패를 조용히 묻지 않음). `plan_path`와 `--all` 둘 다 없으면 즉시 에러로 종료한다.
- `tests/test_dashboard_command.py`: 기존 4개 테스트는 리팩터링에도 그대로 유지(회귀 없음), `--all` 정상 동작(2개 파일 모두 성공), 부분 실패(1개는 제목 파싱 실패로 건너뛰고 나머지 1개는 정상 처리 + exit 1), "인자 둘 다 없음" 에러 케이스까지 3개 신규 테스트 추가.

## 사용 방법
```bash
# 단일 파일 (기존과 동일, 변경 없음)
agentos dashboard sync-plan <exec-plan-file> --owner <owner> --project-number <번호>

# active/ 디렉토리 전체 한 번에 동기화 (신규)
agentos dashboard sync-plan --all --owner <owner> --project-number <번호>
# 또는 환경변수로:
OBSERVABILITY_GITHUB_OWNER=<owner> OBSERVABILITY_GITHUB_PROJECT_NUMBER=<번호> agentos dashboard sync-plan --all
```
- `--all`은 `.agentos/project/exec-plans/active/`의 **모든** `.md` 파일을 대상으로 한다. 이번 기능과 무관한, 이미 완료된 다른 계획이라도 `active/`에 있으면 포함된다(관련성 판단 로직 없음 — 의도된 단순화).
- `archive/`는 대상이 아니다.
- 파일 하나가 실패해도(제목 파싱 실패, GraphQL 오류 등) 나머지는 계속 처리되며, 끝에 "N succeeded, M failed" 요약이 출력된다. 실패가 하나라도 있으면 종료 코드가 1이라, CI나 스크립트에서 실패를 감지할 수 있다.
- 기존 단일 파일 동기화 시 있던 GraphQL 전파 지연 제약(직후 재실행 시 중복 카드 위험)은 `--all`에서도 동일하게 남아 있다.

## 검증 근거
- `Run:` `uv run pytest tests/test_dashboard_command.py -q` → **실행 결과: 7 passed** (기존 4개 + 신규 3개)
- `Run:` `uv run pytest tests/ -q` (전체 회귀) → **실행 결과: 532 passed**
- 실사용 검증: 실행 시점 `ls .agentos/project/exec-plans/active/*.md | wc -l` → 4개 확인 → `OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 uv run agentos dashboard sync-plan --all` 실행 → "4 succeeded, 0 failed" 확인, 4개 계획 모두 카드로 존재 확인(`gh project item-list`). 부분 실패 시나리오도 실제 GitHub API 상대로 별도 재현 — 제목 없는 파일 1개를 섞은 디렉토리에서 실행 시 정상 파일은 처리되고("1 succeeded"), 깨진 파일은 건너뛰며("1 failed"), 종료 코드 1로 끝남을 확인 (2026-07-27).

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
