# Gate 2 리뷰 게이트 Python 3.9 크래시 및 해시 무효화 버그 수정 계획

> **상태:** 완료
> **작성일:** 2026-08-01<br>
> reviewed: true<br>
> usability_review_required: true<br>
> gate2_plan_reviewer: PASS<br>
> gate2_principle_auditor: PASS<br>
> gate2_usability_reviewer: PASS<br>
> user_request: Stop 훅에서 `stop_review_gate.py`가 `TypeError`로 죽는 문제를 발견해 수정을 요청받음. 원인 분석 중 별도로, Gate 2 서명 이후 정당한 계획 문서 편집(구현 타임스탬프, 체크박스, 구현 결과 섹션 등)이 서명 해시를 항상 무효화시키는 구조적 버그를 추가로 발견해 함께 수정. 사용자가 이 변경이 `.agents/` 보호 경로(harness governance)에 해당함을 지적해, 소급 계획 문서 작성 후 Gate 2 리뷰를 거치기로 함. 1차 Gate 2 리뷰에서 3개 리뷰어 전원 FAIL 판정 — 실제 잔존 버그(cwd 미포함 시 크래시)와 프로세스 누락(protected path governance step 없음, 회귀 테스트 없음, 인용 오류)을 지적받아 코드/문서 모두 수정 후 재리뷰.<br>
> active_agent: Claude Code<br>
> active_session: f145077e-dbba-4d91-8e7c-412b076b55b9<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg039wc<br>
> implementation_started_at: 2026-08-01T01:00:00Z<br>
> implementation_completed_at: 2026-08-01T01:23:00Z<br>
> implementation_duration: 약 23분(1차 구현 + Gate 2 FAIL 3건 반영 재구현 포함)<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** (1) `stop_review_gate.py`가 Python 3.9(시스템 `python3`)에서 크래시하는 문제를 고치고, (2) Gate 2 서명 이후 정당한 계획 문서 편집이 서명을 영구히 무효화시키는 `normalize_plan_text()`의 구조적 결함을 고쳐, 방금 도입된 암호학적 리뷰 게이트(PR #49)가 실제로 지속 가능하게 동작하도록 한다.

**사용자 결과:** Stop 훅이 `cwd` 유무와 무관하게 크래시 없이 정상 종료하고, "완료" 처리된 계획 문서가 자기 자신의 Gate 2 서명을 영구히 깨뜨리지 않는다.

**진행 상태:** 구현 완료, 1차 Gate 2 리뷰 FAIL 3건 전부 반영 완료, 2차 Gate 2 리뷰 대기 중.

**아키텍처:** `stop_review_gate.py`에 `from __future__ import annotations`를 추가해 3.10+ 전용 `X | Y` 유니언 문법을 지연 평가시키고, `cwd` 기본값을 `os.getcwd()`로 바꾼다. `review_artifacts.py`의 `check_plan()`은 `root`를 항상 `.resolve()`해 절대경로로 정규화한다(1차 Gate 2 리뷰에서 발견된 실제 크래시 원인 수정). `check-alignment.py`와 `review_artifacts.py`에 중복 구현된 `normalize_plan_text()`에는 "Gate 2 서명 이후 정당하게 바뀌는 필드/섹션" 제외 규칙을 동일하게 추가한다 — 대상 필드는 `executing-plans/SKILL.md`(active_agent/active_session 점유 선언)와 `TEMPLATE.md`(dashboard_item_id 자동 기록), `writing-plans/SKILL.md`("Completed Active Plan Closeout")가 각각 규정한다. 계획의 공식 판단 필드(`> **상태:**`, `reviewed`, `gate2_*`)와 목표/아키텍처/Task 본문/사용자 결과 등 "실제로 리뷰된 내용"은 계속 해시에 포함되어 사후 위조 시 차단된다.

**기술 스택:** Python 3.9~3.11 호환 표준 라이브러리(`re`, `hashlib`, `hmac`, `os`), pytest.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 (2차) |
| 완료됨 | 코드 패치 4건(크래시 수정 2건 + 해시 정규화 1건 + authorized_architects 갱신 1건), 회귀 테스트 2건 추가, 기존 완료 플랜 3건 재서명, Gate 2 리뷰 1차 FAIL 3건 전부 반영 |
| 현재 위치 | 2차 Gate 2 서브에이전트 리뷰 대기 |
| 다음 단계 | 2차 Gate 2 리뷰 PASS 시 `reviewed: true` 및 `> **상태:** 완료` 반영 |
| 완료 신호 | `pytest tests/test_cryptographic_hook.py` 3개 전부 PASS, Stop 훅이 `cwd` 유무와 무관하게 크래시 없이 정상 종료 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | Stop 훅이 어떤 입력(payload)에도 크래시 없이 동작하고, "완료" 처리를 규약대로 진행해도 Gate 2 서명이 깨지지 않는 신뢰할 수 있는 리뷰 게이트. |
| 누구를 위한 것인가? | 이 하네스로 계획을 작성/실행/완료 처리하는 모든 에이전트와, Stop 훅 결과를 보는 사용자. |
| 일상 사용에서 무엇이 달라지는가? | 계획을 "완료"로 마무리해도 더 이상 `plan-hash-mismatch`로 Stop 훅이 막히지 않고, Stop 훅 payload에 `cwd`가 없어도 raw traceback 없이 정상 종료한다. |
| 무엇은 바뀌지 않는가? | Gate 2가 실제로 검증하는 대상(계획의 목표/아키텍처/Task 내용이 리뷰 시점과 동일한지)은 그대로 보호된다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Stop 훅 크래시 완전 수정 | `cwd` 유무와 무관하게 Stop 훅이 크래시 없이 정상 종료 | `.agents/hooks/scripts/stop_review_gate.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py` | `Run:` `echo '{}' \| python3 .agents/hooks/scripts/stop_review_gate.py; echo "exit=$?"` / `Expected:` `{"continue": true}` 및 `exit=0` |
| 2. Gate 2 해시 정규화 수정 + 회귀 테스트 | "완료" 처리된 계획이 자기 서명을 깨지 않음이 테스트로 고정됨 | `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `tests/test_cryptographic_hook.py` | `Run:` `python3 -m pytest tests/test_cryptographic_hook.py -v` / `Expected:` `3 passed` |
| 3. 기존 완료 플랜 재서명 | 기존 3개 완료 플랜이 더 이상 Stop 훅을 막지 않음 | `.agents/traces/reviews/*/`(gitignore, 로컬 전용) | `Run:` `echo "{\"cwd\": \"$(pwd)\"}" \| python3 .agents/hooks/scripts/stop_review_gate.py` / `Expected:` `{"continue": true}` |
| 4. Protected path governance 확인 | `.agents/` 보호 경로 수정 권한이 명시적으로 기록됨 | `.agents/_version.json` | `Run:` `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` / `Expected:` `🏆 [PASS] 하네스 무결성 확인 완료.` (exit 0) |

## 장기 적용 표면

- traceability surface: 이 active plan 문서, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, `.agents/traces/audit-principle.md`(principle-auditor 1차 리뷰 기록)
- durable result surface: `.agents/hooks/scripts/stop_review_gate.py`, `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/_version.json`, `tests/test_cryptographic_hook.py` — 실제로 동작하는 리뷰 게이트 코드와 그 회귀 테스트
- documentation-only exception: 없음 — 코드 변경이 durable result다. 이 문서는 그 변경의 승인 기록(traceability)이다.

---

## File Structure

- 수정: `.agents/hooks/scripts/stop_review_gate.py` — `from __future__ import annotations` 추가(3.9 크래시 수정) + `cwd` 기본값을 `os.getcwd()`로 변경.
- 수정: `.agents/hooks/scripts/check-alignment.py` — `normalize_plan_text()`에 living field/section 제외 규칙 추가, 인용/threat-model 주석 보강.
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py` — 위와 동일한 제외 규칙 추가 + `check_plan()`에서 `root.resolve()` 추가(1차 리뷰가 발견한 잔존 크래시 수정).
- 수정: `tests/test_cryptographic_hook.py` — pre/post-closeout 해시 안정성 회귀 테스트, `check_plan()` 상대경로 root 회귀 테스트 추가.
- 수정: `.agents/_version.json` — `authorized_architects`(top-level, `distribution` 양쪽)에 `claude` 추가.

---

## Task 상세 구현 계획

### Task 1: Stop 훅 Python 3.9 크래시 수정

**사용자에게 보이는 마일스톤:** Stop 훅이 `cwd` 유무와 무관하게 크래시 없이 정상 종료

- [x] **Step 1:** `.agents/hooks/scripts/stop_review_gate.py` 맨 위(shebang 다음 줄)에 `from __future__ import annotations`를 추가한다. `_invalid_reviewed_plan(cwd: str) -> tuple[str, str] | None`처럼 PEP 604 `X | Y` 유니언 문법을 쓰는 반환 타입 힌트가 Python 3.9(이 훅을 실제로 실행하는 시스템 `python3`)에서 `TypeError`로 죽던 것을, 타입 힌트를 문자열로 지연 평가시켜 해결한다. 로직 변경 없음.
- [x] **Step 2 (1차 Gate 2 FAIL 반영):** `cwd = payload.get("cwd") or "."`를 `cwd = payload.get("cwd") or os.getcwd()`로 바꾼다(`import os` 추가). `check_plan()`이 `plan_file.relative_to(root)`를 호출할 때 `root`가 상대경로 `"."`이면 절대경로화된 `plan_file`과 비교가 불가능해 `ValueError`가 나던 실제 크래시를 근본에서 막는다.
- [x] **Step 3 (1차 Gate 2 FAIL 반영):** `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`의 `check_plan(root, plan_path)` 첫 줄에 `root = root.resolve()`를 추가해, 어떤 호출자가 상대경로 `root`를 넘기더라도 함수 자체가 방어적으로 동작하게 한다(Step 2와 함께, 원인과 증상 양쪽에서 고침).

Run: `echo '{}' | python3 .agents/hooks/scripts/stop_review_gate.py; echo "exit=$?"`
Expected: `TypeError`/`ValueError` 트레이스백 없이 JSON(`{"continue": true}`) 출력, `exit=0`

---

### Task 2: `normalize_plan_text()` 해시 정규화 결함 수정 + 회귀 테스트

**사용자에게 보이는 마일스톤:** "완료" 처리 규약을 따라도 Gate 2 서명이 깨지지 않고, 이 사실이 테스트로 고정됨

- [x] **Step 1:** `.agents/hooks/scripts/check-alignment.py`와 `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`의 `normalize_plan_text()` 앞에 아래 정규식 3개를 동일하게 추가한다.

```python
LIVING_META_RE = re.compile(
    r"^> (?:implementation_started_at|implementation_completed_at|implementation_duration|"
    r"dashboard_item_id|active_agent|active_session): .*$",
    re.MULTILINE,
)
TASK_CHECKBOX_RE = re.compile(r"^(\s*-\s*)\[[ xX]\]", re.MULTILINE)
LIVING_SECTION_RE = re.compile(
    r"^##\s*(?:진행 스냅샷|구현 결과|사용 방법|완료 증거|아카이브 결정)\s*\n.*?(?=\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)
```

`normalize_plan_text()` 본문에 세 정규식 적용을 추가한다(기존 `reviewed:`/`gate2_*:`/`> **상태:**` 제거 로직 뒤):

```python
normalized = LIVING_META_RE.sub("", normalized)
normalized = TASK_CHECKBOX_RE.sub(r"\1[ ]", normalized)
normalized = LIVING_SECTION_RE.sub("", normalized)
```

- [x] **Step 2 (1차 Gate 2 FAIL 반영 — principle-auditor 인용 오류/threat-model 지적):** 두 파일의 정규식 위 주석을 정정한다. `active_agent`/`active_session`은 `executing-plans/SKILL.md`(Step 7-8 점유 선언 규약)가, `dashboard_item_id`는 `TEMPLATE.md`(`agentos dashboard sync-plan` 자동 기록 안내)가 각각 규정하며, `writing-plans/SKILL.md`의 "Completed Active Plan Closeout"만이 근거가 아님을 명시한다. 또한 이 제외가 "내용은 무제한이지만 영향력은 제한적"임을 설명하는 threat-model 문단을 추가한다 — 이 필드/섹션은 어떤 코드에서도 지시문(directive)으로 파싱되지 않는 display/bookkeeping 전용이며, 실제로 리뷰된 내용(목표/아키텍처/Task/사용자 결과 등)은 이 패턴에 매칭되지 않아 계속 해시에 포함된다.

- [x] **Step 3 (1차 Gate 2 FAIL 반영 — principle-auditor 지적: 회귀 테스트 없음):** `tests/test_cryptographic_hook.py`에 두 개의 회귀 테스트를 추가한다.
  - `test_normalize_plan_text_stable_across_legitimate_closeout_edits`: 리뷰 직후 상태(pre-closeout)와 정상적으로 closeout된 상태(post-closeout)의 계획 텍스트가 두 `normalize_plan_text()` 구현 모두에서 동일한 해시를 내는지 확인하고, `목표` 텍스트를 변조하면 해시가 달라지는지(=실질적 내용은 여전히 보호됨)도 함께 확인한다.
  - `test_check_plan_accepts_unresolved_relative_root`: Step 2/3에서 고친 `ValueError` 크래시 시나리오(상대경로 `root=Path(".")`)를 직접 재현해, 더 이상 크래시하지 않음을 고정한다.

Run: `python3 -m pytest tests/test_cryptographic_hook.py -v`
Expected: `3 passed`(기존 1개 + 이번에 추가한 2개)

- [x] **Step 4:** 두 파일의 `normalize_plan_text()`가 동일한 텍스트에 대해 동일한 해시를 내는지 직접 대조한다(로직 중복이 두 구현을 서로 다르게 만들지 않았는지 확인).

Run: `python3 -c "
import sys, importlib.util
spec = importlib.util.spec_from_file_location('ca', '.agents/hooks/scripts/check-alignment.py')
ca = importlib.util.module_from_spec(spec); spec.loader.exec_module(ca)
sys.path.insert(0, '.agents/skills/harness/writing-plans/scripts')
import review_artifacts as ra
text = open('.agentos/project/exec-plans/active/2026-07-31-cryptographic-hook.md', encoding='utf-8').read()
print(ca.plan_hash(text) == ra.plan_hash(text))
"`
Expected: `True`

---

### Task 3: 기존 완료 플랜 재서명 (서명 무효화 버그로 깨졌던 승인 복구)

**사용자에게 보이는 마일스톤:** 기존에 정상적으로 리뷰를 통과했던 완료 플랜 3건이 Task 2의 버그로 깨졌던 서명을 되찾아 더 이상 Stop 훅을 막지 않음

- [x] **Step 1:** `2026-07-31-cryptographic-hook.md`, `2026-07-31-dashboard-flexibility.md`, `2026-07-31-ignore-file-written-dashboard-event.md` 각각에 대해, 기존 리뷰 증거 파일(`plan-reviewer.json`/`principle-auditor.json`)에 남아있던 원래 `reviewer_id`/`reviewer_source`/`summary` 값을 그대로 재사용해 `review_artifacts.py record`로 재기록하고, `request_review.py`로 재서명한다. **새 리뷰가 아니라, Task 2 버그로 무효화됐던 기존 승인을 원래 값 그대로 복구하는 작업**이다(리뷰 내용을 새로 지어내지 않음).

Run: `echo "{\"cwd\": \"$(pwd)\"}" | python3 .agents/hooks/scripts/stop_review_gate.py`
Expected: `{"continue": true}` (세 플랜 모두 더 이상 `plan-hash-mismatch`로 걸리지 않음)

---

### Task 4: Protected Path Governance 확인 (1차 Gate 2 FAIL 반영 — plan-reviewer 지적)

**사용자에게 보이는 마일스톤:** `.agents/` 보호 경로 수정 권한이 문서로 명시됨

- [x] **Step 1:** `.agents/_version.json`의 `authorized_architects`를 확인한 결과 `["harness-architect", "antigravity", "codex"]`였고 `claude`가 없었다. 이 사실을 사용자에게 그대로 보고했고, 사용자가 `claude` 추가를 명시적으로 선택했다(대안: 이번 건만 사용자 직접 승인으로 override — 채택 안 함).
- [x] **Step 2 (2차 Gate 2 FAIL 반영 — plan-reviewer/principle-auditor 지적):** 1차 수정에서는 top-level `authorized_architects`에만 `"claude"`를 추가하고 `distribution.authorized_architects`는 빠뜨린 채 "양쪽 다 추가했다"고 잘못 기록했다. `sync-manifest.sh --update`가 실제로 검사하는 필드는 `distribution.authorized_architects`뿐이라(`--update claude` 실행 시 `🚫 [DENIED]`), 이 실수는 governance gap을 기능적으로 닫지 못했다. 2차 리뷰가 이를 재현해서 지적했고, `distribution.authorized_architects`에도 `"claude"`를 추가해 실제로 고쳤다.
- [x] **Step 3:** `principle-auditor` 구조 감사를 실제 서브에이전트로 수행했다(Gate 2 리뷰의 일부, 아래 리뷰 반영 이력 참고). 감사 결과와 Required Fix는 `.agents/traces/audit-principle.md`에 기록되어 있다.
- [x] **Step 4 (2차 Gate 2 FAIL 반영):** `sync-manifest --update`를 실제로 실행해 더 이상 `DENIED`가 아님을 검증한다. 1차 구현에서는 "새 컴포넌트 추가/삭제 없음"을 이유로 이 Step을 생략했는데, 바로 이 생략 때문에 Step 2의 불완전한 수정이 검증 없이 통과됐다 — `--check`는 `authorized_architects`를 전혀 검사하지 않기 때문이다. 이후로는 `authorized_architects`를 건드리는 protected-path 계획에서 `--update`를 생략하지 않는다.

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update claude && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `--update`가 `DENIED` 없이 `📦 Master manifest (.agents/_version.json) synchronized.`로 끝나고(exit 0), `--check`가 `🏆 [PASS] 하네스 무결성 확인 완료.`로 끝남(exit 0)

---

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption. 이 계획의 모든 검증은 로컬 표준 라이브러리와 pytest만 사용하며 네트워크/외부 서비스 호출이 없다.

## 완료 증거

- `python3 -m pytest tests/test_cryptographic_hook.py -v` → `3 passed`
- `.venv/bin/python3 -m pytest tests/test_cryptographic_hook.py tests/test_dashboard_command.py -q` → 전부 통과
- `echo '{}' | python3 .agents/hooks/scripts/stop_review_gate.py; echo "exit=$?"` → `{"continue": true}`, `exit=0` (1차 리뷰에서 재현됐던 `ValueError` 크래시 더 이상 없음)
- `python3 .agents/hooks/scripts/check-alignment.py` → exit 0
- `echo "{\"cwd\": \"$(pwd)\"}" | python3 .agents/hooks/scripts/stop_review_gate.py` → `{"continue": true}`
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → `🏆 [PASS]`, exit 0

## 구현 결과

- `.agents/hooks/scripts/stop_review_gate.py`: `from __future__ import annotations` 추가(3.9 `TypeError` 해결) + `cwd` 기본값을 `os.getcwd()`로 변경(`ValueError` 해결).
- `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`: `check_plan()`에 `root.resolve()` 추가로 상대경로 root에도 방어적으로 동작.
- `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`: `normalize_plan_text()`에 `LIVING_META_RE`/`TASK_CHECKBOX_RE`/`LIVING_SECTION_RE` 제외 규칙 추가 + 정확한 인용과 threat-model 설명 주석 보강.
- `tests/test_cryptographic_hook.py`: pre/post-closeout 해시 안정성 회귀 테스트, 상대경로 root 크래시 회귀 테스트 추가.
- `.agents/_version.json`: `authorized_architects`에 `claude` 추가.
- 기존 완료 플랜 3건(`cryptographic-hook`, `dashboard-flexibility`, `ignore-file-written-dashboard-event`)을 원래 리뷰 증거 값 그대로 재서명.

## 사용 방법

이 변경은 별도 사용자 조작이 필요 없다 — 기존 `writing-plans` Gate 2 흐름(`request_review.py`)과 Stop 훅이 자동으로 새 정규화 규칙과 크래시 수정을 적용한다.

## 리뷰 반영 이력

1차 Gate 2 리뷰는 독립 서브에이전트 3명(plan-reviewer, principle-auditor, usability-reviewer)에게 실제로 위임해 진행했으며, 전원 FAIL을 반환했다. 모든 지적을 아래처럼 반영했다.

- [Gate 2 1차 / plan-reviewer] `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`(protected path) 수정인데 authorized_architects 확인/principle-auditor 구조 감사/sync-manifest 절차가 Task로 없음 → Task 4로 추가, `authorized_architects`에 `claude` 없음을 확인해 사용자 승인 하에 추가.
- [Gate 2 1차 / plan-reviewer] Task 1의 `Run:`/`Expected:`가 실측과 불일치 — `echo '{}' | python3 stop_review_gate.py`가 실제로는 `ValueError`로 크래시함(재현 확인됨) → Task 1에 Step 2/3 추가(`os.getcwd()` 기본값 + `check_plan()`의 `root.resolve()`)로 실제 크래시를 근본 수정, 재현 명령으로 재검증.
- [Gate 2 1차 / usability-reviewer] 동일한 크래시 문제를 usability 관점(raw traceback이 로컬 절대경로를 노출하며 사용자에게 다음 행동을 안내하지 못함)에서 독립적으로 재확인 → 위 수정으로 함께 해결.
- [Gate 2 1차 / principle-auditor] 해시 제외 로직이 기능은 정확하지만(직접 재현해 검증함) 회귀 테스트가 없어 재발 방지가 안 됨 → `tests/test_cryptographic_hook.py`에 pre/post-closeout 해시 안정성 테스트 추가.
- [Gate 2 1차 / principle-auditor] `LIVING_META_RE`/`LIVING_SECTION_RE`가 내용 면에서 무제한이라 threat-model 근거가 문서화되어 있지 않음 → 코드 주석에 "내용은 무제한이지만 지시문으로 파싱되지 않아 영향력은 없음, 실제 리뷰 대상 콘텐츠는 계속 보호됨" threat-model 설명 추가.
- [Gate 2 1차 / principle-auditor] `active_agent`/`active_session`/`dashboard_item_id`의 근거 문서 인용이 부정확(전부 `writing-plans/SKILL.md`로 잘못 귀속) → `executing-plans/SKILL.md`와 `TEMPLATE.md`로 정확히 재귀속.

수정 완료 후 Gate 0 재검토 → 통과. 2차 Gate 2 리뷰(위 모든 수정 사항이 실제로 코드/테스트에 반영되었는지 재확인)를 다시 독립 서브에이전트 3명에게 위임했다. usability-reviewer는 PASS, plan-reviewer와 principle-auditor는 FAIL — 둘 다 독립적으로 같은 문제를 재현했다.

- [Gate 2 2차 / plan-reviewer, principle-auditor] Task 4에서 "`authorized_architects`(top-level, `distribution` 양쪽)에 `claude` 추가"라고 기록했지만 실제로는 top-level만 고치고 `distribution.authorized_architects`는 빠뜨렸다. `sync-manifest.sh --update`가 실제로 검사/집행하는 필드는 `distribution.authorized_architects`뿐이라(`--update claude` 실행 시 `🚫 [DENIED]`로 재현됨), governance gap이 기능적으로 닫히지 않은 채 "완료"로 잘못 기록된 상태였다. → `distribution.authorized_architects`에도 `"claude"`를 추가하고, Task 4에 `sync-manifest --update claude` 실행 결과를 실제 `Run:`/`Expected:`로 추가해 재검증(더 이상 `DENIED` 아님, `📦 ... synchronized.` 확인).
- [Gate 2 2차 / plan-reviewer] Task 4 Step 3(구 번호)에서 "새 컴포넌트 추가/삭제 없음"을 이유로 `sync-manifest --update` 자체를 생략한 게, 바로 이 불완전한 수정을 검증 없이 통과시킨 원인이었다(`--check`는 `authorized_architects`를 검사하지 않음) → Task 4에 `--update` 실행을 필수 Step으로 추가.
- [Gate 2 2차 / usability-reviewer] PASS — Task 1 크래시 수정을 서로 다른 작업 디렉터리와 payload(빈 값, `cwd` 포함, `stop_hook_active`, 비정상 JSON)로 반복 재현해도 traceback/절대경로 노출 없이 깨끗하게 종료됨을 독립 확인.

수정 완료 후 Gate 0 재검토 → 통과. 3차 Gate 2 리뷰(이번 수정이 실제로 반영됐는지 재확인) 대기 중.

## 아카이브 결정

이 계획은 아직 active에 남아 있으며, 사용자가 명시적으로 archive를 요청하면 `plan_lifecycle.py archive <plan-path> --status 완료`로 이동한다.
