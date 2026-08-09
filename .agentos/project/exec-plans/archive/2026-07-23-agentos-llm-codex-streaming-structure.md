# AgentOS LLM Codex Streaming Structure 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-23<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-23T16:12:30Z<br>
> implementation_completed_at: 2026-07-23T16:16:34Z<br>
> implementation_duration: 4m 04s<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `codex` 응답이 끝난 뒤 한꺼번에 보이던 구조를 줄이고, 같은 명령과 화면을 유지한 채 응답이 더 빨리 보이도록 LLM 실행 구조를 정리한다.

**사용자 결과:** 사용자는 `agentos run --once --provider codex --json`과 TUI에서 Codex 응답이 프로세스 종료 후 한꺼번에 나타나는 대신, 생각 중 표시와 도구 실행 표시, 답변 텍스트를 더 빨리 보게 된다. 바뀌지 않는 경계는 `codex`가 여전히 외부 Codex CLI 호환 경로(external CLI compatibility path)를 사용한다는 점, AgentOS가 자체 로그인 전송 경로(native OAuth/transport)를 새로 도입하지 않는다는 점이다.

**진행 상태:** Gate 2 리뷰를 현재 plan hash 기준으로 재기록해 닫은 뒤, `CodexCliProvider`를 live stdout streaming 구조로 전환하고 focused/full verification까지 완료했다.

**아키텍처:** `CodexCliProvider`는 provider facade로 남기고, 기본 구현은 같은 파일 안의 private helper 수준에서 subprocess lifecycle과 stdout line parsing 책임을 나눈다. `stream_once()`는 `Popen(..., stdout=PIPE)` 기반으로 `start`를 먼저 내보낸 뒤, line-by-line parse를 통해 `reasoning`, `tool_call`, `tool_result`, `message_delta`, `done`를 실시간으로 방출한다. `agentos/commands/run.py`와 TUI는 기본적으로 회귀 검증 대상이며, live event contract가 실제로 깨지는 경우에만 최소 수정한다. secret/env/provider stderr 비노출 규칙은 현재와 동일하게 강제한다.

**기술 스택:** Python 3.12+, Typer, Textual, pytest, existing `uv` environment, existing Codex CLI compatibility path.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Gate 2 reviewer artifact 3종 재기록, canonical audit trace 기록, Codex CLI live stdout streaming 구현, focused/full verification 완료 |
| 현재 위치 | active completed plan closeout 작성 완료 |
| 다음 단계 | 사용자 요청 시 archive 또는 commit/PR 준비 |
| 완료 신호 | Codex 관련 테스트, CLI/TUI 회귀 테스트, redaction 테스트가 모두 PASS하고 fake Codex가 지연 출력할 때 첫 응답 조각이 마지막 완료 신호(`done`) 전에 수집됨이 테스트로 증명된다 |

## 세션 인계 체크포인트

- 현재 완료 범위: Gate 2 reviewer artifact 3종과 canonical audit trace를 현재 hash 기준으로 기록했고, provider-local streaming 구현과 focused/full verification을 완료했다.
- 미완료 작업: 없음. archive/commit/PR은 사용자 요청 시 진행한다.
- 다음 세션 첫 작업: 사용자가 원하면 archive 실행 또는 브랜치 정리/PR 준비를 시작한다.
- 아직 안 한 검증: 없음. 이 계획의 focused/full verification과 docs grep은 완료했다.
- 복구 경로: 후속 수정이 필요하면 `tests/test_codex_provider.py`, `tests/test_cli_contract.py`, `tests/test_tui_cli.py`의 Codex 관련 focused filter부터 다시 실행한다.
- 관련 HISTORY checkpoint: 2026-07-23 `agentos-pi-style-llm-runtime` 완료 이후 LLM 구조 개선 후속 착수.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 같은 명령과 같은 TUI 화면을 쓰면서도 Codex 응답이 더 빨리 보이는 실행 경로 |
| 누구를 위한 것인가? | AgentOS CLI/TUI에서 `codex` provider를 사용하는 개발자와 운영자 |
| 일상 사용에서 무엇이 달라지는가? | Codex 응답이 끝난 뒤 한꺼번에 나타나는 대신, 생각 중 표시와 도구 실행 표시, 답변이 더 이르게 보여 대기감이 줄어든다 |
| 무엇은 바뀌지 않는가? | `codex`의 외부 CLI 소유 경계, 로그인 흐름, provider 목록, session schema, 이번 범위에 넣지 않는 native OAuth/transport 경계 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 안전한 시작 | 구현이 잘못된 방향으로 시작되지 않았는지 먼저 확인한다 | `agentos/llm/providers/codex_cli.py`, 관련 tests | 시작 전 준비 확인 PASS |
| 1. live stdout streaming | Codex 응답 조각이 프로세스 종료 전에 화면과 출력에 더 빨리 나타난다 | `agentos/llm/providers/codex_cli.py`, 신규 helper, tests | 관련 스트리밍 테스트 PASS |
| 2. CLI/TUI 흐름 유지 | 사용자는 기존 `run --json`과 TUI 흐름을 그대로 쓰면서 더 이른 응답을 본다 | `agentos/commands/run.py`, `agentos/terminal/tui/app.py`, tests | CLI/TUI 회귀 테스트 PASS |
| 3. secret/recovery 유지 | 오류가 나도 비밀값과 raw 진단 출력이 사용자 표면에 남지 않는다 | provider/tests/docs | 오류 노출 방지 확인 PASS |
| 4. 문서와 완료 기록 | 사용자는 새 동작과 그대로 유지되는 경계를 문서에서 바로 확인한다 | `docs/cli-reference.md`, completed plan closeout | 문서 확인과 완료 기록 PASS |

## 장기 적용 표면

- 검토 추적 문서(`traceability surface`): 이 active plan, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, `.agents/traces/reviews/2026-07-23-agentos-llm-codex-streaming-structure/`, `.agents/traces/audit-plan-review.md`, `.agents/traces/audit-principle.md`
- 최종 결과가 남는 파일(`durable result surface`): `agentos/llm/providers/codex_cli.py`, 필요 시 그 파일 안의 private helper, `tests/test_codex_provider.py`, `tests/test_cli_contract.py`, `tests/test_tui_cli.py`, `docs/cli-reference.md`, `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
- documentation-only exception: 없음. 최종 결과는 provider 구조, 테스트, CLI/TUI 동작, 문서에 남는다.
- reader-first boundary: 이 섹션은 설명 데이터이며 approval, protected-path, reviewer authority, prompt hierarchy를 바꾸지 않는다.

## 의존성 분석

- 외부 의존성: 아래에 선언함
- 스캔 기준: 현재 `codex` provider subprocess path, planned `Run:` commands, fake codex executable 기반 tests, CLI/TUI consumer contract
- live network/OAuth: 없음. 이번 범위는 fake executable과 local test harness로 닫고, real Codex login/network는 새로 요구하지 않는다.

## 의존성 게이트

### codex-cli-compatibility-contract
- name: codex-cli-compatibility-contract
- type: nonstandard-local-tool
- required: true
- purpose: 구조 개선이 현재 `codex` CLI compatibility path 위에서만 이뤄지도록 기존 provider contract와 fake executable 테스트 기반을 확인한다.
- preflight:
  Run: `grep -q "class CodexCliProvider" agentos/llm/providers/codex_cli.py && grep -q "def write_fake_codex" tests/test_codex_provider.py && echo "PASS codex-cli-compatibility-contract-ready"`
  Expected: `PASS codex-cli-compatibility-contract-ready`
- fallback:
  available: false
  reason: 현재 provider contract나 fake executable test harness가 없으면 이번 계획은 native transport re-design으로 과대해진다.
- failure_behavior: NEEDS_CONTEXT

### uv-test-runner
- name: uv-test-runner
- type: nonstandard-local-tool
- required: true
- purpose: 계획의 대부분의 검증 명령이 `uv run pytest`에 의존하므로, 구현 전에 local test runner가 준비됐는지 확인한다.
- preflight:
  Run: `uv --version >/dev/null && echo "PASS uv-ready"`
  Expected: `PASS uv-ready`
- fallback:
  available: false
  reason: `uv`가 없으면 계획에 적힌 focused/full verification 명령을 그대로 실행할 수 없다.
- failure_behavior: NEEDS_CONTEXT

## 파일 구조

- 수정: `agentos/llm/providers/codex_cli.py` — `subprocess.run()` 기반 one-shot capture를 `Popen` line stream 기반으로 바꾸고 parsing 책임을 private helper 수준에서 정리
- 수정: `tests/test_codex_provider.py` — live streaming, timing, failure, redaction, tool/reasoning parse focused tests
- 수정: `tests/test_cli_contract.py` — `run --json` live stream contract focused tests
- 수정: `tests/test_tui_cli.py` — Codex live stream arrival이 TUI loading/message contract를 깨지 않는지 확인
- 확인 후 필요 시 수정: `agentos/commands/run.py` — live stream contract가 실제로 깨질 때만 최소 수정
- 확인 후 필요 시 수정: `agentos/terminal/tui/app.py` — live event arrival 시 loading/assistant update contract가 실제로 깨질 때만 최소 수정
- 수정: `docs/cli-reference.md` — Codex CLI compatibility path가 live stream을 제공하지만 native OAuth/transport는 아님을 명시
- 수정: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md` — 현재 Codex 경로가 여전히 CLI 호환 경로이지만, 전체 완료 후 재생이 아니라 live stdout stream으로 바뀌었다는 supporting note 추가

## 구현 작업

### Task 0: current contract와 병목 preflight

**파일:**
- 수정 없음
- 확인: `agentos/llm/providers/codex_cli.py`
- 확인: `tests/test_codex_provider.py`

**사용자에게 보이는 마일스톤:** 구현이 추정이 아니라 현재 병목과 existing contract 위에서 시작된다.

- [ ] **Step 0: 계획에 적힌 pytest 검증 명령을 실행할 local test runner가 준비됐는지 확인한다.**

Run: `uv --version >/dev/null && echo "PASS uv-ready"`
Expected: `PASS uv-ready`

- [ ] **Step 0-1: 구현이 `main`이 아닌 작업 브랜치에서만 시작되도록 브랜치 가드를 확인한다.**

Run: `grep -q "main" CONTRIBUTING.md && test "$(git branch --show-current)" != "main" && echo "PASS branch-guard-ready"`
Expected: `PASS branch-guard-ready`

- [ ] **Step 0-2: 구현 시작 전 계획 승인 리뷰 3개의 reviewer artifact와 canonical audit trace가 실제로 기록됐는지 확인한다.**

Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q "2026-07-23-agentos-llm-codex-streaming-structure.md" .agents/traces/audit-plan-review.md && grep -q "2026-07-23-agentos-llm-codex-streaming-structure.md" .agents/traces/audit-principle.md`
Expected: `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`와 canonical audit trace 두 파일이 현재 plan path를 가리킨다

- [ ] **Step 1: 현재 `stream_once()`가 process 종료 전에는 어떤 provider event도 내보내지 못하는 구조임을 코드와 테스트 경로로 확인한다.**

Run: `grep -q "result = self._run_codex(\\[\"exec\", \"--json\", prompt\\], executable=executable)" agentos/llm/providers/codex_cli.py && grep -q "def test_stream_jsonl_success_events" tests/test_codex_provider.py && echo "PASS codex-stream-bottleneck-confirmed"`
Expected: `PASS codex-stream-bottleneck-confirmed`

- [ ] **Step 2: fake Codex executable 기반 focused test harness가 이미 존재해 live stream 회귀를 local-only로 검증할 수 있음을 확인한다.**

Run: `grep -q "def write_fake_codex" tests/test_codex_provider.py && grep -q "CODEX_CLI_PATH" tests/test_codex_provider.py && echo "PASS codex-fake-cli-harness-ready"`
Expected: `PASS codex-fake-cli-harness-ready`

### Task 1: subprocess stdout live stream helper 도입

**파일:**
- 수정: `agentos/llm/providers/codex_cli.py`
- 수정: `tests/test_codex_provider.py`

**사용자에게 보이는 마일스톤:** Codex provider가 process 종료 전에도 event를 내보내기 시작한다.

- [ ] **Step 1: 같은 파일 안에서 stdout line iteration, timeout/exit normalization, collected stdout reconstruction을 담당하는 private helper를 만든다.**

Run: `uv run pytest tests/test_codex_provider.py -k "live_stream or timeout or failure_event_is_sanitized" -q`
Expected: `pytest PASS`

- [ ] **Step 2: `CodexCliProvider.stream_once()`가 `start`를 먼저 yield하고, fake Codex가 지연 출력할 때 첫 provider event가 `done` 전에 수집됨을 직접 증명하는 테스트와 함께 stdout line 즉시 방출 구조로 바꾼다.**

Run: `uv run pytest tests/test_codex_provider.py -k "stream_jsonl_success_events or live_stream or emits_before_process_exit or item_completed_agent_message or reasoning_and_tool_call_items" -q`
Expected: `pytest PASS`

- [ ] **Step 3: parse/stream 구조를 분리해도 raw secret, raw stderr, raw executable path가 최종 event에 남지 않는지 negative check를 유지한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_codex_provider.py -k "redacts_secrets or failure_event_is_sanitized or status_missing_cli_contract" -q`
Expected: `pytest PASS and no raw sentinel/raw stderr/raw executable path in captured AgentOS surfaces`

### Task 2: CLI live stream contract 유지

**파일:**
- 확인 후 필요 시 수정: `agentos/commands/run.py`
- 수정: `tests/test_cli_contract.py`

**사용자에게 보이는 마일스톤:** `agentos run --json --once --provider codex`는 같은 schema를 유지하면서 응답을 더 이르게 내보낸다.

- [ ] **Step 1: `run --json --once`가 live provider event를 schema 변화 없이 그대로 전달하는 focused regression을 추가하거나 갱신한다.**

Run: `uv run pytest tests/test_cli_contract.py -k "run_json" -q`
Expected: `pytest PASS`

- [ ] **Step 2: Codex live stream에서도 CLI surface가 error/recovery/redaction contract를 유지하는지 확인한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_cli_contract.py tests/test_codex_provider.py -k "codex and (secret or stderr or error)" -q`
Expected: `pytest PASS and no raw sentinel/raw stderr in captured AgentOS surfaces`

### Task 3: TUI loading/message regression 유지

**파일:**
- 확인 후 필요 시 수정: `agentos/terminal/tui/app.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** TUI는 live Codex event가 더 빨리 와도 `Thinking…`, assistant message 업데이트, usage/status 갱신 규칙을 유지한다.

- [ ] **Step 1: live Codex event arrival이 loading 제거와 assistant message 생성 타이밍을 깨지 않는 focused regression을 추가하거나 갱신한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "loading or codex" -q`
Expected: `pytest PASS`

- [ ] **Step 2: live stream 이후에도 마지막 turn status와 usage recording이 기존처럼 유지되는지 확인한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "usage or codex or last_turn" -q`
Expected: `pytest PASS`

### Task 4: 문서와 전체 검증

**파일:**
- 수정: `docs/cli-reference.md`
- 수정: `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
- 수정: 이 계획 문서 closeout sections

**사용자에게 보이는 마일스톤:** 사용자는 Codex 경로가 더 빨라졌지만 여전히 external CLI compatibility path임을 문서에서 바로 이해한다.

- [ ] **Step 1: CLI reference와 supporting note에 Codex live stream 변화와 native OAuth/transport 미포함 경계를 반영한다.**

Run: `grep -n "external CLI compatibility path\\|native OAuth/transport\\|stream" docs/cli-reference.md .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
Expected: 두 파일에서 live stream, external CLI compatibility path, native OAuth/transport deferred 경계를 설명하는 줄이 출력된다.

- [ ] **Step 2: focused suite와 관련 full regression을 실행한다.**

Run: `uv run pytest tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py tests/test_tui_cli.py -q`
Expected: `pytest PASS`

- [ ] **Step 3: completed active plan closeout 섹션을 채우고 plan board를 최신 상태로 갱신한다.**

Run: `grep -q '^> \*\*상태:\*\* 완료<br>$' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^> implementation_started_at: .\+' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^> implementation_completed_at: .\+' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^> implementation_duration: .\+' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^## 구현 결과$' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^## 사용 방법$' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^## 완료 증거$' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -q '^## 아카이브 결정$' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md && grep -A20 '^## 완료 증거$' .agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md | grep -q 'PASS ' && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`
Expected: completed active plan closeout 필드, 실제 PASS evidence, 비-placeholder 본문이 모두 채워진 뒤 exec-plan board가 최신 상태로 갱신된다

## 리뷰 반영 이력

- 2026-07-23 초안 작성:
  - 최근 코드 확인 결과 `CodexCliProvider.stream_once()`가 `subprocess.run(..., capture_output=True)` 때문에 전체 완료 후 재생 구조라는 점을 기준으로 latency-first 구조 개선 범위를 고정했다.
  - native OAuth/transport나 provider 확장으로 범위를 넓히지 않고, external CLI compatibility path 내부의 live streaming 구조와 focused regression만 이번 계획에 포함했다.
- [Gate 2 1차] usability-reviewer FAIL — `다음 단계`와 세션 체크포인트의 내부 용어가 설명 없이 노출됨 → 계획 리뷰 3개, 리뷰 증거 파일 확인, focused pytest, lifecycle refresh를 사용자 언어 + 괄호 설명으로 바꿨다.
- [Gate 2 1차] usability-reviewer FAIL — 멀티세션 체크포인트에 복구 경로가 없음 → 리뷰 증거 확인 실패 시와 테스트 실패 시의 되돌아가는 순서를 체크포인트에 추가했다.
- [Gate 2 1차] usability-reviewer FAIL — 사용자 진행 계획에 `preflight`, `contract`, `negative tests`, `closeout` 같은 구현 표현이 직접 노출됨 → 사용자 가시 결과 칸을 사용자 언어 중심으로 다시 작성했다.
- [Gate 2 현재 상태] `usability-reviewer`의 이전 PASS artifact는 plan hash mismatch로 stale 상태다. 현재 문서 기준 Gate 2를 닫으려면 reviewer 3종 artifact를 모두 현재 hash로 다시 기록해야 한다.
- [Gate 2 1차] principle-auditor REVISE — `run.py`와 TUI를 기본 수정 표면으로 잡아 단순성 게이트를 넓힘 → 두 consumer는 회귀 검증 대상, 필요 시에만 최소 수정으로 낮췄다.
- [Gate 2 1차] principle-auditor REVISE — 첫 응답이 종료 전 stream으로 관측된다는 핵심 증거가 약함 → fake Codex 지연 출력에서 첫 provider event가 `done` 전에 수집되는 focused test를 완료 신호와 Task 1 검증에 추가했다.
- [Gate 2 1차] principle-auditor REVISE — 신규 파일 생성이 과도하게 확정됨 → `codex_cli.py` 내부 private helper 기본 전략으로 축소하고, 별도 파일 분리는 필요 시로 낮췄다.
- [Gate 2 1차] principle-auditor REVISE — post-implementation 단계에 `review_artifacts.py check`를 성공 기준으로 둠 → Gate 2 artifact check는 구현 전 단계에서만 쓰고, 구현 후에는 closeout evidence와 board refresh만 남기도록 수정했다.
- [Gate 2 2차] plan-reviewer FAIL — `uv` readiness gate 누락과 reader-first 용어 잔여 지적 → `uv` 의존성 게이트와 Task 0 preflight를 추가하고, `Gate 2`, `focused pytest`, `deferred`, `closeout` 표현을 사용자 행동 중심 문구로 다시 정리했다.
- [Gate 2 2차] principle-auditor REVISE — Rule 7 브랜치 가드와 completed-plan closeout 검증이 약함 → Task 0에 non-`main` 브랜치 확인을 추가하고, Task 4 Step 3을 완료 metadata/섹션 전체 검증으로 강화했다.
- [Gate 2 3차] principle-auditor REVISE — 구현 시작 전 reviewer artifact 존재 확인과 완료 후 실제 PASS evidence 검증이 부족함 → Task 0에 Gate 2 artifact check를 추가하고, Task 4 Step 3이 placeholder 제거와 PASS 본문까지 검증하도록 더 강화했다.
- [Gate 2 3차] principle-auditor REVISE — canonical audit trace와 실제 review 상태 표기가 stale함 → traceability surface에 `.agents/traces/audit-plan-review.md`, `.agents/traces/audit-principle.md`를 추가하고, 진행 스냅샷/체크포인트를 current-hash usability PASS 상태에 맞게 갱신했다.
- [Gate 2 최종] `plan-reviewer`, `principle-auditor`, `usability-reviewer` 재심사 PASS를 현재 plan hash 기준 artifact로 재기록했고, `review_artifacts.py check`가 PASS를 반환했다.
- 구현 완료 — `CodexCliProvider.stream_once()`를 `Popen(..., stdout=PIPE)` 기반 live stream 구조로 전환했고, 실패 시 raw stderr/plaintext를 사용자 message로 먼저 노출하지 않도록 JSON 구조 이벤트만 실시간 방출하고 비구조 plaintext는 성공 시에만 최종 message로 반영하도록 정리했다. consumer(`run.py`, TUI)는 코드 수정 없이 회귀 검증만으로 유지했다.

## 구현 결과

구현을 provider-local 범위에서 마쳤다.

- `agentos/llm/providers/codex_cli.py`
  - `stream_once()`를 one-shot `subprocess.run(..., capture_output=True)`에서 `Popen(..., stdout=PIPE)` 기반 live stream으로 전환했다.
  - subprocess 생성과 종료 정규화를 private helper(`_open_codex_process`, `_completed_process_from_stream`)로 분리했다.
  - JSON 구조 이벤트(`reasoning`, `tool_call`, `tool_result`, `message_delta`)는 line-by-line으로 즉시 방출한다.
  - 비구조 plaintext는 성공 시에만 최종 `message_delta`로 반영하고, 실패 시에는 버려 raw stderr/plaintext가 사용자 표면으로 새지 않게 했다.
  - `start` 이벤트는 실제 스트림이 열릴 때만 먼저 방출하고, 실패 경로는 기존처럼 `error` 단일 이벤트를 유지한다.

- `tests/test_codex_provider.py`
  - 첫 provider event가 `done` 전에 관측되는지 timing test를 추가했다.
  - 실패/secret redaction 회귀를 새 구조에 맞게 유지 검증했다.

- `tests/test_cli_contract.py`
  - `agentos run --json --once --provider codex`가 live stream 구조에서도 기존 JSONL schema를 유지하는 focused regression을 추가했다.

- consumer surface
  - `agentos/commands/run.py`, `agentos/terminal/tui/app.py`는 수정하지 않았다.
  - 기존 generic stream 소비 구조가 그대로 유효함을 회귀 테스트로 확인했다.

## 사용 방법

사용 방법은 바뀌지 않는다.

CLI:

- `agentos run --once "Prompt" --provider codex --json`

TUI:

- 기존처럼 Codex provider를 선택한 뒤 메시지를 보내면 된다.

체감 변화:

- 이전에는 Codex CLI 프로세스가 끝난 뒤 JSON item을 한꺼번에 재생했다.
- 이제는 Codex CLI stdout의 JSON item이 도착하는 즉시 AgentOS event로 변환되어 더 빨리 보인다.
- 로그인/credential ownership은 그대로 Codex CLI가 가진다. AgentOS가 native OAuth/transport를 새로 소유하지는 않는다.

복구:

- Codex CLI가 없거나 인증이 깨졌으면 기존과 동일하게 `agentos llm login --provider codex` 또는 `codex login` 경로로 복구한다.

## 완료 증거

- `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`
- `PASS uv-ready`
- `PASS branch-guard-ready`
- `PASS codex-cli-compatibility-contract-ready`
- `PASS codex-stream-bottleneck-confirmed`
- `PASS codex-fake-cli-harness-ready`
- `PASS audit-trace-ready`
- `Run:` `uv run pytest tests/test_codex_provider.py -k "stream_jsonl_success_events or item_completed_agent_message or reasoning_and_tool_call_items or emits_before_process_exit or failure_event_is_sanitized or redacts_secrets or status_missing_cli_contract" -q` → `7 passed`
- `Run:` `uv run pytest tests/test_cli_contract.py -k "run_json or codex" -q` → `2 passed`
- `Run:` `uv run pytest tests/test_tui_cli.py -k "loading or codex or usage or last_turn" -q` → `10 passed`
- `Run:` `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_codex_provider.py tests/test_cli_contract.py tests/test_tui_cli.py -k "redact or secret or stderr or error" -q` → `11 passed`
- `Run:` `grep -n "external CLI compatibility path\|native OAuth/transport\|stream" docs/cli-reference.md .agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md` → 경계/stream 설명 출력 확인
- `Run:` `uv run pytest tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py tests/test_tui_cli.py -q` → `106 passed in 44.29s`

## 아카이브 결정

구현과 검증은 완료됐지만, 이 계획은 active completed plan으로 유지한다. archive는 사용자가 명시적으로 요청할 때만 실행한다.
