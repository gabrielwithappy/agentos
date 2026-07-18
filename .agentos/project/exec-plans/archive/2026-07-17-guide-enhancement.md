# 가이드 문서 최신화 및 강화 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-17<br>
> reviewed: true<br>
> implementation_completed_at: 2026-07-17T03:18:00Z<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 최근 구현된 Python CLI(`agentos`)와 계획 문서 네임스페이스 이전(`.agentos/project/exec-plans`) 내역을 반영하여 프로젝트 가이드 문서를 최신화한다.

**사용자 결과:** 신규 사용자 및 기여자가 낡은 쉘 스크립트(`setup.sh`) 대신 최신 Python CLI 명령어로 AgentOS를 직관적으로 셋업하고 구동할 수 있다.

**진행 상태:** 리뷰 대기

**아키텍처:** `README.md`, `README.ko.md`, `docs/getting-started.md`의 설치 및 실행 안내 섹션을 전면 수정하고, 더 이상 사용되지 않는 레거시 `setup.sh`의 삭제(또는 대체)를 진행한다.

**기술 스택:** Markdown

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Python CLI(Typer/Rich) 기반 명령 구현 및 PR 머지 완료 |
| 현재 위치 | 가이드 문서 최신화를 위한 계획 문서 작성 완료 |
| 다음 단계 | 본 계획 승인 시 가이드 문서 수정 및 레거시 파일 정리 실행 |
| 완료 신호 | 모든 가이드 문서에서 `setup.sh` 대신 `agentos` 기반 셋업 및 실행 명령어가 올바르게 안내됨 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 최신 Python CLI 기반의 명확한 설치 및 실행 가이드 문서 |
| 누구를 위한 것인가? | AgentOS를 처음 설치하거나 개발에 참여하려는 모든 기여자 및 사용자 |
| 일상 사용에서 무엇이 달라지는가? | 레거시 bash 스크립트에 의존하지 않고, 표준 파이썬 기반 CLI를 통해 환경을 세팅하고 에이전트를 구동하게 됨 |
| 무엇은 바뀌지 않는가? | AgentOS의 핵심 비전(Portable AgentCore)과 보안·기여 원칙 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 영문 README 최신화 | `README.md`에서 Python CLI 셋업 및 실행 명령어 안내 확인 | `README.md` | 변경된 문자열(`uv run agentos setup`) 존재 여부 확인 |
| 2. 국문 README 최신화 | `README.ko.md`에서 Python CLI 셋업 및 실행 명령어 안내 확인 | `README.ko.md` | 변경된 문자열(`uv run agentos setup`) 존재 여부 확인 |
| 3. 시작 가이드 상세화 | `docs/getting-started.md`에서 CLI 사용법 및 새로운 계획 문서 경로 안내 | `docs/getting-started.md` | 변경된 문자열(`uv run agentos setup`) 존재 여부 확인 |
| 4. 레거시 스크립트 정리 | 불필요해진 `setup.sh` 제거 | `setup.sh` | 파일 미존재 확인 |

## 장기 적용 표면

- traceability surface: `.agentos/project/exec-plans/active/2026-07-17-guide-enhancement.md`
- durable result surface: `README.md`, `README.ko.md`, `docs/getting-started.md`
- documentation-only exception: 기능 코드의 변경 없이 마크다운 문서 최신화가 핵심 목표임

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.

---

### Task 1: 메인 README 문서 최신화

**파일:**
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/README.md`
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/README.ko.md`

**사용자에게 보이는 마일스톤:** GitHub 메인 화면에서 직관적인 Python CLI 셋업 가이드를 볼 수 있다.

- [ ] **Step 1: README.md 가이드 수정**
`bash setup.sh` 대신 `uv run agentos setup`을 안내하도록 수정한다.

Run: `grep -q "uv run agentos setup" README.md && echo "PASS"`
Expected: `PASS`

- [ ] **Step 2: README.ko.md 가이드 수정**
한국어 리드미 파일도 동일하게 최신 셋업 스크립트로 대체한다.

Run: `grep -q "uv run agentos setup" README.ko.md && echo "PASS"`
Expected: `PASS`

### Task 2: 시작 가이드 상세화 및 레거시 제거

**파일:**
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/docs/getting-started.md`
- 삭제: `/home/gabriel/agent/prj-agent/agentos/agentos/setup.sh`

**사용자에게 보이는 마일스톤:** 시작 가이드가 완전히 최신화되고, 혼란을 주는 레거시 스크립트가 사라진다.

- [ ] **Step 1: getting-started.md 가이드 수정**
설치 및 실행 단계에서 Python CLI 사용법을 안내하고, 계획 문서의 위치가 `.agentos/project/exec-plans`로 변경되었음을 명시한다.

Run: `grep -q "agentos setup" docs/getting-started.md && echo "PASS"`
Expected: `PASS`

- [ ] **Step 2: setup.sh 제거**
더 이상 사용되지 않는 `setup.sh` 스크립트를 삭제한다.

Run: `[ ! -f setup.sh ] && echo "PASS"`
Expected: `PASS`

## 리뷰 반영 이력
- [Gate 2 1차] 자가 검토 (plan-reviewer, principle-auditor, usability-reviewer) 통과. `setup.sh` 삭제 및 `uv run agentos setup` 사용 안내가 명확하며 P1~P4 원칙을 위반하지 않음. 문서상 경로 수정 요구사항 완벽 반영됨.

## 구현 결과
`README.md`, `README.ko.md`, `docs/getting-started.md` 파일들이 Python CLI `agentos`를 사용하도록 최신화되었으며, 불필요한 `setup.sh`가 제거되었습니다.

## 사용 방법
이제 프로젝트를 새로 클론한 후 `bash setup.sh` 대신 `uv run agentos setup`을 실행하여 초기 환경을 구성할 수 있습니다.

## 완료 증거
`README.md` 및 `README.ko.md`에서 `uv run agentos setup` 문자열 확인 통과.
`docs/getting-started.md` 문자열 확인 통과.
`setup.sh` 삭제 확인 통과.

## 아카이브 결정
이 계획은 아직 active에 남아 있으며, 사용자가 명시적으로 archive를 요청하면 `plan_lifecycle.py archive <plan-path> --status 완료`로 이동합니다.
