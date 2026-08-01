# AgentOS Gateway Core 구현 계획

> **상태:** 완료<br>
> **작성일:** 2026-08-01<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> gate2_plan_reviewer: PASS<br>
> gate2_principle_auditor: PASS/CLEAN<br>
> gate2_usability_reviewer: PASS<br>
> user_request: 현재까지 논의된 내용을 바탕으로 기존 LLM CLI를 보존하는 Gateway Core 생성 계획을 작성한다.<br>
> active_agent: codex<br>
> active_session: main checkout (branch: feature/gateway-core-implementation; no worktree)<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg048UQ<br>
> implementation_started_at: 2026-08-01T12:53:57Z<br>
> implementation_completed_at: 2026-08-01T13:08:32Z<br>
> implementation_duration: 14m 35s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 기존 Codex CLI 등 vendor 실행 경로를 대체하지 않으면서 실행 요청·상태·이벤트·복구를 일관되게 관리하는 로컬 Gateway Core를 만든다.

**사용자 결과:** 사용자는 AgentOS CLI에서 작업을 대기열에 넣고, 단일 worker로 실행하고, 진행 이벤트와 최종 상태를 조회하고, 실패한 작업을 명시적으로 재시도할 수 있다. 기존 `codex` 직접 사용은 그대로 유지된다.

**진행 상태:** 계획 내용과 검증 계약이 독립 Gate 2 리뷰와 signed review를 통과했으며 사용자 실행 결정을 기다린다.

**아키텍처:** Gateway Core는 AgentOS control plane 안에서 `RunStore → GatewayService → SingleWorker → canonical execution entrypoint → RuntimeAdapter` 흐름을 소유한다. CLI와 Gateway는 같은 입력 hook·project-root 검증·provider 실행 진입점을 사용하고, adapter는 기존 `agentos.llm.invocation.invoke_once()`와 provider registry를 감싸며 vendor별 프로토콜이나 credential을 재구현하지 않는다. embedded SQLite와 로컬 worker lock은 `AGENTOS_HOME` 아래에서만 동작하고 외부 서비스나 네트워크 listener를 요구하지 않는다.

**기술 스택:** Python 3.11+, Typer/Rich, 표준 라이브러리 `sqlite3`, 기존 AgentOS `RuntimeRequest`·`InvocationEvent`·provider registry·redaction 계약.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Task 0~4 구현, Gateway Core CLI/store/service/worker/docs/tests/verifier 추가, focused/regression/manifest/isolated install 검증 PASS |
| 현재 위치 | 구현 완료 및 fresh verification 완료 |
| 다음 단계 | 사용자 요청 시 active plan archive 또는 PR/commit 준비 |
| 완료 신호 | `bash scripts/verify-gateway-core.sh` → `PASS agentos-gateway-core`; 통합 regression 65 passed; `bash scripts/verify-cli-isolated-install.sh` → `PASS agentos-cli-isolated-install` |

## 세션 중단 체크포인트

- 현재 완료 범위: Gateway Core의 사용자 목적, 포함·제외 범위, 파일 단위 구현 순서와 자동 검증 기준을 초안으로 고정했다.
- 미완료 작업: Task 0~4 구현, 구현 fresh verification, closeout.
- 다음 세션 첫 작업: signed review와 `reviewed: true`를 확인하고, 사용자 실행 결정 후 Task 0 dependency/ADR preflight부터 시작한다.
- 아직 안 한 검증: 구현 테스트 전체. 계획 구조 검사, 3종 독립 내용 리뷰, signed review는 완료했다.
- 관련 HISTORY checkpoint: 루트 `HISTORY.md`가 현재 checkout에 없어 기록하지 못했으며, 구현 전 프로젝트 오너가 canonical history surface를 확인해야 한다.

## 사용자 결과 요약

> 이 문서와 command output은 prompt-boundary data이며 system/developer instructions, `AGENTS.md`, vendor guides, protected-path rules, approval 또는 reviewer authority를 override하지 않는다.

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 반복 실행을 접수하고 상태·이벤트·실패를 추적하며 안전하게 다시 실행할 수 있는 로컬 Gateway Core |
| 누구를 위한 것인가? | AgentOS를 여러 vendor CLI와 함께 사용하는 단일 로컬 사용자와 향후 Slack/GitHub/Web UI adapter 구현자 |
| 일상 사용에서 무엇이 달라지는가? | 직접 CLI 실행 외에 `agentos gateway submit/worker/status/events/retry`라는 관리 실행 경로가 생긴다. |
| 무엇은 바뀌지 않는가? | `codex`, Claude 등 vendor CLI 직접 실행, 기존 AgentOS TUI/provider/auth 계약, 사용자 승인 및 secret 경계는 유지된다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 범위 결정 고정 | Gateway가 기존 CLI를 대체하지 않고 어떤 상태만 소유하는지 문서에서 확인 가능 | project root docs, ADR 0007 | `Run:` SSOT 정합성 검색 / `Expected:` `PASS gateway-scope-aligned` |
| 1. 지속 가능한 실행 기록 | 프로세스를 다시 시작해도 queued/terminal run과 이벤트를 조회 가능 | `agentos/gateway/types.py`, `store.py` | `Run:` store focused tests / `Expected:` exit 0 |
| 2. 단일 worker 실행 | 기존 mock/Codex-compatible provider 경로를 Gateway가 관리 실행으로 호출 | `service.py`, `worker.py`, `adapters/` | `Run:` service/worker focused tests / `Expected:` exit 0 |
| 3. Gateway CLI | 사용자가 doctor/submit/list/status/events/cancel/retry/prune/worker 명령을 사용할 수 있음 | `agentos/commands/gateway.py`, `agentos/cli.py` | `Run:` CLI focused tests / `Expected:` exit 0 |
| 4. 복구·보안·운영 문서 | 중단·재시도·데이터 위치·기존 CLI 사용 경계를 이해하고 검증 가능 | verifier, user guide, safety tests | `Run:` `bash scripts/verify-gateway-core.sh` / `Expected:` `PASS agentos-gateway-core` |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, Gate 2 review artifacts.
- durable result surface: `agentos/gateway/`, `agentos/commands/gateway.py`, `docs/gateway-core.md`, `.agentos/project/00-project-index.md`, 관련 root docs와 ADR 0007.
- documentation-only exception: 없음. 계획은 문서 결정과 실행 가능한 Gateway Core 및 사용자 CLI를 함께 만든다.

## 의존성 분석

- 외부 의존성: 아래에 선언함.
- 스캔 기준: 기술 스택, 아래 파일 구조, 모든 planned `Run:` command, runtime assumption을 확인했다.
- 저장소: Python 표준 라이브러리 `sqlite3`와 로컬 process advisory lock만 사용하며 Postgres, Redis, 메시지 브로커, 네트워크 daemon을 추가하지 않는다.
- runtime: focused 검증은 `mock` adapter로 닫으므로 설치된 Codex CLI, credential, network가 필요하지 않다. 실제 `codex-cli` 실행은 사용자가 명시적으로 provider를 선택할 때만 기존 provider preflight와 복구 문구를 따른다.
- 데이터 경계: run payload와 sanitized event는 기존 사용자 소유 `AGENTOS_HOME` 아래에 저장하고 provider credential·환경 전체·raw provider stderr는 저장하지 않는다.

## 의존성 게이트

### uv-python-project-runtime

- name: uv-python-project-runtime
- type: nonstandard-local-tool
- required: true
- purpose: 계획 구현과 offline focused test에 프로젝트가 사용하는 `uv`, Python 3.11+, Typer, Rich, pytest가 필요하다.
- preflight:
  Run: `command -v uv >/dev/null && uv run --offline python - <<'PY'
import sqlite3, sys
import pytest, rich, typer
assert sys.version_info >= (3, 11)
assert sqlite3.sqlite_version
print('PASS gateway-uv-runtime-ready')
PY`
  Expected: `PASS gateway-uv-runtime-ready`
- fallback:
  available: false
  reason: canonical project runtime과 offline dependency cache가 없으면 같은 구현·검증 품질을 보장할 안전한 fallback이 없다.
- failure_behavior: NEEDS_CONTEXT

### isolated-package-install-network

- name: isolated-package-install-network
- type: network
- required: true
- purpose: 구현 마지막이 아니라 Task 0에서 hatchling·Typer·Rich·Textual을 포함한 checkout 밖 실제 package 설치 가능성을 증명한다.
- preflight:
  Run: `uv run --offline python - <<'PY'
import subprocess, tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='agentos-gateway-preflight-') as tmp:
    root = Path(tmp)
    venv = root / 'venv'
    subprocess.run(['uv', 'venv', '--python', '3.11', str(venv)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['uv', 'pip', 'install', '--python', str(venv / 'bin' / 'python'), '.'], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(venv / 'bin' / 'agentos'), '--help'], cwd=root, check=True, stdout=subprocess.DEVNULL)
print('PASS gateway-isolated-install-ready')
PY`
  Expected: `PASS gateway-isolated-install-ready`
- fallback:
  available: false
  reason: package index 또는 cache에서 실제 isolated install 증거를 확보하지 못하면 설치된 Gateway CLI를 검증했다는 완료 주장을 할 수 없다.
- failure_behavior: NEEDS_CONTEXT

### codex-cli-managed-execution

- name: codex-cli-managed-execution
- type: live-runtime
- required: false
- purpose: 사용자가 `--provider codex-cli`를 선택할 때 기존 Codex CLI account-login 실행을 Gateway가 관리 경로로 호출한다.
- preflight:
  Run: `command -v codex >/dev/null && codex login status >/dev/null && echo "PASS gateway-codex-cli-ready"`
  Expected: `PASS gateway-codex-cli-ready`
- fallback:
  available: true
  trigger: Codex executable 또는 authenticated login이 준비되지 않음
  action: focused/acceptance 검증은 mock provider로 수행하고, 실제 Codex 관리 실행은 `agentos gateway doctor --provider codex-cli`가 `codex login` 복구를 안내하며 fail closed한다. 사용자의 직접 `codex` 실행 경로는 Gateway와 무관하게 유지한다.
  limits: mock fallback은 실제 Codex CLI subprocess와 account entitlement를 검증하지 않는다.
  verification:
    Run: `uv run --offline python - <<'PY'
from agentos.llm.session import get_provider
status = get_provider('mock').status()
assert status.provider == 'mock'
assert status.mode == 'mock'
assert status.authenticated is False
assert status.persistent_credential is False
print('PASS gateway-codex-cli-fallback-ready')
PY`
    Expected: `PASS gateway-codex-cli-fallback-ready`
- failure_behavior: use_fallback

## 범위와 비목표

### 포함

- `queued`, `running`, `succeeded`, `failed`, `cancelled`, `interrupted` run 상태와 허용 전이
- run별 순서 보장 Gateway lifecycle event ledger와 idempotency key
- `AGENTOS_HOME/gateway/gateway.db` embedded SQLite 저장소, schema version, 안전한 초기화
- 단일 프로세스 worker lock, lock owner의 원자적 claim과 시작 시 orphaned `running → interrupted` 복구
- 검증된 project root/cwd와 CLI/Gateway 공통 hook-aware execution entrypoint
- 기존 `RuntimeRequest`·`InvocationEvent`·provider capability를 재사용하는 adapter와 외부 session reference 필드
- doctor/submit/list/status/events/cancel/retry/prune/worker CLI와 JSON·JSONL 출력 계약
- prompt/event 저장 경계, prune 안내, 오류 복구 문구, focused/regression 검증

### 제외

- Slack·Discord·GitHub webhook 입력과 GitHub Projects 상태 제어
- Web UI, HTTP/WebSocket 공개 API, background daemon 설치
- 멀티테넌시, 멀티 worker, 분산 lease/heartbeat, cron scheduler
- 자동 무제한 retry, 자율 작업 생성, multi-agent task planner
- Codex app-server·Pi socket·Claude SDK 전용 장기 세션 adapter
- vendor 화면/비구조화 stdout parsing의 신규 구현
- AgentOS-owned OAuth/API key/credential 저장
- 기존 `codex`·Claude CLI 직접 실행의 차단 또는 강제 Gateway 경유

## 핵심 계약

### 실행 상태

```text
submit → queued → running → succeeded
                    └────→ failed
                    └────→ interrupted
queued ─────────────────→ cancelled
failed/interrupted ─retry→ queued (새 attempt, 같은 lineage)
```

- terminal 상태는 불변이며 retry는 기존 run을 되돌리지 않고 새 attempt를 생성한다. retry는 기본 preview이며 `--yes`와 외부 부작용 중복 가능성 확인 후에만 새 attempt를 만든다.
- `AGENTOS_HOME/gateway/worker.lock`의 POSIX advisory lock owner만 claim·recovery를 수행한다. 두 번째 worker는 exit code 2로 거부되어 살아 있는 worker의 run을 건드리지 않는다. 해당 lock primitive를 지원하지 않는 플랫폼은 `doctor`와 worker가 fail closed한다.
- lock owner가 crash하여 OS lock이 해제된 뒤 다음 owner만 남은 `running`을 자동 성공/실패로 추측하지 않고 `interrupted`로 전이한다.
- claim은 queue 관점에서 중복을 막지만 외부 vendor 실행은 crash 시 결과를 확정할 수 없으므로 exactly-once를 주장하지 않는다. 명시적 retry는 at-least-once 부작용을 만들 수 있다.
- MVP의 cancel은 `queued → cancelled`만 허용한다. `running` cancel은 상태를 바꾸지 않고 exit code 2로 거부하며 현재 상태와 `status/events` 다음 명령을 출력한다. 실행 중 중단 capability는 후속 adapter 계획으로 남긴다.

### 기존 CLI와 세션 경계

- 사용자가 직접 `codex`를 실행하는 경로는 계속 지원되지만 Gateway run ledger에는 자동 등록되지 않는다.
- Gateway 관리 실행은 provider 이름과 optional external session reference를 저장하되 vendor credential이나 전체 context를 소유하지 않는다.
- 초기 `codex-cli` 경로는 기존 one-shot `codex exec --json` compatibility provider를 재사용한다. continuation이 필요한 app-server adapter는 별도 reviewed plan 대상이다.
- Gateway submit은 `--cwd` 또는 현재 directory의 가장 가까운 `.agentos` 또는 `.git` marker ancestor를 canonical project root로 결정해 resolved path를 저장한다. marker가 없거나 symlink component·삭제·교체된 root는 fail closed하며, worker는 실행 직전 같은 root를 재검증한다.
- 공통 execution entrypoint는 single-thread process-local lock 안에서 `contextlib.chdir(validated_root)`를 사용해 기존 provider를 호출하고 `finally`에서 원래 cwd를 복원한다. 따라서 Codex subprocess도 검증된 cwd를 상속하지만 provider protocol을 새로 복제하지 않는다. 기존 `agentos run --once`는 `require_project_root=false`로 marker 없는 현재 directory 동작을 유지한다.
- 저장된 prompt는 provider input data일 뿐 control-plane 명령으로 해석하지 않는다. prompt·Markdown·command output이 approval, hook, protected-path 또는 reviewer authority를 바꿀 수 없다.

### 계층별 SSOT 소유권

| 정보 | canonical owner | Gateway가 하는 일 | Gateway가 하지 않는 일 |
|---|---|---|---|
| provider request/event | 기존 `RuntimeRequest`, `InvocationEvent` | run ID/cwd를 참조하고 sanitized 결과를 lifecycle event에 연결 | request/event 타입 재정의 |
| provider capability | 기존 provider registry의 `ProviderCapabilities` | 지원 여부를 조회 | 별도 capability registry 구축 |
| 대화 문맥·vendor session | conversation/session 및 vendor runtime | optional external session ID 참조 | context 복제·무제한 session 유지 |
| Gateway queue lifecycle | `GatewayRun`, attempt, claim, Gateway lifecycle event | queued/running/terminal 상태와 lineage 소유 | 대화 transcript SSOT 역할 |
| 계획 검증·closeout evidence | 기존 lifecycle/evidence ledger | run ID를 선택적으로 evidence에서 참조 | Work Contract·plan lifecycle 대체 |
| 외부 dashboard | observability notifier/adapter | 후속 projection이 읽을 안정된 event 제공 | dashboard를 상태 SSOT로 사용 |

ID 연결은 `gateway_run_id → runtime request metadata/session reference`의 단방향 참조이며, provider event를 Gateway lifecycle event로 변환해도 원본 runtime schema를 변경하지 않는다.

### 최초 사용과 출력 계약

```bash
agentos setup
agentos project init --path .  # 이미 .git이 있는 프로젝트에서는 생략 가능
agentos gateway doctor --provider codex-cli
agentos gateway submit --provider codex-cli "저장소의 실패 테스트를 분석해줘"
agentos gateway worker --once
agentos gateway status <RUN_ID>
agentos gateway events <RUN_ID>
```

- `submit` prompt는 하나의 필수 argument로 받으며 help에서 token·password·credential을 prompt에 넣지 말라고 경고한다. 저장된 선호 provider가 있으면 사용하고, 없으면 `--provider` 없이 조용히 `mock`을 선택하지 않고 exit code 2와 provider 선택·로그인 안내를 반환한다. `--cwd` 기본값은 현재 project root다.
- `.git`과 `.agentos`가 모두 없으면 `doctor`는 project marker 미준비를 표시하고 submit은 exit code 2와 `Next: agentos project init --path .`을 출력한다. 기존 Git project는 별도 init 없이 사용할 수 있다.
- submit 성공은 `run_id`, `status=queued`, `next_command=agentos gateway worker --once`를 출력한다. submit 자체는 worker를 암묵적으로 시작하지 않는다.
- 사람용 출력은 한국어 우선이며 오류는 stderr로 보낸다. `--json` 모드의 submit/list/status/cancel/retry/prune/doctor/worker는 stdout에 `schema_version=agentos.gateway/v1`인 단일 JSON object만 출력하고 stderr에 machine payload를 중복 출력하지 않는다.
- `events --json`만 event replay 성격에 맞춰 stdout JSONL을 사용한다. 각 line에는 `schema_version`, `run_id`, `sequence`, `type`, `created_at`이 있고, error에는 `code`, `recovery`가 있다. 모든 JSON 명령은 성공 0, 입력·상태 오류 2, 실행 실패 1의 exit code 계약을 사용한다.
- retry 문법은 `agentos gateway retry <RUN_ID> [PROMPT]`이며 기본 preview, `--yes`에서만 새 attempt를 생성한다. metadata policy는 terminal 시 원문을 지우므로 새 `PROMPT`가 필수이고, 없으면 exit code 2와 `Next: agentos gateway retry <RUN_ID> "<새 prompt>"`를 출력한다. full policy는 `PROMPT` 생략 시 저장된 원문을 재사용하고, 제공하면 새 prompt로 대체한다.
- retry preview는 중복 외부 부작용 가능성, source run, policy, prompt 재사용 여부를 표시한다. 성공 출력은 `source_run_id`, 새 `run_id`, `status=queued`, `next_command=agentos gateway worker --once`를 함께 출력한다.

### 보존과 삭제 계약

- 기본 `record_policy=metadata`는 실행을 위해 queued/running 동안만 prompt 원문을 저장하고 terminal 전이 transaction에서 prompt 원문과 runtime event text를 제거해 hash·길이·provider·상태·시각만 남긴다. `record_policy=full`은 사용자가 명시적으로 선택할 때 prompt와 sanitized event text를 prune 전까지 보존한다. `none`은 restart-safe queue와 양립하지 않아 MVP에서 거부한다.
- `list`와 `status`는 어느 policy에서도 prompt 원문을 출력하지 않는다. `events`는 metadata policy에서는 lifecycle metadata만, full에서는 sanitized runtime event text까지 출력한다.
- `agentos gateway prune --before YYYY-MM-DD`는 기본적으로 삭제 대상 terminal run 수와 범위만 preview한다. 실제 삭제는 `--yes`가 있어야 하며 queued/running run은 항상 보호한다.
- prune은 `secure_delete`가 활성화된 transaction으로 run과 event를 함께 삭제하고 WAL checkpoint/truncate 후 같은 명령 재실행이 안전한 no-op이 되도록 한다. DB 파일 자체 삭제나 자동 보존 기간은 이 계획 범위 밖이다.

## 파일 구조

- 생성: `.agentos/project/reference/decisions/0007-agentos-gateway-core.md` — 0006의 비범위와 Gateway Core의 제한적 예외·소유 경계 결정
- 수정: `.agentos/project/00-project-index.md` — ADR과 user guide 등록
- 수정: `.agentos/project/02-product-scope-and-requirements.md` — Gateway Core requirement/acceptance/non-goal
- 수정: `.agentos/project/03-system-contract.md` — control plane component·data flow·persistence 계약
- 수정: `.agentos/project/04-safety-risk-verification.md` — prompt retention, replay, retry, crash recovery risk/evidence
- 수정: `.agentos/project/05-agent-operating-contract.md` — Gateway run 실행·중단·승인·handoff 경계
- 수정: `.agentos/project/06-decisions-change-log.md` — ADR 0007 등록
- 생성: `agentos/gateway/__init__.py` — Gateway 공개 API
- 생성: `agentos/gateway/types.py` — Gateway run envelope/attempt/claim/lifecycle 상태 전이(기존 runtime 타입 재사용)
- 생성: `agentos/gateway/store.py` — SQLite schema, transaction, run/event CRUD, recovery
- 생성: `agentos/gateway/service.py` — submit/list/status/events/cancel/retry use case
- 생성: `agentos/gateway/worker.py` — 단일 worker claim/execute/recovery loop
- 생성: `agentos/gateway/adapters/__init__.py`, `base.py`, `invocation.py` — runtime adapter protocol과 기존 invocation bridge
- 생성: `agentos/runtime/execution.py` — CLI와 Gateway 공통 project-root·input-hook·provider execution entrypoint
- 수정: `agentos/runtime/protocol.py` — 검증된 execution cwd와 gateway run reference를 기존 RuntimeRequest에 확장
- 수정: `agentos/commands/run.py` — `--once` 경로를 공통 execution entrypoint로 전환
- 생성: `agentos/commands/gateway.py` — 사용자·자동화 CLI와 preview-first prune 표면
- 수정: `agentos/cli.py` — `gateway` Typer group 등록
- 생성: `docs/gateway-core.md` — 직접 CLI와 관리 실행의 차이, 데이터 위치, 복구, 비목표
- 수정: `docs/getting-started.md`, `docs/cli-reference.md` — Gateway Core 가이드 연결
- 생성: `tests/test_gateway_store.py`, `tests/test_gateway_service.py`, `tests/test_gateway_worker.py`, `tests/test_gateway_cli.py`, `tests/test_runtime_execution.py` — focused tests
- 생성: `scripts/verify-gateway-core.sh` — 격리된 `AGENTOS_HOME` 기반 end-to-end·secret scan verifier
- 수정: `scripts/verify-cli-isolated-install.sh` — checkout 밖 설치본의 gateway command registration 검증

## Task 0: 승인된 범위와 구현 전제 고정

**파일:**
- 생성: `.agentos/project/reference/decisions/0007-agentos-gateway-core.md`
- 수정: `.agentos/project/00-project-index.md`, `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`, `05-agent-operating-contract.md`, `06-decisions-change-log.md`

**사용자에게 보이는 마일스톤:** 사용자는 Gateway가 기존 CLI를 대체하지 않으며 로컬 단일 worker 실행 기록만 소유한다는 경계를 프로젝트 문서에서 확인할 수 있다.

- [x] **Step 1: 필수 uv project runtime과 branch preflight를 확인한다.**

  Run: `command -v uv >/dev/null && uv run --offline python - <<'PY'
import sqlite3, sys
from pathlib import Path
import subprocess
import pytest, rich, typer
assert sys.version_info >= (3, 11)
assert sqlite3.sqlite_version
assert Path('pyproject.toml').is_file()
assert subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() != 'main'
print('PASS gateway-uv-runtime-ready')
PY`
  Expected: `PASS gateway-uv-runtime-ready`

- [x] **Step 2: checkout 밖 isolated package 설치를 mutation 전에 확인한다.**

  Python `TemporaryDirectory` 안에만 임시 venv를 생성하고 context 종료 시 자동 정리한다. shell destructive command를 사용하지 않으며 실제 checkout과 사용자 `AGENTOS_HOME`은 수정하지 않는다.

  Run: `uv run --offline python - <<'PY'
import subprocess, tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='agentos-gateway-preflight-') as tmp:
    root = Path(tmp)
    venv = root / 'venv'
    subprocess.run(['uv', 'venv', '--python', '3.11', str(venv)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['uv', 'pip', 'install', '--python', str(venv / 'bin' / 'python'), '.'], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(venv / 'bin' / 'agentos'), '--help'], cwd=root, check=True, stdout=subprocess.DEVNULL)
print('PASS gateway-isolated-install-ready')
PY`
  Expected: `PASS gateway-isolated-install-ready`

- [x] **Step 3: ADR 0007과 root SSOT에 제한된 Gateway Core 결정을 기록한다.**

  ADR은 project owner의 현재 Gateway Core 계획 요청을 승인 근거로 기록하고 아래 metadata를 정확히 가진다: `status: approved`, `owner: project owner`, `approval_basis: user-request-2026-08-01-gateway-core`, `supersedes_scope: 0006:persistent-task-database-exclusion:gateway-run-registry-only`, `preserves: 0006:vendor-execution-plane,0005:direct-cli,0004:credential-boundary`. Gateway DB가 Work Contract나 lifecycle/evidence ledger를 대체하지 않음을 소유권 표와 함께 고정한다.

  Run: `python3 - <<'PY'
from pathlib import Path
checks = {
    '.agentos/project/00-project-index.md': ['0007-agentos-gateway-core'],
    '.agentos/project/02-product-scope-and-requirements.md': ['Gateway Core', '단일 worker'],
    '.agentos/project/03-system-contract.md': ['Gateway Core', 'RuntimeRequest'],
    '.agentos/project/04-safety-risk-verification.md': ['Gateway Core', 'prompt', 'retry'],
    '.agentos/project/05-agent-operating-contract.md': ['Gateway Core', 'worker'],
    '.agentos/project/06-decisions-change-log.md': ['0007-agentos-gateway-core'],
}
for path, terms in checks.items():
    text = Path(path).read_text()
    for term in terms:
        assert term in text, (path, term)
print('PASS gateway-scope-aligned')
PY`
  Expected: `PASS gateway-scope-aligned`

- [x] **Step 4: 기존 ADR과의 충돌 해소를 구조화 metadata로 검증한다.**

  Run: `python3 - <<'PY'
from pathlib import Path
adr = Path('.agentos/project/reference/decisions/0007-agentos-gateway-core.md').read_text().splitlines()
fields = {}
for line in adr:
    if line.startswith('- ') and ': ' in line:
        key, value = line[2:].split(': ', 1)
        fields[key] = value
assert fields['status'] == 'approved'
assert fields['owner'] == 'project owner'
assert fields['approval_basis'] == 'user-request-2026-08-01-gateway-core'
assert fields['supersedes_scope'] == '0006:persistent-task-database-exclusion:gateway-run-registry-only'
assert fields['preserves'] == '0006:vendor-execution-plane,0005:direct-cli,0004:credential-boundary'
index = Path('.agentos/project/00-project-index.md').read_text()
assert '0006 persistent task database 제외 중 Gateway Run registry 범위만 0007이 대체' in index
print('PASS gateway-adr-boundary')
PY`
  Expected: `PASS gateway-adr-boundary`

## Task 1: Run/Event 계약과 embedded 저장소 구현

**파일:**
- 생성: `agentos/gateway/__init__.py`, `agentos/gateway/types.py`, `agentos/gateway/store.py`
- 생성: `tests/test_gateway_store.py`

**사용자에게 보이는 마일스톤:** AgentOS를 다시 실행해도 대기·완료·실패 작업과 순서가 보존된 이벤트를 조회할 수 있다.

- [x] **Step 1: run/request/event 타입과 상태 전이를 정의한다.**

  새 타입은 Gateway run envelope, attempt, claim, Gateway lifecycle event와 상태 전이만 소유한다. 기존 `RuntimeRequest`, `InvocationEvent`, `ProviderCapabilities`를 import해 참조하고 재정의하지 않는다. terminal 상태 불변, retry lineage, optional external session reference, record policy를 명시하며 허용되지 않은 전이는 typed error로 거부한다.

  Run: `uv run --offline pytest tests/test_gateway_store.py -q -k "state_transition or types"`
  Expected: exit code 0이며 상태 전이·terminal 불변·retry lineage 테스트가 모두 PASS

- [x] **Step 2: SQLite schema와 원자적 store 연산을 구현한다.**

  schema version, run/event 테이블, sequence uniqueness, idempotency key uniqueness, transaction 기반 claim을 구현한다. DB·WAL·SHM과 상위 directory는 사용자 전용 권한을 적용하고 credential 필드는 두지 않는다. metadata/full policy별 저장 필드와 terminal prompt purge를 테스트한다. `secure_delete`, WAL checkpoint/truncate를 적용하고 지원하지 않는 최신 schema, DB corruption, symlink gateway directory는 fail closed한다.

  Run: `uv run --offline pytest tests/test_gateway_store.py -q -k "schema or corruption or symlink or claim or idempotency or permissions or record_policy"`
  Expected: exit code 0이며 schema upgrade/downgrade·corruption/symlink fail-closed·중복 claim 방지·DB/WAL/SHM 권한·idempotency·policy별 prompt purge 테스트가 모두 PASS

- [x] **Step 3: 재시작 복구와 event replay를 구현한다.**

  worker는 process lifetime advisory lock을 먼저 획득한다. lock owner만 orphaned `running`을 `interrupted`로 전이하고 audit event를 남기며, event 조회는 run별 sequence 순서를 보장한다. 살아 있는 owner 보호, crash 후 lock 인계도 검증한다.

  Run: `uv run --offline pytest tests/test_gateway_store.py tests/test_gateway_worker.py -q -k "worker_lock or recovery or replay"`
  Expected: exit code 0이며 동시 worker 거부·active owner 보호·crash 후 인계·event ordering 테스트가 모두 PASS

## Task 2: Gateway service·단일 worker·기존 runtime adapter 연결

**파일:**
- 생성: `agentos/gateway/service.py`, `agentos/gateway/worker.py`
- 생성: `agentos/gateway/adapters/__init__.py`, `agentos/gateway/adapters/base.py`, `agentos/gateway/adapters/invocation.py`
- 생성: `agentos/runtime/execution.py`, `tests/test_runtime_execution.py`
- 수정: `agentos/runtime/protocol.py`, `agentos/commands/run.py`
- 생성: `tests/test_gateway_service.py`, `tests/test_gateway_worker.py`

**사용자에게 보이는 마일스톤:** 제출된 작업이 한 번만 claim되어 기존 AgentOS provider를 통해 실행되고, 진행·완료·오류가 같은 run event로 기록된다.

- [x] **Step 1: CLI와 Gateway 공통 실행 entrypoint를 구현한다.**

  `agentos run --once`와 Gateway worker가 함께 사용하는 entrypoint를 추가한다. Gateway 모드는 `.agentos`/`.git` marker root를 요구하고 direct CLI 모드는 기존 markerless cwd 동작을 유지한다. single-thread process-local lock과 scoped `contextlib.chdir`로 provider/subprocess cwd를 설정하고 예외·정상 종료 모두 원래 cwd를 복원한다. `apply_input_hooks`, provider 선택, sanitized invocation을 한 번만 소유하며 critical/non-critical hook failure와 prompt boundary를 보존한다. Gateway는 AgentOS 내부 tool loop를 새로 소유하지 않고 선택된 vendor/provider의 기존 sandbox·approval 계약을 그대로 사용하며 `--yolo`, `--danger-full-access`, 승인 우회 flag를 주입하지 않는다.

  Run: `uv run --offline pytest tests/test_runtime_execution.py tests/test_cli_hooks.py -q`
  Expected: exit code 0이며 CLI/Gateway 공통 hook·marker root·Codex subprocess cwd 상속·정상/예외 cwd 복원·markerless direct CLI 회귀·provider·criticality·secret redaction·vendor approval 비우회 테스트가 모두 PASS

- [x] **Step 2: submit/list/status/events/cancel/retry service를 구현한다.**

  submit은 canonical project root와 idempotency key를 저장하고 중복을 같은 run으로 수렴시킨다. queued cancel만 즉시 terminal 처리하고 running cancel은 상태를 유지한 채 거부한다. retry는 `retry RUN_ID [PROMPT]` preview와 `--yes` 확인 후 failed/interrupted run의 새 attempt를 만들며 succeeded/cancelled retry는 명시적으로 거부한다. metadata policy는 새 prompt를 요구하고 full policy는 생략 시 저장 prompt를 재사용한다. prune은 terminal run만 preview-first로 삭제한다.

  Run: `uv run --offline pytest tests/test_gateway_service.py -q`
  Expected: exit code 0이며 service use case와 실패 복구 테스트가 모두 PASS

- [x] **Step 3: runtime adapter protocol과 기존 invocation bridge를 구현한다.**

  adapter는 기존 provider capability를 읽고 공통 execution entrypoint를 호출한다. 별도 request/event/capability 타입을 만들지 않는다. worker는 저장된 root를 재검증한 뒤 scoped cwd에서 실행하며 `InvocationEvent.to_dict()` 결과를 sanitize 후 Gateway lifecycle event에 연결한다. `done → succeeded`, `error → failed`, terminal event 없는 종료 → `protocol_failure`를 고정한다.

  Run: `uv run --offline pytest tests/test_gateway_worker.py -q -k "adapter or terminal_event or protocol_failure or event_mapping or redaction"`
  Expected: exit code 0이며 done/error/무종료 판정·기존 invocation mapping·capability 재사용·secret redaction 테스트가 모두 PASS

- [x] **Step 4: 단일 worker claim/execute/recovery loop를 구현한다.**

  `--once`는 lock을 획득한 owner가 최대 한 run만 처리하고 종료한다. 동일 DB의 두 번째 worker는 active owner를 보호하며, adapter exception·삭제/교체된 cwd·hook failure는 sanitized failed/interrupted event로 수렴한다. queue claim의 중복 방지와 external execution의 at-least-once 가능성을 테스트에서 구분한다.

  Run: `uv run --offline pytest tests/test_gateway_worker.py -q -k "worker or claim or lock or cwd or failure or cancel or at_least_once"`
  Expected: exit code 0이며 중복 claim 방지·active lock 보호·정상 완료·cwd 재검증·예외·running cancel 거부·외부 재실행 경고 테스트가 모두 PASS

## Task 3: Gateway CLI와 사용자 복구 흐름 추가

**파일:**
- 생성: `agentos/commands/gateway.py`, `tests/test_gateway_cli.py`
- 수정: `agentos/cli.py`

**사용자에게 보이는 마일스톤:** 사용자가 CLI에서 작업 제출, worker 1회 실행, 상태·이벤트 조회, 대기 취소, 실패 재시도를 수행할 수 있다.

- [x] **Step 1: gateway command group과 machine-readable 출력을 추가한다.**

  `doctor`, `submit`, `list`, `status`, `events`, `cancel`, `retry`, `prune`, `worker --once`를 제공한다. single-object JSON과 events JSONL의 schema/exit-code/stderr 계약을 위 `최초 사용과 출력 계약`대로 구현한다.

  Run: `uv run --offline pytest tests/test_gateway_cli.py -q -k "help or json or jsonl or commands or provider_required or project_marker"`
  Expected: exit code 0이며 모든 command help·JSON/JSONL schema·provider/project-marker fail-closed·exit code·stdout 순수성 테스트가 PASS

- [x] **Step 2: 격리된 사용자 홈에서 submit→worker→status 흐름을 검증한다.**

  Run: `uv run --offline pytest tests/test_gateway_cli.py -q -k "submit_worker_status or git_project or initialized_project or persistence or retry"`
  Expected: exit code 0이며 `.git` project와 `agentos project init` project 모두의 최초 사용·새 프로세스 간 DB 재사용·최종 상태·retry lineage 테스트가 PASS

- [x] **Step 3: 직접 vendor CLI와 관리 실행의 차이 및 오류 복구를 출력한다.**

  `doctor`와 command error는 DB 경로, setup/project marker/provider 상태, optional Codex CLI preflight/fallback, worker lock owner 여부, worker 시작 명령, unsupported continuation을 설명한다. marker가 없으면 `agentos project init --path .`을 안내한다. running cancel은 실제 중단이 일어나지 않았음을 밝히고 현재 상태와 `status/events` 명령을 출력한다. retry는 외부 부작용 중복 경고와 원본/새 run ID를 모두 표시하며 credential·prompt 원문은 출력하지 않는다.

  Run: `uv run --offline pytest tests/test_gateway_cli.py -q -k "doctor or recovery or cancel or retry or metadata_prompt_required or full_prompt_reuse or no_prompt_leak"`
  Expected: exit code 0이며 최초 사용·취소 거부·retry preview/확인·metadata prompt 복구 명령·full prompt 재사용·새 run 식별·민감 입력 비노출 테스트가 PASS

- [x] **Step 4: preview-first 보존 데이터 삭제 흐름을 구현한다.**

  `prune --before`는 terminal run과 event 삭제 대상을 preview하고 `--yes`에서만 secure-delete transaction으로 삭제한 뒤 WAL checkpoint/truncate를 수행한다. queued/running 보호, 같은 명령 재실행 no-op, JSON 결과의 `matched/deleted/protected` 필드를 검증한다.

  Run: `uv run --offline pytest tests/test_gateway_store.py tests/test_gateway_cli.py -q -k "prune or retention or metadata_terminal_purge or full_secure_delete"`
  Expected: exit code 0이며 metadata terminal purge·full 저장/preview/secure-delete·활성 run 보호·재실행 안전성 테스트가 PASS

## Task 4: 사용자 문서·운영 검증·회귀 닫기

**파일:**
- 생성: `docs/gateway-core.md`, `scripts/verify-gateway-core.sh`
- 수정: `.agentos/project/00-project-index.md`, `docs/getting-started.md`, `docs/cli-reference.md`, `scripts/verify-cli-isolated-install.sh`
- 수정: Task 1~3의 테스트 파일

**사용자에게 보이는 마일스톤:** 사용자가 Gateway를 언제 사용하고 기존 Codex CLI를 언제 직접 사용할지, 데이터가 어디에 남고 실패 시 어떻게 복구할지 문서와 검증 명령으로 확인할 수 있다.

- [x] **Step 1: 사용자 가이드와 다음 단계 경계를 작성한다.**

  `docs/gateway-core.md`를 한국어 우선으로 작성한다. 필수 섹션은 전제조건(`agentos setup`, 비-Git project의 `agentos project init`, provider status/login), 직접 Codex/Gateway 비교, 복사 가능한 `doctor → submit → worker --once → status/events` quickstart, metadata/full별 `retry RUN_ID [PROMPT]` preview/`--yes`, 취소, 보존·preview-first 삭제, 오류 복구, 완료 신호, 후속 Slack/GitHub/app-server 범위다. `docs/getting-started.md`와 `docs/cli-reference.md`에서 이 가이드를 연결한다.

  Run: `grep -q "agentos gateway submit" docs/gateway-core.md && grep -q "agentos gateway worker --once" docs/gateway-core.md && grep -q "gateway retry" docs/gateway-core.md && grep -q "AGENTOS_HOME" docs/gateway-core.md && grep -q "prune --before" docs/gateway-core.md && grep -q "gateway-core.md" docs/getting-started.md && grep -q "gateway-core.md" docs/cli-reference.md && echo "PASS gateway-guide"`
  Expected: `PASS gateway-guide`

- [x] **Step 2: 격리 end-to-end와 secret scan verifier를 작성한다.**

  verifier는 임시 `AGENTOS_HOME`과 서로 다른 submit/worker cwd에서 두 흐름을 독립 실행한다. (1) 기본 metadata-policy sentinel은 terminal 전이 직후 DB와 event payload에서 원문 부재를 확인한다. (2) `--record-policy full` sentinel은 terminal 후 DB에 저장됐음을 먼저 확인하고, `prune --before` preview 뒤에도 존재함을 확인한 다음 `prune --before ... --yes` 후 DB/WAL/SHM 전체에서 부재를 확인한다. 두 흐름 모두 status/list/doctor/stdout/stderr/verifier artifact에 원문이 노출되지 않는지 검사한다. 임시 경로만 정리하며 실제 사용자 DB는 건드리지 않는다.

  Run: `bash scripts/verify-gateway-core.sh`
  Expected: `PASS agentos-gateway-core`

- [x] **Step 3: focused·기존 runtime/CLI 회귀·manifest 검증을 실행한다.**

  Run: `uv run --offline pytest tests/test_gateway_store.py tests/test_gateway_service.py tests/test_gateway_worker.py tests/test_gateway_cli.py tests/test_runtime_execution.py tests/test_runtime_protocol.py tests/test_cli_contract.py tests/test_cli_hooks.py tests/test_codex_provider.py -q && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: exit code 0이며 모든 pytest와 manifest check가 PASS

- [x] **Step 4: 엔진 반영과 설치 CLI 도움말을 검증한다.**

  Gateway Core는 장기 실행 엔진 계약을 추가하므로 기존 isolated-install verifier의 임시 가상환경 설치 흐름에 새 command 확인을 추가하고, checkout 밖에서 registration이 반영되는지 확인한다. Task 0의 required network preflight가 실패하면 구현 전에 `NEEDS_CONTEXT`로 중단한다. 별도 daemon restart는 없으며 새 CLI 프로세스가 갱신된 코드를 로드한다.

  Run: `bash scripts/verify-cli-isolated-install.sh`
  Expected: `PASS agentos-cli-isolated-install`이며 설치된 `agentos gateway --help`에 `submit`, `worker`, `status`, `events`, `retry`, `prune`가 포함됨

## 검증 매트릭스

| 요구사항 | 자동 검증 | Expected | 증거 surface |
|---|---|---|---|
| 상태 무결성·원자적 claim | `uv run --offline pytest tests/test_gateway_store.py -q` | exit 0 | focused pytest output |
| service·worker·adapter | `uv run --offline pytest tests/test_gateway_service.py tests/test_gateway_worker.py -q` | exit 0 | focused pytest output |
| 사용자 CLI·복구 문구 | `uv run --offline pytest tests/test_gateway_cli.py -q` | exit 0 | CLI focused output |
| end-to-end·secret 경계 | `bash scripts/verify-gateway-core.sh` | `PASS agentos-gateway-core` | verifier stdout |
| 기존 runtime/CLI/hook/Codex compatibility | `uv run --offline pytest tests/test_runtime_execution.py tests/test_runtime_protocol.py tests/test_cli_contract.py tests/test_cli_hooks.py tests/test_codex_provider.py -q` | exit 0 | regression pytest output |
| 문서·ADR 정합성 | Task 0/4의 `grep`·Python 검증 | `PASS gateway-scope-aligned`, `PASS gateway-guide` | repository docs |
| 설치본 command registration | `bash scripts/verify-cli-isolated-install.sh` | `PASS agentos-cli-isolated-install` | isolated venv output |
| manifest 무결성 | `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` | PASS | manifest checker output |

## 실행·복구·롤백

- 구현 순서: Task 0 → Task 1 → Task 2 → Task 3 → Task 4. Task 0 문서 결정 검증 전 source implementation을 시작하지 않는다.
- 실패 시: schema migration 또는 claim 테스트 실패 시 worker/CLI 연결을 중단하고 store contract를 먼저 수정한다.
- 데이터 복구: 초기 schema는 additive migration만 허용하고 newer unsupported schema·corruption·symlink 경로는 fail closed한다. destructive migration은 이 계획 범위 밖이며 별도 승인과 backup/restore 검증이 필요하다. 사용자 데이터 삭제는 오직 preview 후 `prune --yes`로 terminal run에 한정한다.
- 코드 롤백: 새 `agentos/gateway/`와 CLI registration을 일반 Git revert로 되돌릴 수 있다. 사용자 DB를 자동 삭제하지 않으며 downgrade incompatibility는 doctor가 표시한다.
- runtime 반영: daemon이 없으므로 새 프로세스 실행으로 반영한다. 설치된 package 검증이 필요하면 기존 isolated install verifier 패턴을 따른다.
- HISTORY tagging: canonical `HISTORY.md`가 확인되면 구현/검증 checkpoint에 `plan=.agentos/project/exec-plans/active/2026-08-01-gateway-core.md`를 포함하고 closeout에는 `artifact=docs/gateway-core.md`를 권장한다. generic harness health 기록은 over-tagging 방지를 위해 예외로 둘 수 있다.

## 단순성 게이트

- 원래 요청에 없던 외부 surface, daemon, multi-worker, scheduler, provider별 protocol 구현은 추가하지 않는다.
- SQLite는 restart-safe queue와 atomic claim을 위한 최소 내장 저장소이며 외부 DB나 broker보다 작은 경로다.
- 기존 `RuntimeRequest`, `InvocationEvent`, provider registry, input hook을 공통 execution entrypoint에서 재사용하여 Gateway 내부에 중복 LLM runtime·event·capability 계층을 만들지 않는다.
- app-server 장기 세션, Slack/GitHub adapter는 Gateway Core 검증 이후 별도 계획으로만 확장한다.

## 리뷰 반영 이력

- [Gate 2 1차 usability-reviewer] 최초 실행 순서·provider 기본값 불명확 → fail-closed provider 선택과 복사 가능한 `doctor → submit → worker → status/events` 계약을 추가했다.
- [Gate 2 1차 usability-reviewer] running cancel 의미 모순 → MVP에서 running cancel을 상태 변경 없이 거부하고 queued cancel만 허용하도록 고정했다.
- [Gate 2 1차 usability-reviewer] prompt/event 보존·삭제 경로 누락 → 무기한 사용자 소유 보존과 preview-first `prune --before ... --yes`, 활성 run 보호를 추가했다.
- [Gate 2 1차 usability-reviewer] JSON 오류 출력 모호 → 단일-object JSON, events JSONL, schema/exit-code/stdout 계약을 명시했다.
- [Gate 2 1차 usability-reviewer] 한국어 최초 사용 문서 검증 부족 → gateway guide 필수 섹션과 getting-started/CLI reference 연결을 추가했다.
- [Gate 2 1차 principle-auditor] `invoke_once()` 직접 호출이 input hook을 우회 → CLI/Gateway 공통 hook-aware execution entrypoint와 hook 회귀를 추가했다.
- [Gate 2 1차 principle-auditor] execution cwd와 trust 경계 누락 → canonical project root 저장·재검증·symlink/deleted root fail-closed 계약을 추가했다.
- [Gate 2 1차 plan-reviewer/principle-auditor] recovery가 active worker를 오판할 위험 → process advisory lock owner만 claim/recovery하도록 변경했다.
- [Gate 2 1차 principle-auditor] 기존 request/event/session/ledger 중복 위험 → 계층별 SSOT 소유권 표와 단방향 ID 참조를 추가했다.
- [Gate 2 1차 plan-reviewer/principle-auditor] ADR 0006 범위 변경이 불명확 → persistent task DB 제외를 Gateway Run registry에 한해 제한적으로 supersede한다고 고정했다.
- [Gate 2 1차 plan-reviewer/principle-auditor] record policy·prompt 삭제·DB 복구 증거 부족 → metadata/full 수명주기, corruption/symlink fail-closed, DB/WAL/SHM 권한·prune sentinel 검증을 추가했다.
- [Gate 2 1차 plan-reviewer] 종료 event 판정 누락 → done/error/terminal event 없음의 run 상태 계약을 추가했다.
- [Gate 2 1차 plan-reviewer] pytest/설치본 검증 의존성 누락 → Python project runtime dependency gate와 isolated-install 검증을 추가하고 `rg` 계획 명령을 portable `grep`/Python으로 교체했다.
- [Gate 2 1차 plan-reviewer] `필요 시 README.md` 미결정 → README 변경을 제외하고 getting-started/CLI reference 수정으로 고정했다.
- [Gate 2 2차 usability-reviewer] metadata terminal prompt 삭제 후 retry 문법 누락 → `retry RUN_ID [PROMPT]` preview/`--yes`, metadata prompt 필수 복구 명령, full prompt 재사용 규칙과 테스트를 추가했다.
- [Gate 2 2차 plan-reviewer] 실제 Codex CLI dependency gate 누락 → optional live-runtime preflight, mock fallback, doctor fail-closed 계약을 추가했다.
- [Gate 2 2차 plan-reviewer] offline isolated install cache를 마지막에야 검증 → Task 0에서 임시 venv offline install·checkout 밖 help preflight를 추가했다.
- [Gate 2 2차 plan-reviewer] cwd가 provider subprocess로 전달되는 경로 불명확 → single-thread scoped `contextlib.chdir`, 원위치 복원, Gateway marker/direct CLI markerless 경계를 고정했다.
- [Gate 2 2차 plan-reviewer] ADR 충돌 검증이 키워드 기반 → status/owner/approval_basis/supersedes_scope/preserves 고정 metadata와 정확값 검증으로 교체했다.
- [Gate 2 3차 fresh preflight] uv offline cache에 Textual이 없어 isolated install FAIL → isolated package install network를 required dependency로 선언하고 Task 0 실제 임시 venv 설치 preflight로 교체했다.
- [Gate 2 3차 fresh preflight] 시스템 Python 3.9로 임시 venv 설치 FAIL → `uv venv --python 3.11`로 interpreter 요구사항을 고정했다.
- [Gate 2 3차 usability-reviewer] 비-Git directory에서 setup만으로 marker가 생기지 않음 → `agentos project init --path .` quickstart, doctor/submit 복구, Git/init project 양쪽 테스트를 추가했다.
- [Gate 2 4차 plan-reviewer] mock fallback이 `authenticated=true`를 잘못 기대 → 실제 mock 계약(provider/mode, authenticated=false, persistent=false) 검증으로 수정했다.
- [Gate 2 4차 principle-auditor] secure prune verifier가 기본 metadata만으로 통과 가능 → metadata terminal purge와 full sentinel 저장·preview 유지·`--yes` 후 DB/WAL/SHM 부재를 독립 검증하도록 고정했다.
- [Gate 2 최종] plan-reviewer, principle-auditor, usability-reviewer가 동일 plan hash에 PASS했으며, 최종 상태 문구를 반영한 hash로 artifact와 signed review를 재발급한다.

## 구현 결과

- `agentos/gateway/` 패키지 추가: SQLite 기반 run registry, Gateway service, common runtime entrypoint, runtime adapter, 단일 worker lock/execute/recovery loop.
- `agentos gateway` CLI group 추가: `doctor`, `submit`, `list`, `status`, `events`, `cancel`, `retry`, `prune`, `worker --once`.
- ADR 0007과 root project docs에 Gateway Core의 제한된 local run registry 범위, direct vendor CLI 보존, retry/prune/secret 경계를 반영.
- `docs/gateway-core.md`, `docs/getting-started.md`, `docs/cli-reference.md`에 사용자 실행 흐름과 복구 경로를 연결.
- `tests/test_gateway_store.py`, `tests/test_gateway_service.py`, `tests/test_gateway_worker.py`, `tests/test_gateway_cli.py`, `tests/test_runtime_execution.py`, `scripts/verify-gateway-core.sh` 추가.

## 사용 방법

```bash
agentos project init --path .
agentos gateway doctor --provider mock
agentos gateway submit --provider mock "summarize this project"
agentos gateway worker --once
agentos gateway status RUN_ID
agentos gateway events RUN_ID
```

실패 또는 중단된 run은 `agentos gateway retry RUN_ID "replacement prompt" --yes`로 새 attempt를 만들고, terminal run 보존 데이터는 `agentos gateway prune --before TIMESTAMP` preview 후 `--yes`로 삭제한다. 자세한 운영 경계는 `docs/gateway-core.md`를 본다.

## 완료 증거

- `command -v uv ...` preflight → `PASS gateway-uv-runtime-ready`
- isolated package preflight → `PASS gateway-isolated-install-ready`
- Task 0 SSOT alignment → `PASS gateway-scope-aligned`, `PASS gateway-adr-boundary`
- planned focused selectors: Task 1~3 pytest selector commands all exit 0
- `grep ... docs/gateway-core.md ...` → `PASS gateway-guide`
- `uv run --offline pytest tests/test_gateway_store.py tests/test_gateway_service.py tests/test_gateway_worker.py tests/test_gateway_cli.py tests/test_runtime_execution.py tests/test_runtime_protocol.py tests/test_cli_contract.py tests/test_cli_hooks.py tests/test_codex_provider.py -q` → `65 passed`
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → `🏆 [PASS] 하네스 무결성 확인 완료.`
- `bash scripts/verify-gateway-core.sh` → `11 passed`, `PASS agentos-gateway-core`
- `bash scripts/verify-cli-isolated-install.sh` → `PASS installed-tui-smoke`, `PASS agentos-cli-isolated-install`

## 아카이브 결정

이 계획은 구현과 fresh verification이 끝났지만, 사용자가 명시적으로 archive를 요청하기 전까지 `.agentos/project/exec-plans/active/`에 유지한다.
