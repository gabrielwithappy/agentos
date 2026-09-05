---
status: 완료
date: 2026-09-05
reviewed: true
usability_review_required: false
user_request: harness-loop, mcp, agent-token-info 스킬 삭제
active_agent: antigravity
active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: chore/remove-legacy-harness-skills)
dashboard_item_id:
implementation_started_at: 2026-09-05T02:33:00Z
implementation_completed_at: 2026-09-05T02:35:00Z
implementation_duration: 2m
next_action: user archive decision
---

# harness-loop, mcp, agent-token-info 레거시 하네스 스킬 제거 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 사용하지 않는 레거시 하네스 스킬인 `harness-loop`, `mcp`, `agent-token-info` 스킬 디렉터리를 삭제하고, 관련 레지스트리(`catalog/skills/catalog.json`, `config/public-boundary.json`, `.agents/skills/README.md`)를 정합화하여 하네스 표면을 단순화한다.

**사용자 결과 요약:**
- 불필요하고 중복되거나 비활성화된 3개 레거시 스킬이 제거되어 스킬 카탈로그와 하네스 탐색 표면이 명확해지며, 카탈로그 뷰어 및 하네스 테스트가 군더더기 없이 통과한다.

**의존성 분석:**
- 외부 의존성: 없음
- 내부 선행 조건: `feature/knowledge-curator-path-normalization`이 `main`에 병합 완료됨. 다른 active 계획과 충돌 없음.
- 스캔 기준: Git 상태, `catalog/skills/catalog.json`, `config/public-boundary.json`, `.agents/skills/README.md`, 하네스 테스트, public suite.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, `HISTORY.md`, generated plan board
- Durable Result Surface: `.agents/skills/harness/`, `catalog/skills/catalog.json`, `config/public-boundary.json`, `.agents/skills/README.md`
- Documentation-Only Exception: 없음. 실제 파일 삭제 및 레지스트리 정리 작업이다.

**진행 상태:** 계획 초안 작성, 독립 리뷰 대기 중

**아키텍처:**
- `.agents/skills/harness/agent-token-info/`, `.agents/skills/harness/harness-loop/`, `.agents/skills/harness/mcp/` 3개 디렉터리를 제거한다.
- `catalog/skills/catalog.json`에서 위 3개 스킬 항목을 삭제한다.
- `config/public-boundary.json`에서 위 3개 스킬 경로를 제거한다.
- `.agents/skills/README.md`의 Core Skills 목록에서 삭제된 스킬명을 제거한다.
- `.agents/skills/harness/run-all-tests/tests/harness/test_harness_portability_contract.sh`에서 삭제된 파일 예외 경로를 정리한다.

**기술 스택:** Git, Markdown, JSON, Python 3.11+, pytest, 기존 catalog viewer 및 public verifier

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 대상 스킬 3종 삭제, 카탈로그/경계/문서 정합화, 공개/하네스 테스트 전체 통과 |
| 현재 위치 | 구현 및 검증 완료 |
| 다음 단계 | 커밋, 푸시, PR 병합 및 아카이브 결정 |
| 완료 신호 | 대상 스킬 3종 및 카탈로그/경계 참조 제거 완료, 하네스 및 공개 테스트 스위트 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 불필요한 레거시 하네스 스킬이 정리된 깔끔한 스킬 디렉터리와 카탈로그 |
| 누구를 위한 것인가? | AgentOS를 탐색하고 스킬을 사용하는 개발자와 에이전트 |
| 일상 사용에서 무엇이 달라지는가? | 스킬 카탈로그 뷰어 및 목록에서 불필요한 스킬이 노출되지 않으며 인지 부하가 감소함 |
| 무엇은 바뀌지 않는가? | core-engine 내부 스크립트 기능, 타 정상 하네스 스킬, 기존 문서/테스트 무결성 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 스킬 디렉터리 안전 삭제 | 대상 3개 스킬 디렉터리가 Git에서 안전하게 제거됨 | `.agents/skills/harness/` | `git rm` 및 디렉터리 부재 확인 |
| 2. 카탈로그 및 공개 경계 정합화 | catalog.json, public-boundary, README에서 참조 제거 | catalog.json, public-boundary.json, README.md | python json 검증 및 grep 부재 확인 |
| 3. 전체 검증 및 계약 테스트 | 카탈로그 뷰어 정상 생성 및 하네스/공개 테스트 PASS | tests, harness suite, public suite | 27/27 하네스 통과, public suite PASS |

## 리뷰 반영 이력

- 계획 초안: 사용자 요청에 따라 harness-loop, mcp, agent-token-info 3개 레거시 스킬 삭제 및 메타데이터 정합화 수립.

## 사전 실행 Gate와 closeout 경계

- 이 계획은 `.agents/` surface의 파일 삭제를 포함하므로 Gate 2 PASS를 구현 전에 확인한다.
- reviewer artifact 생성·검증 및 closeout은 구현 Task가 아니라 Gate 2와 closeout 절차에서 처리한다.

## 리뷰 범위

- 변경 범위:
  - `.agents/skills/harness/agent-token-info/**` (삭제)
  - `.agents/skills/harness/harness-loop/**` (삭제)
  - `.agents/skills/harness/mcp/**` (삭제)
  - `catalog/skills/catalog.json` (수정)
  - `config/public-boundary.json` (수정)
  - `.agents/skills/README.md` (수정)
  - `.agents/skills/harness/run-all-tests/tests/harness/test_harness_portability_contract.sh` (수정)
- required review: `plan-reviewer` PASS, `principle-auditor` PASS/CLEAN
- recovery: `git checkout` 또는 `git restore`로 삭제된 파일 및 변경 사항을 롤백한다.

## Task 0: 실행 전 기준 및 선행 조건 확인

**파일:**
- 읽기: `catalog/skills/catalog.json`, `config/public-boundary.json`, `.agents/skills/README.md`
- 수정: 없음

**사용자에게 보이는 마일스톤:** 삭제 대상 스킬의 존재 여부와 브랜치 상태가 확인된다.

- [x] **Step 0.1: feature 브랜치 상태를 확인한다.**

Run: `test "$(git branch --show-current)" = "chore/remove-legacy-harness-skills" && git status --short && echo 'PASS branch-preflight'`
Expected: `PASS branch-preflight`

- [x] **Step 0.2: 삭제 대상 3개 스킬의 존재 여부를 확인한다.**

Run: `test -d .agents/skills/harness/agent-token-info && test -d .agents/skills/harness/harness-loop && test -d .agents/skills/harness/mcp && echo 'PASS preflight-skills-exist'`
Expected: `PASS preflight-skills-exist`

## Task 1: 대상 스킬 디렉터리 삭제

**파일:**
- 삭제: `.agents/skills/harness/agent-token-info/**`
- 삭제: `.agents/skills/harness/harness-loop/**`
- 삭제: `.agents/skills/harness/mcp/**`

**사용자에게 보이는 마일스톤:** 3개 스킬 디렉터리가 저장소에서 안전하게 제거된다.

- [x] **Step 1.1: Git 명령어로 3개 스킬 디렉터리를 삭제한다.**

Run: `git rm -r .agents/skills/harness/agent-token-info .agents/skills/harness/harness-loop .agents/skills/harness/mcp && ! test -e .agents/skills/harness/agent-token-info && ! test -e .agents/skills/harness/harness-loop && ! test -e .agents/skills/harness/mcp && echo 'PASS skills-removed'`
Expected: `PASS skills-removed`

## Task 2: 카탈로그, 공개 경계 및 참조 문서 정합화

**파일:**
- 수정: `catalog/skills/catalog.json`
- 수정: `config/public-boundary.json`
- 수정: `.agents/skills/README.md`
- 수정: `.agents/skills/harness/run-all-tests/tests/harness/test_harness_portability_contract.sh`

**사용자에게 보이는 마일스톤:** 삭제된 스킬에 대한 카탈로그 항목과 경로가 정리된다.

- [x] **Step 2.1: catalog/skills/catalog.json에서 3개 스킬 항목을 삭제한다.**

Run: `python3 -c "import json; p='catalog/skills/catalog.json'; d=json.load(open(p)); targets={'agent-token-info', 'harness-loop', 'mcp'}; d['skills']=[s for s in d['skills'] if s['name'] not in targets]; json.dump(d, open(p, 'w'), indent=2); print('catalog-updated')"`
Expected: `catalog-updated`

Run: `python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); names={s['name'] for s in d['skills']}; assert not names & {'agent-token-info', 'harness-loop', 'mcp'}; print('PASS catalog-cleaned')"`
Expected: `PASS catalog-cleaned`

- [x] **Step 2.2: config/public-boundary.json에서 삭제된 스킬 경로를 제거한다.**

Run: `python3 -c "import json; p='config/public-boundary.json'; d=json.load(open(p)); remove_prefixes=('.agents/skills/harness/agent-token-info/', '.agents/skills/harness/harness-loop/', '.agents/skills/harness/mcp/'); d['paths']=[f for f in d['paths'] if not any(f.startswith(prefix) for prefix in remove_prefixes)]; json.dump(d, open(p, 'w'), indent=2); print('boundary-updated')"`
Expected: `boundary-updated`

Run: `python3 -c "import json; d=json.load(open('config/public-boundary.json')); assert not any(any(f.startswith(p) for p in ('.agents/skills/harness/agent-token-info/', '.agents/skills/harness/harness-loop/', '.agents/skills/harness/mcp/')) for f in d['paths']); print('PASS public-boundary-cleaned')"`
Expected: `PASS public-boundary-cleaned`

- [x] **Step 2.3: .agents/skills/README.md 및 테스트 참조를 정리한다.**

Run: `python3 -c "p='.agents/skills/README.md'; text=open(p).read(); text=text.replace('- \`harness-loop\`\n', '').replace('- \`mcp\`\n', ''); open(p, 'w').write(text); print('readme-updated')"`
Expected: `readme-updated`

Run: `python3 -c "p='.agents/skills/harness/run-all-tests/tests/harness/test_harness_portability_contract.sh'; text=open(p).read(); text=text.replace('    \".agents/skills/harness/harness-loop/SKILL.md:/tmp/harness-loop.out\",\n', ''); open(p, 'w').write(text); print('portability-contract-updated')"`
Expected: `portability-contract-updated`

## Task 3: 전체 무결성 및 검증

**파일:**
- 검증: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py`, `scripts/verify-public-test-suite.sh`, `.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`, `pytest -q`

**사용자에게 보이는 마일스톤:** 카탈로그 뷰어가 정상 생성되고 하네스 및 공개 테스트 스위트가 모두 통과한다.

- [x] **Step 3.1: 카탈로그 뷰어 생성을 검증한다.**

Run: `catalog_tmp=$(mktemp -d) && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output "$catalog_tmp/index.html" 2>"$catalog_tmp/stderr" && ! grep -q 'skipping agent-token-info\|skipping harness-loop\|skipping mcp' "$catalog_tmp/stderr" && echo 'PASS catalog-viewer-clean'`
Expected: `PASS catalog-viewer-clean`

- [x] **Step 3.2: 공개 테스트 스위트 및 하네스 전체 검증을 실행한다.**

Run: `bash scripts/verify-public-test-suite.sh && bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh && git diff --check`
Expected: `PASS agentos-public-suite`, `PASS=27 FAIL=0`, `git diff --check` clean exit 0.

## 구현 결과

1. **레거시 하네스 스킬 3종 제거**:
   - `.agents/skills/harness/agent-token-info/` (SKILL.md) 삭제 완료.
   - `.agents/skills/harness/harness-loop/` (SKILL.md) 삭제 완료. (`.agents/skills/harness/core-engine/scripts/harness-loop.sh`는 core-engine 스크립트로서 온전히 보존됨)
   - `.agents/skills/harness/mcp/` (SKILL.md, resources/mcp-catalog.json) 삭제 완료.
2. **카탈로그 및 공개 경계 정합화**:
   - `catalog/skills/catalog.json`: 3개 스킬 레지스트리 항목 제거.
   - `config/public-boundary.json`: 삭제된 4개 파일 경로 제거.
   - `.agents/skills/README.md`: Core Skills 목록에서 `harness-loop` 및 `mcp` 제거.
   - `test_harness_portability_contract.sh`: 삭제된 `harness-loop/SKILL.md`에 대한 예외 항목 정리.
3. **정합성 및 검증 완료**:
   - 스킬 카탈로그 뷰어(`generate_html.py`)에서 누락 경고 없이 정상 렌더링 검증 통과 (`PASS catalog-viewer-clean`).
   - 공개 테스트 스위트(`verify-public-test-suite.sh`) 통과 (`PASS agentos-public-suite`).
   - 하네스 테스트 스위트(`run_harness_tests.sh`) 27/27 통과 (`PASS=27 FAIL=0`).
   - Git whitespace diff 검사(`git diff --check`) 정상 통과.

## 사용 방법

- 더 이상 레거시 3개 스킬(`agent-token-info`, `harness-loop`, `mcp`)이 스킬 카탈로그나 하네스 탐색 표면에 노출되지 않습니다.
- 하네스 루프 스크립트는 기존과 동일하게 `.agents/skills/harness/core-engine/scripts/harness-loop.sh`로 직접 실행 가능합니다.
- 스킬 카탈로그 뷰어 확인:
  ```bash
  python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output catalog.html
  ```

## 완료 증거

- `PASS branch-preflight`
- `PASS preflight-skills-exist`
- `PASS skills-removed`
- `PASS catalog-cleaned`
- `PASS public-boundary-cleaned`
- `PASS catalog-viewer-clean`
- `PASS agentos-public-suite`
- `PASS=27 FAIL=0` (27/27 harness contract tests passed)
- `git diff --check` clean

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active 디렉토리에 유지한다.
