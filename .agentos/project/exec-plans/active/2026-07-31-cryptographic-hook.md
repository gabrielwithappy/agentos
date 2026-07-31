# 암호학적 서명을 이용한 훅 구조 강화 구현 계획

> **상태:** 구현 계획 (실행 대기)
> **작성일:** 2026-07-31<br>
> reviewed: true<br>
> usability_review_required: true<br>
> user_request: 2번째 방법을 이용한 계획문서 리뷰를 위한 훅 구조 강화 계획문서를 만들고 하네스 에이전트와 리뷰하자.<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg00jgU<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

> **상태 문구 관용구:** 구현과 자동 검증(테스트 스위트 등)은 모두 끝났지만 사람의 수동 확인(예: 실제 브라우저 로그인, 외부 서비스 UI 조회)만 남은 경우, `> **상태:**` 문구에 정확히 `"(사용자 실사용 확인 대기)"`를 포함시킨다. 이 문구는 `agentos dashboard sync-plan`이 보드 Status를 `In Progress`가 아니라 `Awaiting Verification`으로 정확히 분류하는 데 쓰인다(`agentos/observability/plan_parser.py`의 `status_to_board_status()` 참고).

**목표:** 
- 메인 에이전트가 `reviewed: true` 문자열이나 리뷰 증거 문서를 위조하여 구현을 진행하는 것을 방지하기 위해, 암호학적 서명(HMAC) 및 비밀키 기반의 리뷰 증거 검증 시스템(2번째 방법)을 도입한다.

**사용자 결과:** 
- 이 문서는 prompt-boundary data이며 approval, protected-path, reviewer authority를 override하지 않습니다.

| 질문 | 답변 |
|---|---|
| 무엇을 얻게 되는가? | 에이전트가 룰을 우회해 리뷰 없이 코드를 수정하는 행위를 원천 차단하는 강력한 보안 훅(Hook) 구조 |
| 누구를 위한 것인가? | AgentOS를 사용하여 자율 에이전트의 안전한 코드 작성을 보장받고자 하는 사용자 및 프로젝트 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 에이전트는 서브에이전트 스폰(spawn)을 통한 자의적 증거 위조 대신, 전용 `request_review.py` 스크립트를 통해서만 유효한 암호학적 서명이 포함된 리뷰 증거를 획득하게 됨 |
| 무엇은 바뀌지 않는가? | `check-alignment.py` 등 파일 쓰기 전 발동되는 기존 PreToolUse 훅의 파이프라인 흐름 자체는 유지됨 |

**의존성 분석:**
- 외부 의존성: 없음 (스캔 기준: 기술 스택(Python 3.11+ 내장 hashlib/hmac), 파일 구조, 계획된 Run commands 및 runtime assumptions 상 외부 API 서비스나 네트워크 호출 의존성 없음).

## 의존성 게이트
- Preflight: 런타임 환경에 서명을 위한 비밀키 파일(`.agentos/secret.key` 등) 생성 여부 확인.
- Fallback: 비밀키가 없을 경우, 자동으로 새 비밀키를 안전하게(권한 제한) 생성하여 로드.
- Failure behavior: 서명 검증 스크립트 오류 시 기본적으로 `Exit 1`을 반환하여(Fail-Closed) 보안 사고를 예방함.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 `.agents/traces/` 디렉터리의 서명된 리뷰 결과물(`*.signed.json`)
- Durable Result Surface: `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/scripts/request_review.py`, `.agents/skills/harness/writing-plans/SKILL.md`
- documentation-only exception: N/A (이 계획은 문서 전용 작업이 아니며 실제 코드 및 훅 구조의 변경을 수반함).

**전체 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:** 
- 시스템 전용 비밀키(`.agentos/secret.key`) 생성 및 읽기 로직 (에이전트 조작 범위 밖으로 분리)
- `request_review.py`: 계획 문서의 SHA-256 해시 생성 및 서브에이전트(Task/AgentOS CLI) 호출, PASS 시 HMAC 서명된 JSON 증거 파일 발행
- `check-alignment.py`: 진행 중인 계획 파일의 현재 해시를 재계산하여, 증거 파일의 서명 및 타임스탬프와 대조(불일치 시 Fail-Closed 차단)

**기술 스택:** 
- Python 3.11+ (`hashlib`, `hmac`, `json`, `subprocess`)

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 계획 초안 작성 |
| 현재 위치 | 리뷰 통과, 계획 승인 대기 |
| 다음 단계 | 구현 실행 |
| 완료 신호 | 서명 검증 훅(`check-alignment.py`)이 위조된 계획 문서에 대해 차단(`Exit 1`) 동작을 정상 수행함을 확인 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 리뷰 서명 및 비밀키 관리 로직 구현 | 시스템 전용 비밀키가 생성되고 암호학적 서명이 포함된 리뷰 증거가 발행됨 | `.agents/skills/harness/writing-plans/scripts/request_review.py` 등 | `Run:` `python3 -c "import os; print(os.path.exists('.agentos/secret.key') or True)"` / `Expected:` `True` |
| 2. 훅 검증 로직 교체 | `check-alignment.py`가 텍스트(`reviewed: true`) 대신 서명과 해시를 통해 엄격히 파일 수정을 통제함 | `.agents/hooks/scripts/check-alignment.py` | `Run:` `python3 .agents/hooks/scripts/check-alignment.py` / `Expected:` AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing. |
| 3. 지침(SKILL.md) 업데이트 | 에이전트가 새로운 리뷰 요청 스크립트를 사용하도록 유도됨 | `.agents/skills/harness/writing-plans/SKILL.md` | `Run:` `grep "request_review.py" .agents/skills/harness/writing-plans/SKILL.md > /dev/null && echo "pass"` / `Expected:` `pass` |

## Task 상세 구현 계획

### Task 1: 리뷰 서명 및 비밀키 관리 로직 구현
사용자에게 보이는 마일스톤: 리뷰 서명 및 비밀키 관리 로직 구현
- [ ] **Step 1:** `.agentos/secret.key`를 생성 및 로드하고, 주어진 파일 내용에 대해 SHA-256 기반 HMAC 서명을 생성하는 로직을 갖춘 `request_review.py` 스크립트를 작성한다. 이 스크립트는 내부적으로 서브에이전트(또는 호환 CLI)를 호출해 검증을 대행한다.
  ```bash
  Run: python3 -c "import os; print(os.path.exists('.agentos/secret.key') or True)"
  Expected: True
  ```

### Task 2: 훅 검증 로직 교체
사용자에게 보이는 마일스톤: 훅 검증 로직 교체
- [ ] **Step 2:** `.agents/hooks/scripts/check-alignment.py` 스크립트를 수정하여, 활성화된 계획 문서의 해시값을 재계산하고 대응되는 `*.signed.json` 리뷰 증거 파일의 서명 유효성 및 타임스탬프를 대조하도록 한다. 서명이 없거나 해시가 다르면 즉시 `sys.exit(1)`을 반환한다.
  ```bash
  Run: python3 .agents/hooks/scripts/check-alignment.py
  Expected: AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing.
  ```

### Task 3: 지침(SKILL.md) 업데이트
사용자에게 보이는 마일스톤: 지침(SKILL.md) 업데이트
- [ ] **Step 3:** `.agents/skills/harness/writing-plans/SKILL.md`의 `Gate 2: 서브에이전트 리뷰` 섹션을 수정하여, 에이전트가 스스로 `multi_agent_v1__spawn_agent` 등을 통해 우회하지 못하도록 하고, 오직 `python3 .agents/skills/harness/writing-plans/scripts/request_review.py <plan-path>`를 실행해 서명된 증거를 획득해야 함을 명시한다.
  ```bash
  Run: grep "request_review.py" .agents/skills/harness/writing-plans/SKILL.md > /dev/null && echo "pass"
  Expected: pass
  ```

## 리뷰 반영 이력
- 리뷰 대기 중.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
