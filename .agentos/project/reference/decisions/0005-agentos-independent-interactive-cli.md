# 0005 - AgentOS 독립 대화형 CLI와 Harness 입력 계약

- Expansion Trigger: 기존 최소 Typer 명령군은 존재하지만 source checkout/CWD 의존과 대화형 입력·hook 계약이 없어 독립적인 AgentOS 사용자 인터페이스가 아니다.
- parent root doc: `01-project-charter.md`, `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`, `05-agent-operating-contract.md`, `06-decisions-change-log.md`
- reason for creation: 취소된 REPL 중단 결정을 대체하고, 대화형 CLI와 hook 기반 입력 관리의 제품·보안 경계를 장기적으로 기록한다.
- owner: project owner
- freshness rule: CLI command contract, hook lifecycle, session persistence, provider boundary, or user-data policy가 바뀌면 갱신한다.
- status: 현재
- source evidence: 사용자(PO) 2026-07-19 결정; `references/pi`의 CLI/TUI·mode 분리; `references/hermes-agent`의 command family·diagnostic pattern; 현재 `agentos/cli.py`와 `agentos/commands/`.
- links back to: `0002-agentos-repl-deprecation.md`, `0004-agentos-llm-credential-strategy.md`, `06-decisions-change-log.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, reviewer authority, or the credential safety boundary in `0004`.

## 결정

AgentOS는 Python/Typer 기반의 자체 독립 CLI를 제품의 주 사용자 인터페이스로 발전시킨다. 기본 `agentos`는 실제 TTY에서 대화형 세션을 시작하고, 명시적 command는 설치·진단·LLM 상태·단발 실행·harness 실행을 제공한다. 비대화형 자동화에는 안정적인 JSONL 출력과 종료 코드를 제공한다.

입력은 `input_received -> input_normalized -> pre_turn -> turn_started -> turn_event -> post_turn -> session_closed` lifecycle로 다루며, hook은 명시적으로 등록된 AgentOS hook만 실행한다. hook은 입력 정규화, 컨텍스트 보강, 안전 검사, 관측값 기록을 할 수 있으나, 사용자의 원문 입력·provider secret·환경 전체를 무단 저장하거나 stdout JSONL 계약을 오염시킬 수 없다.

## 범위와 비범위

- 포함: TTY 대화형 CLI, 단발 prompt 실행, session/history 관리, command 도움말, setup/doctor, 사용자 설정의 명시적 hook, 구조화 이벤트, 입력 편집과 중단/복구 UX.
- 제외: pi의 TypeScript/Bun/TUI 런타임 이식, Hermes gateway·메신저·백업 명령군, arbitrary third-party hook code 실행, packaged `.agents`/harness asset 복제, AgentOS-owned OAuth/API-key 저장, raw secret/provider stderr 전달.
- hook 성능 판단: hook은 turn latency, cancellation, input transformation, error recovery의 측정 가능한 개선만 주장한다. 모델 품질 향상은 비교 가능한 eval 없이 주장하지 않는다.

## 설계 원칙

1. CLI shell은 입력/렌더링/명령 해석을 소유하고, LLM provider와 harness engine은 adapter로 분리한다.
2. 대화형 text 화면과 기계용 JSONL은 같은 typed event stream을 소비하되, JSONL stdout에는 이벤트만 쓰고 인간용 진단은 stderr로 보낸다.
3. hook은 allowlist, 순서, timeout, failure mode, redaction, opt-in scope를 가진다. 실패한 non-critical hook은 경고 후 turn을 계속하고, critical safety hook은 실행 전 중단하며 복구 명령을 제시한다.
4. session 데이터와 hook 관측값은 사용자 소유 `AGENTOS_HOME` 아래에만 저장하며, project-local 규칙은 신뢰 승인 없이는 실행하지 않는다. Session은 자동 삭제하지 않으며 `delete`/`prune`은 preview와 명시적 확인을 요구한다.
5. 현재 Codex CLI delegation의 account-login·secret redaction 경계는 그대로 유지한다.

## 결과와 후속 조건

후속 실행 계획은 command grammar, event schema, hook API, session format, migration/rollback, automated tests, pseudo-TTY 사용자 검증을 파일 단위로 정하고 Gate 2를 통과해야 한다. 실제 구현은 그 계획의 fresh review 뒤에만 시작한다.
