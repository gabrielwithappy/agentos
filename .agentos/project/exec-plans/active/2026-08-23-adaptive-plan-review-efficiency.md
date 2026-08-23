---
status: 완료
date: 2026-08-23
reviewed: true
usability_review_required: true
user_request: 계획 리뷰가 핵심 위험과 성공 기준에 집중하고, 간단한 작업은 불필요한 LLM 리뷰 없이 문서 작성 후 바로 구현할 수 있도록 리뷰 정책·모델 라우팅·비용 상한을 개선한다.
active_agent: codex
active_session:
dashboard_item_id:
implementation_started_at: 2026-08-23T05:54:00Z
implementation_completed_at: 2026-08-23T06:12:00Z
implementation_duration: 약 18분
---

# 적응형 계획 리뷰 효율화 구현 계획

> **상태:** 완료
> reviewed: true
> **usability_review_required:** true

**목표:** 계획 리뷰가 목표·범위·위험·검증 가능성 같은 핵심만 판단하도록 리뷰 계약을 정리하고, 작업 위험도에 맞춰 리뷰 생략·경량 리뷰·전체 리뷰를 선택하게 한다.

**사용자 결과:** 간단한 작업은 짧은 자체 검증 후 바로 구현할 수 있고, 중요한 작업은 필요한 reviewer와 적절한 모델로만 검증되어 리뷰 품질과 실행 속도를 함께 확보한다.

**진행 상태:** 구현 및 focused verification 완료

**아키텍처:** 계획 생성 시 변경 surface와 위험 신호를 기준으로 `simple`, `standard`, `high-risk` 등급을 결정한다. 결정론적 policy 모듈은 필요한 reviewer, 허용 모델 class, 토큰·시간·재시도 상한만 반환한다. 실제 모델 호출과 provider usage 수집은 현재 runtime 범위 밖으로 두고, reviewer artifact에는 적용된 policy와 사용량이 제공될 때만 남긴다.

**기술 스택:** Markdown plan contract, Python review tooling, JSON review artifacts, pytest, Bash

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | tier policy, self-check gate, reviewer focus contract, template 및 회귀 테스트 구현 |
| 현재 위치 | 사용자 검토 및 archive 결정 대기 |
| 다음 단계 | 필요 시 실제 reviewer provider runner에 policy budget을 연결 |
| 완료 신호 | focused review suite, execution gate, signed review, manifest check PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 간단한 계획은 불필요한 리뷰 대기 없이 실행되고, 복잡하거나 위험한 계획은 필요한 리뷰만 수행된다. |
| 누구를 위한 것인가? | 계획을 작성·검토·실행하는 프로젝트 오너와 AgentOS reviewer runtime |
| 일상 사용에서 무엇이 달라지는가? | 리뷰가 문장·포맷의 사소한 차이보다 목표, 범위, 위험, 검증 누락을 우선 지적하며 리뷰 시간과 LLM 사용량을 확인할 수 있다. |
| 무엇은 바뀌지 않는가? | protected path, 보안·credential, 데이터 손실, 외부 서비스, 사용자 동작 변경 작업의 독립 리뷰 의무와 인간 승인 경계는 유지된다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 리뷰 등급 계약 | 계획이 변경 surface와 위험도에 따라 review path를 선택함 | `writing-plans` skill, plan template, review classifier | representative plan matrix PASS |
| 2. 핵심 리뷰 계약 | reviewer가 목표·범위·위험·검증·회귀만 보고 문체·사소한 표현은 무시함 | `plan-reviewer`, `principle-auditor`, `usability-reviewer` instructions | in-scope/out-of-scope fixture PASS |
| 3. 모델·예산 라우팅 | simple/standard/high-risk에 맞는 모델과 토큰·시간 상한이 적용됨 | review request runner/config | routing and budget tests PASS |
| 4. 생략·에스컬레이션 | simple 작업은 self-check 후 실행 가능하고 위험 신호가 있으면 full review로 승격됨 | execution gate, plan lifecycle, review artifact validator | skip/escalation regression PASS |
| 5. 관측 및 회귀 | 리뷰 시간·토큰·재시도·발견 이슈가 기록되고 품질 저하를 감시함 | review artifact schema, metrics/tests, docs | schema and metric contract PASS |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, review artifacts, lifecycle board, evolution status
- durable result surface: `AGENTS.md`, `.agents/skills/harness/writing-plans/`, `.agents/agents/harness/`, review tooling/tests, project plan template
- documentation-only exception: 없음. 최종 결과는 실행 정책과 검증 도구의 동작 변경이다.

## File Structure

- 수정: `AGENTS.md` - 난이도별 리뷰 의무와 simple skip의 상위 정책
- 수정: `.agents/skills/harness/writing-plans/SKILL.md` - review matrix, 핵심성 기준, skip/escalation, model budget contract
- 수정: `.agentos/project/exec-plans/TEMPLATE.md` - 계획에 `review_tier`, `review_required`, `review_budget`를 선언하는 필드
- 수정: `.agents/agents/harness/plan-reviewer.md` - in-scope/out-of-scope와 finding severity contract
- 수정: `.agents/agents/harness/principle-auditor.md` - 구조·보안·protected path 위험만 심층 검토
- 수정: `.agents/agents/harness/usability-reviewer.md` - 실제 user-facing 변화가 있을 때만 호출되는 조건과 복구성 기준
- 생성: `.agents/skills/harness/writing-plans/scripts/review_policy.py` - 등급 분류, reviewer set, 모델 class, 예산, 승격 신호의 단일 정책
- 수정: `.agents/skills/harness/writing-plans/scripts/request_review.py` - policy profile을 signed review request에 기록
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py` - skip self-check와 standard/high-risk artifact provenance 검증
- 수정: `.agents/skills/harness/writing-plans/scripts/execution_gate.py` - `review_required=false`의 self-check·scope 경계와 승격 판정
- 생성: `tests/test_adaptive_plan_review.py` - 분류·라우팅·skip·escalation·예산·artifact contract 회귀 테스트
- 수정: `tests/`의 기존 plan/review 테스트 - mandatory full review 가정과 새 matrix 정합성 반영
- 수정: `.agents/skills/harness/_version.json` - protected skill/agent 구조 변경 후 manifest sync 결과

## Review Policy Matrix

| 등급 | 기본 조건 | 리뷰 동작 | 모델/예산 정책 |
|---|---|---|---|
| `simple` | 최대 두 개의 Markdown 문서만 바꾸며, protected path·보안·데이터·외부 연동·setup/onboarding·CLI 동작 변경이 없음 | reviewer 호출 생략 가능; 작성자 self-check와 deterministic validation만 수행 | LLM 0회, 고정 명령 검증만 |
| `standard` | 일반 기능·버그·여러 파일 변경이나 high-risk 신호 없음 | `plan-reviewer` 1회 | 경량 model class, 최대 3,000 tokens / 120 seconds / 1회 |
| `high-risk` | protected path, AGENTS/skill/reviewer contract, credential·보안·데이터 삭제, 외부 서비스, CLI/setup/onboarding/error behavior, architecture migration | 독립 `plan-reviewer` + `principle-auditor`; 실제 user interaction을 바꾸면 `usability-reviewer` 추가 | capable model class, reviewer당 최대 8,000 tokens / 300 seconds / 2회 |

`simple`은 분류 결과만으로 허용되지 않는다. 계획의 declared scope와 실제 diff가 일치하고 deterministic checks가 통과해야 하며, 위험 신호가 하나라도 발견되면 `standard` 또는 `high-risk`로 승격한다.

## 핵심 리뷰 범위

Reviewer는 아래 항목만 FAIL 사유로 삼는다.

- 사용자 목표와 결과의 불일치
- 범위 누락·범위 확장·파일 ownership 불일치
- 보안, 데이터 손실, protected path, 권한 또는 prompt boundary 위험
- 실행 순서·의존성·rollback·검증 기준의 누락
- 사용자 동작이나 복구 경로를 실제로 깨뜨리는 안내·오류 메시지 문제

다음은 위 핵심 항목에 영향을 주지 않으면 finding으로 만들지 않는다.

- 문장 선호, 번역 어투, 제목·표현의 미세한 차이
- 구현자의 취향 차이인 변수명·명령어 표기
- 이미 `Run:`/`Expected:`와 scope fence로 닫힌 세부 설명의 반복
- 계획의 성공이나 안전성에 영향을 주지 않는 추가 아이디어

## Task 0: 정책 사전 검증 및 reviewer fixture 정의

**사용자에게 보이는 마일스톤:** 기존 계획을 실제 위험도별로 분류할 수 있는 기준과 대표 fixture가 준비된다.

- [x] **Step 1:** 대표 plan surface를 `simple`/`standard`/`high-risk`로 분류하고 오분류 사례를 고정한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'classifier or matrix' -q`
Expected: `PASS plan-review-matrix`

- [x] **Step 2:** 각 reviewer의 in-scope/out-of-scope와 blocking severity를 정의한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'scope or severity or finding' -q`
Expected: `PASS review-fixture-contract`

## Task 1: 난이도·위험도 분류와 review policy contract 구현

**사용자에게 보이는 마일스톤:** 계획 작성 시 review tier, reviewer 필요 여부, 모델·예산이 자동으로 결정된다.

- [x] **Step 1:** plan frontmatter/template에 `review_tier`, `review_required`, `review_budget`, `review_reason` 필드를 추가하고 classifier가 안전한 default를 적용한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'frontmatter or default or tier' -q`
Expected: `PASS adaptive-plan-frontmatter`

- [x] **Step 2:** protected path·security·external service·user-facing·multi-file signals와 simple allowlist를 deterministic classifier로 구현한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'classif or protected or escalation' -q`
Expected: `PASS adaptive-plan-classifier`

## Task 2: 핵심성 중심 reviewer contract와 모델 라우팅 구현

**사용자에게 보이는 마일스톤:** reviewer가 핵심 위험만 보고, 단순 작업에는 과도한 모델과 reviewer가 호출되지 않는다.

- [x] **Step 1:** 세 reviewer 지침에 공통 severity·out-of-scope·max findings·stop condition을 추가한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'scope or severity or finding' -q`
Expected: `PASS reviewer-focus-contract`

- [x] **Step 2:** tier별 reviewer set, model class, token/time budget, retry count를 선언형 policy로 라우팅하고 actual usage가 없는 runtime에서 usage 측정을 주장하지 않는다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'routing or model or budget or retry' -q`
Expected: `PASS review-routing-budget`

## Task 3: simple skip, escalation, artifact provenance 구현

**사용자에게 보이는 마일스톤:** 간단한 작업은 즉시 실행되고, 위험 신호가 감지되면 자동으로 full review로 승격된다.

- [x] **Step 1:** `review_required=false` 허용 조건과 self-check 결과를 execution gate가 검증한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'skip or self_check or execution_gate' -q`
Expected: `PASS simple-review-skip`

- [x] **Step 2:** plan content hash 또는 declared scope/dependency 변경이 tier를 올리면 기존 review artifact를 invalid 상태로 만들고 required reviewer를 재호출한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'diff or stale or reclassif or escalate' -q`
Expected: `PASS review-escalation`

- [x] **Step 3:** skip/lightweight/full 결과 모두 plan hash, classifier version, model class, token/time usage가 제공된 경우의 기록, reason, timestamp를 artifact에 기록한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'artifact or provenance or schema' -q`
Expected: `PASS review-artifact-provenance`

## Task 4: 관측·문서·회귀 검증

**사용자에게 보이는 마일스톤:** 리뷰 절감 효과와 품질 저하 여부를 나중에 수치로 확인할 수 있다.

- [x] **Step 1:** policy tier, reviewer set, 허용 model class, token/time/retry budget, 실제 usage가 제공된 경우의 optional usage를 artifact에 기록한다.

Run: `pytest tests/test_adaptive_plan_review.py -k 'metrics or usage or duration' -q`
Expected: `PASS review-metrics`

- [x] **Step 2:** 사용자 문서와 reviewer 운영 문서에 tier별 실제 사용법·승격·복구 경로를 반영한다.

Run: `rg -n 'simple|standard|high-risk|review_required|review_budget|escalat' .agents/skills/harness/writing-plans .agents/agents/harness AGENTS.md`
Expected: 모든 정책 용어와 복구 경로가 문서에 존재

- [x] **Step 3:** 전체 관련 suite와 manifest를 실행한다.

Run: `pytest tests/test_adaptive_plan_review.py tests/test_plan_parser.py tests/test_cli_contract.py -q && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `PASS adaptive-plan-review-suite` 및 manifest `[PASS]`

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: reviewer runner, plan parser, execution gate, manifest, existing tests

## 리뷰 반영 이력

- [Gate 2 fallback plan-reviewer] 현재 runtime이 실제 provider usage 수집과 모델 호출을 하지 않는데 계획이 이를 전제함 → 결정론적 policy profile과 optional usage artifact로 범위를 축소했다.
- [Gate 2 fallback principle-auditor] 단순 작업의 정의가 넓어 protected/user-facing 경계를 우회할 위험이 있음 → Markdown 최대 두 파일, explicit 위험 신호, scope/diff mismatch escalation 조건을 추가했다.
- [Gate 2 fallback usability-reviewer] reviewer 호출 생략 시 사용자에게 이유와 복구 경로가 불명확함 → tier/reason/self-check artifact와 high-risk escalation·execution-gate recovery를 계획에 추가했다.

## 구현 결과

- `review_policy.py`가 plan surface에서 `simple`, `standard`, `high-risk` tier와 reviewer/model/budget profile을 결정한다.
- `simple` plan은 실제 validator를 적은 self-check artifact가 있어야 execution gate를 통과하며, plan content 또는 declared scope가 바뀌면 self-check hash가 무효화된다.
- `standard`는 plan reviewer 한 명만, `high-risk`는 principle audit과 필요 시 usability review를 추가로 요구한다.
- reviewer 지침은 목표·범위·위험·검증·회귀만 blocking finding으로 허용하고 최대 다섯 개에서 종료한다.

## 사용 방법

- 새 plan은 template의 `review_*` 필드를 참고용으로 채운다. 실제 tier는 declared change surface로 계산된다.
- simple plan은 `review_artifacts.py self-check --plan <path> --summary <summary> --validator <passed-command>`로 self-check를 기록한다.
- standard/high-risk plan은 기존 reviewer artifact와 `request_review.py <plan-path>` signed review를 사용한다.
- execution gate가 실패하면 출력된 recovery command를 사용하고, scope가 커지면 tier를 낮추지 말고 재분류한다.

## 완료 증거

- PASS `uv run pytest tests/test_adaptive_plan_review.py tests/test_cryptographic_hook.py tests/test_plan_parser.py tests/test_plan_events.py tests/test_setup_bootstrap.py -q` (50 passed)
- PASS current high-risk plan `review_artifacts.py check`, `execution_gate.py`, `request_review.py`
- PASS `sync-manifest.sh --update codex` 및 `--check`
- PASS `git diff --check`
- Baseline known: harness aggregate suite는 이번 변경 전과 같은 `24 PASS / 30 FAIL` 상태이며, focused review suite와 별도로 추적한다.

## 아카이브 결정

이 계획은 active에 유지하며, 사용자가 명시적으로 archive를 요청할 때만 lifecycle 명령으로 이동한다.
