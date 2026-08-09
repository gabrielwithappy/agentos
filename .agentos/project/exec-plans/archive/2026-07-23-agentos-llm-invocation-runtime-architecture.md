# AgentOS LLM 호출 런타임 아키텍처 개선 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-23<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-23T23:43:15Z<br>
> implementation_completed_at: 2026-07-24T00:03:27Z<br>
> implementation_duration: 20m 12s<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** AgentOS의 체감 지연 원인을 `pi` 구조를 기준으로 측정 가능한 invocation 단계로 분해하고, `uv run` 가설이 사실일 때만 후속 runtime 분리 구현으로 넘어갈 수 있는 구조적 토대를 만든다.

**사용자 결과:** 사용자는 설치된 `agentos` command를 기본 경로로 써야 하는지, `uv run`이 실제 병목인지, 후속 daemon 분리를 진행해도 되는지를 benchmark와 복구 절차로 명확히 판단할 수 있다. 바뀌지 않는 경계는 현재 `codex`가 여전히 external CLI compatibility path를 사용한다는 점, native OAuth/transport를 이번 범위에 넣지 않는다는 점, raw token/env/provider stderr 비노출 규칙을 유지한다는 점이다.

**진행 상태:** 측정 우선의 invocation runtime surface, typed invocation contract, launcher/recovery guidance, docs/project boundary, focused tests, isolated install smoke, full public suite 검증을 완료했다.

**아키텍처:** `pi-coding-agent`가 app layer, `pi-agent`가 turn runtime, `pi-ai`가 provider integration을 소유하는 구조를 AgentOS에 맞게 번역하되, 이번 계획에서는 소비자 전환까지 바로 하지 않는다. 먼저 `agentos/runtime` benchmark/protocol surface를 만들어 launcher, bootstrap, provider, persistence 비용을 분리 측정하고, 그 결과가 명확할 때만 후속 plan에서 `run.py`와 TUI를 client/consumer로 옮긴다. 이번 계획의 산출물은 측정 surface, installed-launcher 증거, 사용자 복구 절차, 후속 분리 착수 여부를 판단하는 go/no-go gate다.

**기술 스택:** Python 3.12+, Typer, Textual, pytest, existing `uv` environment, existing `codex` external CLI compatibility path, benchmark helper scripts, typed runtime protocol surface.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | `agentos.runtime` benchmark/protocol surface, `agentos.llm.invocation` wrapper, `doctor --json` launcher/runtime recovery fields, isolated install smoke, docs/project/CLI reference alignment, focused/full verification |
| 현재 위치 | 구현 및 검증 완료, active plan closeout 기록 |
| 다음 단계 | 사용자가 요청하면 archive 또는 후속 daemon/server-client 분리 계획 작성 |
| 완료 신호 | `PASS invocation-baseline-captured`, `PASS runtime-boundary-documented`, focused runtime tests PASS, `PASS canonical-launcher-guidance`, `PASS agentos-cli-isolated-install`, `PASS invocation-runtime-benchmark`, `149 passed`, `sync-manifest --check` PASS |

## 세션 인계 체크포인트

- 현재 완료 범위: invocation runtime measurement/protocol/doctor/docs/install smoke/test coverage 구현 및 검증 완료.
- 미완료 작업: 없음. archive는 사용자 명시 요청 전까지 보류.
- 다음 세션 첫 작업: 사용자가 원하면 이 active completed plan을 archive하거나, benchmark PASS evidence를 근거로 별도 daemon/server-client 분리 계획을 작성한다.
- 아직 안 한 검증: 없음.
- 관련 HISTORY checkpoint: 2026-07-24 `agentos-llm-invocation-runtime-architecture` 구현 완료 closeout.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `uv run`이 병목인지 아닌지와, 후속 runtime 분리를 진행할지 중단할지를 판단할 수 있는 benchmark와 복구 절차 |
| 누구를 위한 것인가? | AgentOS CLI/TUI를 반복 실행하는 개발자와 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 설치된 `agentos`와 개발용 `uv run`의 역할이 분리되고, 설치/실행/복구 판단 기준이 명확해진다 |
| 무엇은 바뀌지 않는가? | `codex` external CLI compatibility path, native OAuth/transport 제외, current redaction boundary |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 기준선 측정 | 무엇이 실제로 느린지 phase timings로 구분된다 | `agentos/runtime/bench.py`, tests, docs | 완료: `PASS invocation-baseline-captured` |
| 2. 측정용 runtime contract | 어떤 단계가 느린지 같은 request/event/timings schema로 비교된다 | `agentos/runtime/`, `agentos/llm/invocation.py`, tests | 완료: `tests/test_runtime_protocol.py` PASS |
| 3. launcher 경계와 복구 절차 | 설치된 `agentos`와 `uv run`의 차이, 실패 시 다음 행동이 분명해진다 | doctor/help/docs/install smoke | 완료: `PASS canonical-launcher-guidance`, `PASS agentos-cli-isolated-install` |
| 4. go/no-go 결정 표면 | 후속 daemon 분리를 진행할지 중단할지 benchmark 결과로 판정된다 | benchmark output, docs/project, `docs/cli-reference.md` | 완료: `PASS invocation-runtime-benchmark` |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, `.agents/traces/reviews/2026-07-23-agentos-llm-invocation-runtime-architecture/`, `.agents/traces/audit-plan-review.md`, `.agents/traces/audit-principle.md`
- durable result surface: `.agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md`, `agentos/runtime/`, `agentos/llm/invocation.py`, `agentos/commands/doctor.py`, `docs/cli-reference.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `scripts/verify-cli-isolated-install.sh`, `tests/test_runtime_protocol.py`, `tests/test_runtime_bench.py`
- documentation-only exception: 없음. 최종 결과는 benchmark/protocol 코드, install smoke, recovery 문서, docs/project 판단 표면에 남아야 한다.

## 의존성 분석

- 외부 의존성: 없음. 이번 계획은 측정, 판단, launcher 증거, recovery 표면 정의까지만 다룬다.
- 로컬 의존성: current Python/Typer/Textual codebase, existing `codex` compatibility provider, `references/pi` read-only architecture evidence.
- 범위 충돌 주의: `.agentos/project/exec-plans/active/2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md`는 `run.py`, TUI, canonical runtime ownership, native transport ownership을 다룬다. 이번 계획은 그 표면을 수정하지 않고 benchmark/protocol/launcher proof만 다룬다.
- 측정 합격 기준: `uv_run.first_event_ms - runtime_warm.first_event_ms >= 250` 이고 `runtime_warm.bootstrap_ms < uv_run.bootstrap_ms`일 때만 warm-path 개선 PASS로 본다. 수치가 충족되지 않으면 daemon/server-client 분리 follow-up은 작성하지 않고, benchmark/docs/install guidance만 남긴 채 이 계획을 closeout한다.

## 사용자 복구 절차

1. 설치된 `agentos`가 없을 때:
   Run: `bash scripts/verify-cli-isolated-install.sh`
   Expected: `PASS agentos-cli-isolated-install`
   다음 행동: 설치형 entrypoint가 준비되기 전까지는 `uv run agentos ...`를 개발용 경로로만 사용한다.
2. `agentos doctor`의 runtime health check가 실패할 때:
   Run: `uv run agentos doctor --json`
   Expected: JSON에 `runtime`, `recovery`, `next_action`이 포함된다.
   다음 행동: stale runtime/socket 정리 후 benchmark를 다시 실행한다. recovery 문구가 `runtime cleanup 후 재시도`를 가리켜야 한다.
3. benchmark 결과가 기대보다 느릴 때:
   Run: `uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --assert-warm-faster`
   Expected: `PASS invocation-runtime-benchmark`가 아니면 후속 daemon 분리를 진행하지 않는다.
   다음 행동: 현재 external CLI compatibility path를 유지하고 benchmark 결과를 supporting note에 기록한 뒤 계획을 closeout한다.

## 의존성 게이트

### pi-runtime-evidence-ready

- name: pi-runtime-evidence-ready
- type: local-reference
- required: true
- purpose: `pi`의 app layer / agent runtime / ai integration 분리 구조를 계획 근거로 사용할 수 있는지 확인한다.
- preflight:
  Run: `grep -q "pi-coding-agent" .agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md && grep -q "pi-agent" .agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md && grep -q "pi-ai" .agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md && echo "PASS pi-runtime-evidence-ready"`
  Expected: `PASS pi-runtime-evidence-ready`
- fallback:
  available: false
  reason: 구조 근거가 없으면 invocation runtime 분리 계획이 다시 추측에 의존하게 된다.
- failure_behavior: NEEDS_CONTEXT

### current-boundary-measured

- name: current-boundary-measured
- type: local-benchmark
- required: true
- purpose: `uv run`이 진짜 가장 큰 병목인지, 아니면 provider/persistence/UI 결합이 더 큰지 phase timings로 먼저 검증한다.
- preflight:
  Run: `grep -q "5.1s~5.3s" .agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md && grep -q "5.3s~6.1s" .agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md && echo "PASS current-boundary-measured"`
  Expected: `PASS current-boundary-measured`
- fallback:
  available: true
  reason: 추가 측정이 필요하면 benchmark helper를 먼저 구현하고 이후 단계로 진행한다.
- failure_behavior: CONTINUE_WITH_BENCH_TASK

## 파일 구조

- 생성: `agentos/runtime/__init__.py`
- 생성: `agentos/runtime/protocol.py`
- 생성: `agentos/runtime/bench.py`
- 생성: `agentos/llm/invocation.py`
- 수정: `agentos/commands/doctor.py`
- 수정: `docs/cli-reference.md`
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`
- 생성: `tests/test_runtime_protocol.py`
- 생성: `tests/test_runtime_bench.py`
- 수정: `scripts/verify-cli-isolated-install.sh`

## 구현 작업

### Task 0: 기준선 측정과 stop gate 고정

**파일:**
- 생성: `agentos/runtime/bench.py`
- 수정: `.agentos/project/03-system-contract.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`

**사용자에게 보이는 마일스톤:** 사용자는 느린 원인이 무엇인지 추측이 아니라 phase timings로 확인할 수 있다.

- [x] **Step 1: 현재 `uv run agentos`, 설치된 `agentos`, direct provider path, warm runtime path를 같은 prompt로 비교하는 benchmark surface를 만든다.**

Run: `uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --format json >/tmp/agentos-runtime-bench.json && python3 - <<'PY'\nimport json\np=json.load(open('/tmp/agentos-runtime-bench.json'))\nassert all(k in p for k in ('uv_run','installed_cli','direct_provider','runtime_warm'))\nassert all('first_event_ms' in p[k] and 'bootstrap_ms' in p[k] for k in ('uv_run','installed_cli','direct_provider','runtime_warm'))\nprint('PASS invocation-baseline-captured')\nPY`
Expected: `PASS invocation-baseline-captured`

- [x] **Step 2: system contract와 safety matrix에 invocation runtime phase timings, canonical launcher, recovery boundary를 기록한다.**

Run: `grep -q "invocation runtime" .agentos/project/03-system-contract.md && grep -q "phase timings" .agentos/project/04-safety-risk-verification.md && echo "PASS runtime-boundary-documented"`
Expected: `PASS runtime-boundary-documented`

- [x] **Step 3: benchmark가 합격 기준을 못 넘으면 daemon follow-up을 중단한다는 stop gate를 문서와 코드 표면에 고정한다.**

Run: `grep -q "daemon/server-client 분리 follow-up은 작성하지 않고" .agentos/project/exec-plans/active/2026-07-23-agentos-llm-invocation-runtime-architecture.md && echo "PASS hypothesis-stop-gate-locked"`
Expected: `PASS hypothesis-stop-gate-locked`

### Task 1: 측정용 invocation runtime contract 도입

**파일:**
- 생성: `agentos/runtime/protocol.py`
- 생성: `agentos/llm/invocation.py`
- 생성: `tests/test_runtime_protocol.py`

**사용자에게 보이는 마일스톤:** 어떤 단계가 느린지 같은 request/event/timings schema로 비교할 수 있다.

- [x] **Step 1: runtime request와 normalized event/timings schema를 typed contract로 고정한다.**

Run: `uv run pytest tests/test_runtime_protocol.py -k "request_schema or event_schema or timings_schema" -q`
Expected: `pytest PASS`

- [x] **Step 2: invocation layer가 provider facade 호출을 감싸고 `session_id`, `transport_hint`, `record_policy`, `timings`를 함께 다루도록 만든다.**

Run: `uv run pytest tests/test_runtime_protocol.py -k "invocation_layer or codex_facade_bridge" -q`
Expected: `pytest PASS`

- [x] **Step 3: current `codex_cli` provider를 유지한 채 측정용 invocation contract 아래에서만 호출한다.**

Run: `uv run pytest tests/test_codex_provider.py tests/test_runtime_protocol.py -k "codex and (runtime or stream)" -q`
Expected: `pytest PASS`

### Task 2: launcher 경계 분리와 사용자 복구 절차

**파일:**
- 수정: `agentos/commands/doctor.py`
- 수정: `docs/cli-reference.md`
- 수정: `scripts/verify-cli-isolated-install.sh`

**사용자에게 보이는 마일스톤:** 설치된 `agentos`가 기본 경로인지와 실패 시 다음 행동이 사용자 절차로 보인다.

- [x] **Step 1: 설치된 console script가 실제로 동작한다는 isolated install smoke를 canonical 증거로 고정한다.**

Run: `bash scripts/verify-cli-isolated-install.sh`
Expected: `PASS agentos-cli-isolated-install`

- [x] **Step 2: `agentos doctor`가 설치된 `agentos`가 없을 때, runtime health check가 실패할 때, stale runtime cleanup이 필요할 때의 다음 행동을 JSON으로 안내하도록 바꾼다.**

Run: `uv run agentos doctor --json >/tmp/agentos-doctor.json && python3 - <<'PY'\nimport json\np=json.load(open('/tmp/agentos-doctor.json'))\nassert 'launcher' in p and 'runtime' in p and 'recovery' in p and 'next_action' in p\nprint('PASS canonical-launcher-guidance')\nPY`
Expected: `PASS canonical-launcher-guidance`

- [x] **Step 3: docs에 설치 실패, runtime health 실패, benchmark 미통과 시의 사용자 절차를 명시한다.**

Run: `grep -q "설치된 agentos가 없을 때" docs/cli-reference.md && grep -q "runtime health check가 실패할 때" docs/cli-reference.md && grep -q "benchmark 결과가 기대보다 느릴 때" docs/cli-reference.md && echo "PASS recovery-docs-aligned"`
Expected: `PASS recovery-docs-aligned`

### Task 3: 개선 근거와 go/no-go 결정 표면 고정

**파일:**
- 생성: `tests/test_runtime_bench.py`
- 수정: `docs/cli-reference.md`

**사용자에게 보이는 마일스톤:** 사용자는 후속 daemon 분리를 진행할지 중단할지 benchmark 결과로 판단할 수 있다.

- [x] **Step 1: docs에 설치된 `agentos`를 canonical path로, `uv run`을 개발용 path로 설명한다.**

Run: `grep -q "canonical" docs/cli-reference.md && grep -q "uv run" docs/cli-reference.md && grep -q "warm runtime" docs/cli-reference.md && echo "PASS launcher-docs-aligned"`
Expected: `PASS launcher-docs-aligned`

- [x] **Step 2: benchmark regression test가 warm runtime 경로의 추가 오버헤드와 launcher phase delta를 검증한다.**

Run: `uv run pytest tests/test_runtime_bench.py -k "warm_runtime_overhead or launcher_phase_delta" -q`
Expected: `pytest PASS`

- [x] **Step 3: end-to-end benchmark command가 합격 기준을 한 줄 PASS 신호로 출력하고, 실패 시 후속 분리를 중단해야 함을 분명히 한다.**

Run: `uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --assert-warm-faster`
Expected: `PASS invocation-runtime-benchmark` only when `uv_run.first_event_ms - runtime_warm.first_event_ms >= 250` and `runtime_warm.bootstrap_ms < uv_run.bootstrap_ms`; otherwise the command prints a non-PASS result and this plan stops without daemon migration

## 리뷰 반영 이력

- 2026-07-23 초안 작성:
  - `pi`의 app layer / agent runtime / ai integration 분리 구조를 read-only 근거로 사용해 AgentOS invocation runtime 계획 초안을 작성했다.
  - current `codex` external CLI compatibility path는 유지하고, native auth/transport active plan과 write scope가 겹치지 않도록 launcher/runtime/client boundary 전용 범위로 제한했다.
  - `uv run`이 체감 지연의 전부라고 단정하지 않고, benchmark surface를 먼저 만드는 Task 0을 선행 조건으로 고정했다.
- 2026-07-23 `plan-reviewer` FAIL 반영:
  - warm-path 개선 PASS 기준을 `250ms` 이상 차이와 `bootstrap_ms` 비교로 명시했다.
  - benchmark output에 `runtime_warm`과 phase timings를 필수 필드로 추가했다.
  - 설치형 launcher 증거를 `uv` 경로 추론이 아니라 `scripts/verify-cli-isolated-install.sh` 기반 실제 console-script smoke로 강화했다.
- 2026-07-23 `principle-auditor` FAIL 반영:
  - Task 0이 `uv run` 가설을 뒤집으면 daemon/server-client follow-up을 중단하도록 stop gate를 추가했다.
  - `run.py`, TUI, canonical runtime ownership 전환은 이번 계획에서 제외하고, native auth/transport active plan과 겹치지 않도록 benchmark/protocol/launcher proof 범위로 축소했다.
- 2026-07-23 `usability-reviewer` FAIL 반영:
  - 설치된 `agentos`가 없을 때, runtime health check가 실패할 때, benchmark 결과가 기대보다 느릴 때의 다음 행동을 `doctor`/docs 표면에 명시하도록 바꿨다.
  - 사용자 결과와 마일스톤을 "지금 판단할 수 있는 것" 중심으로 다시 정리했다.

## 구현 결과

- `agentos/runtime/protocol.py`: `RuntimeRequest`, `RuntimeTimings`, `InvocationEvent` typed schema를 추가했다.
- `agentos/llm/invocation.py`: 기존 provider facade를 유지하면서 invocation timing metadata를 붙이는 measurement-only wrapper를 추가했다.
- `agentos/runtime/bench.py`: `uv_run`, `installed_cli`, `direct_provider`, `runtime_warm` phase timings와 warm-path go/no-go 판정을 출력한다.
- `agentos doctor --json`: 기존 state status를 유지하면서 `launcher`, `runtime`, `recovery`, `next_action` 필드를 추가했다.
- `docs/cli-reference.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`: installed `agentos` canonical path, `uv run` development path, phase timings, recovery 절차, daemon follow-up stop gate를 기록했다.
- `scripts/verify-cli-isolated-install.sh`: installed wheel에서 runtime package, doctor JSON, benchmark JSON이 동작하는지 확인한다.
- `pyproject.toml`과 `.gitignore`: `agentos/runtime` package가 isolated wheel에 포함되도록 조정했다.

## 사용 방법

```bash
uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --format json
uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --assert-warm-faster
uv run agentos doctor --json
bash scripts/verify-cli-isolated-install.sh
```

`PASS invocation-runtime-benchmark`가 출력될 때만 후속 daemon/server-client 분리 계획을 작성할 근거가 생긴다. 이번 구현은 daemon을 추가하지 않고 measurement/runtime contract와 launcher recovery surface까지만 만든다.

## 완료 증거

- `PASS invocation-baseline-captured`
- `PASS runtime-boundary-documented`
- `PASS hypothesis-stop-gate-locked`
- `uv run pytest tests/test_runtime_protocol.py -k "request_schema or event_schema or timings_schema" -q` -> 3 passed
- `uv run pytest tests/test_runtime_protocol.py -k "invocation_layer or codex_facade_bridge" -q` -> 2 passed
- `uv run pytest tests/test_codex_provider.py tests/test_runtime_protocol.py -k "codex and (runtime or stream)" -q` -> 8 passed
- `PASS canonical-launcher-guidance`
- `PASS recovery-docs-aligned`
- `PASS launcher-docs-aligned`
- `uv run pytest tests/test_runtime_bench.py -k "warm_runtime_overhead or launcher_phase_delta" -q` -> 2 passed
- `bash scripts/verify-cli-isolated-install.sh` -> `PASS agentos-cli-isolated-install`
- `uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --assert-warm-faster` -> `PASS invocation-runtime-benchmark`
- `uv run pytest tests/test_runtime_protocol.py tests/test_runtime_bench.py tests/test_cli_isolated_install.py tests/test_codex_provider.py tests/test_llm_core.py tests/test_cli_contract.py -q` -> 53 passed
- `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_runtime_protocol.py tests/test_runtime_bench.py tests/test_codex_provider.py tests/test_llm_core.py -k "redact or secret or stderr or error or runtime" -q` -> 16 passed
- `uv run pytest tests/ -q` -> 149 passed
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` -> PASS

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 이 완료된 계획은 active에 남긴다.
