# it-trend-report 장기지식 저장 흐름 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-25<br>
> reviewed: true<br>
> user_request: `it-trend-report` 스킬의 장기지식 저장 동작을 점검하고 올바르게 수정한다.<br>
> active_agent: codex<br>
> active_session: feature/it-trend-report-knowledge-flow<br>
> implementation_started_at: 2026-08-25T14:04:00Z<br>
> implementation_completed_at: 2026-08-25T14:12:00Z<br>
> implementation_duration: 약 8분<br>

**목표:** IT trend 실행 결과가 저장소 루트 기준의 날짜별 실행 근거와 `docs/knowledge` 최종 지식으로 정확히 분리되도록 스킬을 수정한다.

**사용자 결과:** 사용자는 저장소 루트에서 주간 파이프라인을 실행하고, 검토된 리포트를 `docs/knowledge/concepts/it-trend-reports/`에 남길 수 있으며, 실행은 자동으로 commit/push하지 않는다.

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:** 기존 단계형 파이프라인을 유지한다. 실행 스크립트는 저장소 루트를 스스로 결정하고 `runs/YYYY-MM-DD/`와 `docs/knowledge/...`를 연결하지만 Git 원격 변경은 수행하지 않는다.

**기술 스택:** Python 3 표준 라이브러리 HTML parser, PyYAML, Markdown, OKF v0.2

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 리뷰, 경로/부작용 수정, 표준 parser 전환, smoke tests, 최종 검증 |
| 현재 위치 | 구현 및 자동 검증 완료 |
| 다음 단계 | 사용자가 diff를 검토하고 commit/PR 여부 결정 |
| 완료 신호 | 3개 smoke tests PASS, skill validator PASS, forbidden-pattern scan PASS, OKF validate `"ok": true` |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 재현 가능한 IT trend 실행과 올바른 `docs/knowledge` 저장 경로 |
| 누구를 위한 것인가? | `knowledge-agent` 운영자와 장기지식을 작성하는 에이전트 |
| 일상 사용에서 무엇이 달라지는가? | `runs/YYYY-MM-DD`는 증거, `docs/knowledge/...`는 검토된 결과로 고정되고 push는 수동이다 |
| 무엇은 바뀌지 않는가? | 기존 OKF 콘텐츠, source 목록의 의미, knowledge-curator의 backup/sync 계약 |

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, review traces, 변경 diff
- durable result surface: `knowledge-agent/skills/it-trend-report/` 및 해당 스킬의 테스트
- documentation-only exception: 없음. 실행 스크립트의 경로·부작용 동작도 수정한다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 실행 경로 정정 | 날짜별 run과 최종 knowledge 경로가 저장소 루트 기준으로 동작 | `run_weekly_trend.py`, `generate_final_report.py`, README/SKILL | unittest smoke tests |
| 2. 부작용 제거 | 실행만으로 commit/push/config 변경이 발생하지 않음 | `run_weekly_trend.py` | forbidden-pattern scan 및 테스트 |
| 3. bundle 회귀 확인 | 기존 장기지식 OKF 구조가 유효함 | `docs/knowledge` | knowledge-curator validate |

## 의존성 분석

- 외부 의존성: 아래에 선언함
- 스캔 기준: Python 3, PyYAML, BeautifulSoup, 기존 CLI와 계획의 모든 `Run:` 명령

## 의존성 게이트

### PyYAML
- name: PyYAML
- type: nonstandard-local-tool
- required: true
- purpose: source extraction run configuration parsing
- preflight:
  Run: `python3 -c 'import yaml; print("PASS parser-deps-ready")'`
  Expected: `PASS parser-deps-ready`
- fallback:
  available: true
  trigger: extraction is not exercised in offline smoke tests
  action: run pipeline and report-generation tests with fixture JSON/empty sources
  limits: live URL extraction is not verified
  verification:
    Run: `python3 -c 'import unittest; print("PASS offline-fallback-ready")'`
    Expected: `PASS offline-fallback-ready`
- failure_behavior: use_fallback

## 파일 구조

- 수정: `knowledge-agent/skills/it-trend-report/SKILL.md` — 실행·검토·저장 경계
- 수정: `knowledge-agent/skills/it-trend-report/README.md` — 실제 명령과 수동 publish 흐름
- 수정: `knowledge-agent/skills/it-trend-report/scripts/run_weekly_trend.py` — 날짜/루트/부작용 정정
- 수정: `knowledge-agent/skills/it-trend-report/scripts/generate_final_report.py` — 하드코딩 제거 및 CLI 인자화
- 생성: `knowledge-agent/skills/it-trend-report/tests/test_scripts.py` — 오프라인 smoke tests

## Task 0: 리뷰·의존성·보호 경계 확인

**사용자에게 보이는 마일스톤:** 구현 전에 대상 범위와 외부 의존성 상태가 고정된다.

- [x] **Step 0.1: Gate 2 리뷰 증거를 기록한다.**

Run: `test -f .agents/traces/audit-plan-review-it-trend-report-knowledge-flow.md && test -f .agents/traces/audit-principle-it-trend-report-knowledge-flow.md && test -f .agents/traces/audit-usability-it-trend-report-knowledge-flow.md`
Expected: `exit 0`

- [x] **Step 0.2: parser dependency preflight를 실행한다.**

Run: `python3 -c 'import yaml; print("PASS parser-deps-ready")'`
Expected: `PASS parser-deps-ready`

## Task 1: 실행 스크립트의 저장 경로와 부작용 수정

**파일:** `run_weekly_trend.py`, `generate_final_report.py`

**사용자에게 보이는 마일스톤:** 저장소 어디서 실행해도 날짜별 run과 최종 리포트 경로가 올바르고, 자동 commit/push가 없다.

- [x] **Step 1.1: 저장소 루트와 `--run-date`/`--run-dir`를 명시적으로 지원한다.**

Run: `python3 knowledge-agent/skills/it-trend-report/scripts/run_weekly_trend.py --help && python3 knowledge-agent/skills/it-trend-report/scripts/generate_final_report.py --help`
Expected: 두 help에 실행 날짜/경로 인자가 표시되고 exit 0

- [x] **Step 1.2: 리포트 생성기를 fixture run과 output path로 실행한다.**

Run: `python3 -m unittest discover -s knowledge-agent/skills/it-trend-report/tests -v`
Expected: 모든 smoke test PASS

## Task 2: 사용자 문서와 장기지식 계약 정합화

**파일:** `SKILL.md`, `README.md`

**사용자에게 보이는 마일스톤:** 실행 증거와 검토된 장기지식의 역할, 수동 backup/sync 경계가 문서와 코드에 일치한다.

- [x] **Step 2.1: run 경로·검토·수동 publish 흐름을 문서화한다.**

Run: `rg -n "runs/YYYY-MM-DD|docs/knowledge/concepts/it-trend-reports|backup|sync|commit|push|review" knowledge-agent/skills/it-trend-report/SKILL.md knowledge-agent/skills/it-trend-report/README.md`
Expected: 각 경계와 수동 publish 안내가 검색됨

- [x] **Step 2.2: 금지된 하드코딩·자동 원격 변경 패턴을 검사한다.**

Run: `! rg -n 'runs/today|/root/workspace|\["git"|git", "(push|commit|config|add)' knowledge-agent/skills/it-trend-report/scripts`
Expected: 출력 없음, exit 0

## Task 3: 최종 검증

- [x] **Step 3.1: skill 형식과 전체 OKF bundle을 검증한다.**

Run: `python3 /home/gabriel/.codex/skills/.system/skill-creator/scripts/quick_validate.py knowledge-agent/skills/it-trend-report && python3 -S knowledge-agent/skills/knowledge-curator/scripts/knowledge.py validate --project knowledge-agent/docs/knowledge`
Expected: `Skill is valid!`, JSON `"ok": true`, exit 0

- [x] **Step 3.2: 변경 범위를 확인한다.**

Run: `git diff --check && git status --short --branch`
Expected: whitespace 오류 없음; 기존 사용자 변경은 보존되고 계획 범위 밖 삭제/원격 변경 없음

## 리뷰 반영 이력

- Gate 2 증거가 생성되기 전에는 `reviewed: true`로 전환하지 않는다.
- 현재 런타임에 서브에이전트 호출 도구가 없으면 AGENTS.md 허용 fallback으로 reviewer trace를 남긴다.

## 구현 결과

- `run_weekly_trend.py`: 저장소 루트 자동 판별, `--run-date`/`--run-dir`/`--output` 지원, `runs/YYYY-MM-DD` 사용
- `generate_final_report.py`: `/root/workspace` 하드코딩 제거, 명시적 CLI, fixture evidence만 리포트에 반영
- `extract_sources.py`: 설치되지 않은 BeautifulSoup 의존성을 표준 `HTMLParser`로 대체
- 자동 `git config`, `git add`, `git commit`, `git push` 제거
- 스킬 문서에 `docs/knowledge` 장기지식과 `runs/` 실행증거 경계 및 수동 publish 흐름 반영
- 오프라인 smoke tests 3개 추가

## 사용 방법

저장소 루트에서 실행한다:

```bash
python3 skills/it-trend-report/scripts/run_weekly_trend.py --run-date YYYY-MM-DD
python3 skills/knowledge-curator/scripts/knowledge.py validate --project docs/knowledge
```

리포트를 사람이 검토한 뒤 `knowledge-curator backup`과 필요 시 명시적 `sync`를 실행한다. 실행 스킬 자체는 원격 변경을 수행하지 않는다.

## 완료 증거

- `python3 -m unittest discover -s knowledge-agent/skills/it-trend-report/tests -v` → 3 tests OK
- `quick_validate.py knowledge-agent/skills/it-trend-report` → `Skill is valid!`
- 금지 패턴 검사 → 출력 없음
- `knowledge.py validate --project knowledge-agent/docs/knowledge` → exit 0, `"ok": true`
- `py_compile` 및 `git diff --check` → PASS
- 기존 bundle의 advisory warning 2건은 기존 `2026-08-24-weekly.md` 메타데이터이며 이번 구현 범위 밖이다.

## 아카이브 결정

이 계획은 완료 증거를 남긴 active plan으로 유지한다. 사용자가 별도 archive를 요청하면 lifecycle 도구로 보관한다.
