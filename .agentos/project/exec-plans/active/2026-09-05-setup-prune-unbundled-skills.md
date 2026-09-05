---
status: 완료
date: 2026-09-05
reviewed: true
usability_review_required: false
user_request: setup 시 번들에서 제외된 스킬 정리 및 로컬 환경/카탈로그 정리
active_agent: antigravity
active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: fix/setup-prune-unbundled-skills)
dashboard_item_id:
implementation_started_at: 2026-09-05T03:00:00Z
implementation_completed_at: 2026-09-05T03:02:00Z
implementation_duration: 2m
next_action: user archive decision
---

# setup 시 번들 제외 스킬 자동 정리 및 유령 카탈로그 제거 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `agentos setup` 실행 시 과거에 `bundled`로 설치되었으나 현재 번들 목록(`DEFAULT_SKILL_NAMES`)에서 제외된 스킬을 전역 디렉터리(`~/.agentos/core/.agents/skills/`) 및 매니페스트에서 자동으로 안전하게 제거(prune)하도록 기능을 개선한다.
- `catalog/skills/`에 소스 디렉터리가 없는 유령 스킬 3종(`ascii-art`, `baoyu-comic`, `xlsx`)을 `catalog/skills/catalog.json` 및 `config/public-boundary.json`에서 정리하여, `project init` 등의 스킬 선택창에 나타나지 않도록 정합화한다.

**사용자 결과 요약:**
- 사용자가 `agentos setup`을 실행하면 더 이상 번들에서 제외된 구버전 스킬이 전역 스킬 풀에 남아있지 않고 자동 정리된다.
- `agentos project init`의 옵셔널 스킬 선택창(Selection)에서 실제 소스가 없는 유령 스킬(`baoyu-comic` 등)이 깔끔하게 제거된다.
- 기존 정상 번들 스킬이나 사용자가 외부에서 설치한 커스텀 스킬(`origin != "bundled"`)은 안전하게 보존된다.

**의존성 분석:**
- 외부 의존성: 없음
- 내부 선행 조건: `chore/remove-legacy-harness-skills`가 `main`에 병합 완료됨.
- 스캔 기준: Git 상태, `agentos/terminal/skills.py`, `agentos/commands/setup.py`, `catalog/skills/catalog.json`, `config/public-boundary.json`, 단위 테스트, 하네스 테스트, 공개 검증 스위트.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, `HISTORY.md`, generated plan board
- Durable Result Surface: `agentos/terminal/skills.py`, `agentos/commands/setup.py`, `catalog/skills/catalog.json`, `config/public-boundary.json`, `tests/`
- Documentation-Only Exception: 없음. 실제 코드 수정 및 레지스트리 정합화 작업이다.

**진행 상태:** 계획 초안 작성, 독립 리뷰 대기 중

**아키텍처:**
1. `agentos/terminal/skills.py`:
   - `BundledInstallSummary`에 `pruned: int = 0` 필드 추가.
   - `install_bundled_skills()`에 prune 로직 추가: `manifest["skills"]`에 `origin == "bundled"`로 기록되어 있으나 현재 `bundled_skill_sources()`에 존재하지 않는 스킬 디렉터리를 `shutil.rmtree()`로 제거하고 매니페스트에서도 삭제.
2. `agentos/commands/setup.py`:
   - `summary.pruned`가 있을 경우 사용자 콘솔 출력에 정리 수량을 표시.
3. `catalog/skills/catalog.json`:
   - `ascii-art`, `baoyu-comic`, `xlsx` 3개 항목 삭제.
4. `config/public-boundary.json`:
   - 삭제된 3개 스킬 관련 경로 5개 제거.
5. 테스트:
   - `tests/test_setup_bundled_prune.py`: 과거 번들 스킬이 `setup` 실행 시 prune되고 커스텀 스킬은 보존되는지 검증.

**기술 스택:** Python 3.11+, pytest, Typer, JSON, Git

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | unbundled 스킬 자동 prune 구현, 유령 카탈로그 및 공개 경계 정합화, 단위/공개/하네스 테스트 전체 PASS |
| 현재 위치 | 구현 및 검증 완료 |
| 다음 단계 | 커밋, 푸시, PR 병합 및 아카이브 결정 |
| 완료 신호 | unbundled 스킬 자동 prune 기능 구현, 유령 카탈로그 항목 제거, 테스트 100% 통과 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 번들에서 빠진 레거시 스킬이 자동으로 청소되는 안정적인 `setup`과 정확한 스킬 카탈로그 |
| 누구를 위한 것인가? | AgentOS CLI를 설치·사용하고 새 프로젝트를 초기화하는 모든 개발자 |
| 일상 사용에서 무엇이 달라지는가? | `agentos project init` 시 존재하지 않는 유령 스킬이 목록에 뜨지 않고, setup 시 자동으로 불필요한 번들 잔여물이 청소됨 |
| 무엇은 바뀌지 않는가? | 사용자가 `agentos skill install`로 설치한 커스텀 스킬은 삭제되지 않고 보존됨 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 번들 제외 스킬 자동 prune 구현 | setup 시 unbundled 스킬이 안전하게 삭제됨 | `agentos/terminal/skills.py`, `agentos/commands/setup.py` | 단위 테스트 통과 |
| 2. 유령 카탈로그 및 공개 경계 정합화 | catalog.json 및 public-boundary에서 유령 스킬 3종 제거 | `catalog/skills/catalog.json`, `config/public-boundary.json` | JSON 파싱 및 부재 검증 |
| 3. 전체 검증 및 계약 테스트 | 카탈로그 뷰어 생성 및 공개/하네스 테스트 전체 PASS | tests, harness suite, public suite | pytest 및 27/27 하네스 테스트 통과 |

## 리뷰 반영 이력

- 계획 초안: setup 시 unbundled 스킬 자동 정리 및 catalog.json / public-boundary.json 정합화 계획 수립.

## 사전 실행 Gate와 closeout 경계

- Gate 2 artifact는 구현 Task가 아니라 이 lifecycle section에서 확인한다.
- `plan-reviewer`와 `principle-auditor`의 독립 PASS를 먼저 확인하고 진행한다.

## 리뷰 범위

- 변경 범위:
  - `agentos/terminal/skills.py`
  - `agentos/commands/setup.py`
  - `catalog/skills/catalog.json`
  - `config/public-boundary.json`
  - `tests/test_setup_bundled_prune.py`
- required review: `plan-reviewer` PASS, `principle-auditor` PASS/CLEAN
- recovery: `git checkout` 또는 `git restore`로 변경 사항을 롤백한다.

## Task 0: 사전 기준 및 브랜치 확인

**파일:**
- 읽기: `agentos/terminal/skills.py`, `catalog/skills/catalog.json`
- 수정: 없음

**사용자에게 보이는 마일스톤:** 작업 브랜치 상태와 대상 파일이 확인된다.

- [x] **Step 0.1: feature 브랜치 상태를 확인한다.**

Run: `test "$(git branch --show-current)" = "fix/setup-prune-unbundled-skills" && echo 'PASS branch-preflight'`
Expected: `PASS branch-preflight`

- [x] **Step 0.2: 유령 카탈로그 항목 존재를 확인한다.**

Run: `python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); names={s['name'] for s in d['skills']}; assert {'ascii-art', 'baoyu-comic', 'xlsx'}.issubset(names); print('PASS ghost-skills-detected')"`
Expected: `PASS ghost-skills-detected`

## Task 1: unbundled 스킬 자동 prune 기능 구현

**파일:**
- 수정: `agentos/terminal/skills.py`
- 수정: `agentos/commands/setup.py`

**사용자에게 보이는 마일스톤:** setup 실행 시 번들에서 빠진 스킬이 자동으로 정리된다.

- [x] **Step 1.1: `BundledInstallSummary`에 `pruned` 필드를 추가하고 `install_bundled_skills`에 prune 로직을 구현한다.**

Run: `python3 -c "from agentos.terminal.skills import BundledInstallSummary; s = BundledInstallSummary(pruned=1); assert s.pruned == 1; print('PASS summary-pruned-field')"`
Expected: `PASS summary-pruned-field`

- [x] **Step 1.2: `setup.py`에 pruned 출력 메시지를 추가한다.**

Run: `python3 -c "import agentos.commands.setup; print('PASS setup-imported')"`
Expected: `PASS setup-imported`

- [x] **Step 1.3: 단위 테스트를 작성하여 unbundled 스킬 삭제 및 커스텀 스킬 보존을 검증한다.**

Run: `pytest tests/test_setup_bundled_prune.py -v`
Expected: `1 passed`

## Task 2: 유령 카탈로그 항목 및 공개 경계 정합화

**파일:**
- 수정: `catalog/skills/catalog.json`
- 수정: `config/public-boundary.json`

**사용자에게 보이는 마일스톤:** 실체 파일이 없는 유령 스킬이 카탈로그와 공개 경계에서 제거된다.

- [x] **Step 2.1: `catalog/skills/catalog.json`에서 `ascii-art`, `baoyu-comic`, `xlsx` 항목을 삭제한다.**

Run: `python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); names={s['name'] for s in d['skills']}; assert not names & {'ascii-art', 'baoyu-comic', 'xlsx'}; print('PASS catalog-cleaned')"`
Expected: `PASS catalog-cleaned`

- [x] **Step 2.2: `config/public-boundary.json`에서 해당 스킬 경로를 제거한다.**

Run: `python3 -c "import json; d=json.load(open('config/public-boundary.json')); assert not any(any(x in p for x in ('ascii-art', 'baoyu-comic', 'xlsx')) for p in d['paths']); print('PASS boundary-cleaned')"`
Expected: `PASS boundary-cleaned`

## Task 3: 전체 검증 및 계약 테스트

**파일:**
- 검증: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py`, `scripts/verify-public-test-suite.sh`, `.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`, `git diff --check`

**사용자에게 보이는 마일스톤:** 카탈로그 뷰어 생성 및 공개/하네스 테스트 전체가 통과한다.

- [x] **Step 3.1: 카탈로그 뷰어 생성을 검증한다.**

Run: `catalog_tmp=$(mktemp -d) && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output "$catalog_tmp/index.html" 2>"$catalog_tmp/stderr" && ! grep -q 'skipping ascii-art\|skipping baoyu-comic\|skipping xlsx' "$catalog_tmp/stderr" && echo 'PASS catalog-viewer-clean'`
Expected: `PASS catalog-viewer-clean`

- [x] **Step 3.2: 공개 테스트 스위트 및 하네스 전체 검증을 실행한다.**

Run: `bash scripts/verify-public-test-suite.sh && bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh && git diff --check`
Expected: `PASS agentos-public-suite`, `PASS=27 FAIL=0`, `git diff --check` clean exit 0.

## 구현 결과

1. **unbundled 번들 스킬 자동 정리(prune) 기능 구현**:
   - `BundledInstallSummary`에 `pruned: int = 0` 필드를 추가했습니다.
   - `agentos/terminal/skills.py`의 `install_bundled_skills()`에서 매니페스트 상 `origin == "bundled"`로 기록되어 있으나 현재 `bundled_skill_sources()`(`DEFAULT_SKILL_NAMES`)에서 제외된 레거시 스킬 디렉터리를 `shutil.rmtree()`로 자동 삭제하고 매니페스트에서도 정리하도록 구현했습니다.
   - `origin != "bundled"`인 사용자 외부 커스텀 스킬은 삭제되지 않고 안전하게 보존됩니다.
   - `agentos/commands/setup.py` 콘솔 출력에 정리된 스킬 수가 있을 경우 `, 정리 N`이 표시되도록 했습니다.
   - 전용 단위 테스트 `tests/test_setup_bundled_prune.py`를 작성하여 정상 작동을 검증했습니다.
2. **유령 카탈로그 및 공개 경계 정합화**:
   - 소스 파일이 삭제되었으나 남아있던 `ascii-art`, `baoyu-comic`, `xlsx` 3개 항목을 `catalog/skills/catalog.json`에서 완전히 삭제했습니다.
   - `config/public-boundary.json`에서 위 3개 스킬 관련 경로 5개를 제거했습니다.
3. **전체 검증 완료**:
   - `pytest tests/test_setup_bundled_prune.py` 및 `pytest tests/test_setup_bootstrap.py` 통과.
   - 스킬 카탈로그 뷰어 생성 시 유령 스킬 스킵 경고 부재 확인 (`PASS catalog-viewer-clean`).
   - 공개 테스트 스위트 통과 (`PASS agentos-public-suite`).
   - 하네스 계약 테스트 27/27 통과 (`PASS=27 FAIL=0`).
   - `git diff --check` whitespace 무결성 확인.

## 사용 방법

- `agentos setup`을 실행하면 현재 번들 목록에서 제외된 구버전 번들 스킬이 전역 스킬 디렉터리(`~/.agentos/core/.agents/skills/`)에서 자동으로 안전하게 정리됩니다.
- `agentos project init` 실행 시 더 이상 실체 없는 유령 스킬(`baoyu-comic`, `ascii-art`, `xlsx`)이 선택창에 노출되지 않습니다.

## 완료 증거

- `PASS branch-preflight`
- `PASS ghost-skills-detected`
- `PASS summary-pruned-field`
- `PASS setup-imported`
- `tests/test_setup_bundled_prune.py::test_install_bundled_skills_prunes_obsolete_bundled_skill_and_preserves_custom PASSED`
- `PASS catalog-cleaned`
- `PASS boundary-cleaned`
- `PASS catalog-viewer-clean`
- `PASS agentos-public-suite`
- `PASS=27 FAIL=0` (27/27 harness contract tests passed)
- `git diff --check` clean

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active 디렉토리에 유지한다.
