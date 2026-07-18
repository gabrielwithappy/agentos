# AgentOS CLI 구조 개편 및 AHA 잔재 제거 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-17<br>
> reviewed: true<br>
> implementation_completed_at: 2026-07-17T11:24:00Z<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 기존 `aha` CLI 쉘 스크립트 명칭과 호출 방식을 현재 파이썬 구조(Typer/Rich)에 맞게 `agentos` 명령어로 전면 리팩토링하고 관련 카탈로그 문서들을 수정한다.

**사용자 결과:** 오래된 aha 기반 쉘 스크립트 참조를 모두 제거하고, Python CLI 구조(agentos skill, agentos agent 등)에 맞게 일관된 사용자 경험을 제공한다. 또한 불필요한 상태 확인용 레거시 기능을 제거하여 CLI를 단순화한다.

**진행 상태:** 구현 완료

**아키텍처:** 
- `cli.py`에 `agent` 서브명령어 그룹 추가
- 기존 `skill` 명령어의 `add`를 `install`로 통일
- 카탈로그 문서 내 `aha` 및 `$AHA_HOME` 참조를 `agentos` 및 `$AGENTOS_HOME`으로 치환
- `harness-loop.sh` 쉘 스크립트 폐기 및 `harness.py`로 핵심 실행 기능 완전 이관 (단, 최신 `/goal` 슬래시 커맨드 트렌드에 맞춰 불필요한 `status`, `watch`, `inspect` 기능은 제거)

**기술 스택:** Python (Typer, Rich), Markdown, JSON

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 모든 카탈로그 JSON 및 문서 수정, Python CLI(agent, skill, harness) 코드 재작성 및 쉘 스크립트 삭제 |
| 현재 위치 | 구현 완료 및 검증 통과 |
| 다음 단계 | (없음) |
| 완료 신호 | 모든 카탈로그 파일에서 `aha` 참조가 사라지고, 명령어 테스트(PASS agentos-public-suite) 성공 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 직관적이고 일관된 최신 파이썬 CLI 명령어(`agentos`)와 정확히 일치하는 문서 가이드 |
| 누구를 위한 것인가? | AgentOS 카탈로그 플러그인을 관리하거나 Harness 코어를 직접 실행하려는 사용자 |
| 일상 사용에서 무엇이 달라지는가? | 파이썬만 설치되어 있다면 크로스 플랫폼에서 안전하게 에이전트를 설치하고 harness 루프를 구동할 수 있음 |
| 무엇은 바뀌지 않는가? | 플러그인 복사 로직 및 `harness_loop.py` 파이썬 코어 엔진의 기본 동작 원리 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 카탈로그 문서 최신화 | 모든 문서에서 `agentos`로 수정됨 | `catalog/**/*.md`, `*.json` | `grep` 명령어 결과가 없음 |
| 2. Agent 명령어 그룹 신설 | `agentos agent list/install` 명령어 사용 가능 | `cli.py`, `commands/agent.py` | `uv run agentos agent --help` 실행 시 PASS |
| 3. Skill 명령어 통일 | `agentos skill install` 사용 가능 | `commands/skill.py` | `uv run agentos skill install --help` 실행 시 PASS |
| 4. Harness 명령어 이관 | `agentos harness`가 순수 파이썬으로 동작 | `commands/harness.py`, `harness-loop.sh`(삭제) | `uv run agentos harness --help` 실행 시 PASS |

## 장기 적용 표면

- traceability surface: `.agentos/project/exec-plans/active/2026-07-17-aha-cli-refactoring.md`
- durable result surface: `catalog/`, `agentos/cli.py`, `agentos/commands/`
- documentation-only exception: 아님 (코드 로직 수정 포함)

## 의존성 분석

- 외부 의존성: Typer, Rich
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.

---

### Task 1: 카탈로그 JSON 및 문서에서 AHA 잔재 제거

**파일:**
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/catalog/agents/catalog.json`
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/catalog/skills/catalog.json`
- 수정: 각 에이전트 및 스킬의 `AGENT.md`, `SKILL.md`

- [x] **Step 1: JSON 및 마크다운 파일 내 문자열 치환**
`aha agents install`을 `agentos agent install`로, `aha skills install`을 `agentos skill install`로 변경하고, `$AHA_HOME`을 `$AGENTOS_HOME`으로 치환.

Run: `grep -r "aha " catalog/ && echo "FAIL" || echo "PASS"`
Expected: `PASS`

### Task 2: Python CLI 명령어 개선 (`agent` 그룹 추가 및 `skill` 통일)

**파일:**
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/agentos/cli.py`
- 생성: `/home/gabriel/agent/prj-agent/agentos/agentos/agentos/commands/agent.py`
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/agentos/commands/skill.py`

- [x] **Step 1: `commands/agent.py` 생성 및 `cli.py`에 등록**
`skill.py`의 구조를 참고하여 `agent list` 및 `agent install`을 구현.

Run: `uv run agentos agent --help > /dev/null && echo "PASS"`
Expected: `PASS`

- [x] **Step 2: `commands/skill.py`의 `add`를 `install`로 통일**
기존 `add` 커맨드의 이름을 `install`로 변경(add는 alias로 유지).

Run: `uv run agentos skill install --help > /dev/null && echo "PASS"`
Expected: `PASS`

### Task 3: Harness 명령어 파이썬 이관 및 단순화 (방법 B 적용)

**파일:**
- 수정: `/home/gabriel/agent/prj-agent/agentos/agentos/agentos/commands/harness.py`
- 삭제: `/home/gabriel/agent/prj-agent/agentos/agentos/harness-loop.sh`
- 삭제: `/home/gabriel/agent/prj-agent/agentos/agentos/.agents/skills/harness/harness-loop.sh`

- [x] **Step 1: `harness-loop.sh` 쉘 스크립트 삭제**
더 이상 사용하지 않는 `harness-loop.sh` 파일들을 프로젝트에서 완전히 제거한다.

Run: `[ ! -f harness-loop.sh ] && echo "PASS"`
Expected: `PASS`

- [x] **Step 2: `commands/harness.py`에 핵심 실행 기능 파이썬으로 구현**
과거 상태 조회용 찌꺼기 기능들(`status`, `watch`, `inspect` 등)은 제외하고, `--cli`, `--max-iterations` 등 메인 파라미터만 파싱하여 `core-engine/harness_loop.py`를 파이썬 서브 프로세스로 직접 실행하도록 `harness.py`를 덮어쓴다.

Run: `uv run agentos harness --help > /dev/null && echo "PASS"`
Expected: `PASS`

## 리뷰 반영 이력
- [Gate 2 1차] 사용자의 방법 B(파이썬 완전 이관) 선택 및 핵심 기능 외 불필요한 레거시 상태 확인 기능 제거 반영 완료. 승인됨.

## 구현 결과
모든 `aha` CLI 및 문서 참조가 `agentos` 명령어로 성공적으로 이전되었으며, `harness-loop.sh` 쉘 스크립트는 삭제되고 기능이 Python으로 완전 이관되었습니다.

## 사용 방법
- 에이전트 조회/설치: `uv run agentos agent list` / `uv run agentos agent install <경로>`
- 스킬 설치: `uv run agentos skill install <경로>`
- Harness 실행: `uv run agentos harness <인자>`

## 완료 증거
모든 `--help` 출력 정상 확인, `grep -r "aha "` 누락본 없음 확인, `bash scripts/verify-public-test-suite.sh` 통과 완료.
