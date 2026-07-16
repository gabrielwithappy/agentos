# 시스템 계약

목적: 시스템 형태, 인터페이스, 데이터 흐름, 의존성 경계, 운영 가정을 정의한다.
주요 독자: architect, 구현 에이전트, 리뷰어/운영자, 후속 핸드오프 에이전트.
가능하게 하는 결정: architecture fit, interface ownership, dependency 준비 상태, data boundary, rollback path.
에이전트 핵심 정보: component map, interface contracts, data and prompt boundary, dependency preflights, operational notes.
현재 증거 / 최신성: update before implementation when architecture, dependency, interface behavior, or runtime assumptions change.

## 시스템 개요

- system goal:
- components:
- runtime shape:
- data flow:
- persistence:
- deployment/operation:

## 아키텍처 요약

endpoint-level 또는 file-level implementation detail 전에 이 문서를 채운다.

### Architecture characteristics

| Characteristic | Priority | Tradeoff | Verification signal |
|---|---|---|---|
|  |  |  |  |

### Architecture style

- selected style:
- why it fits:
- intentionally avoids:
- evidence:

### Logical components

| Component | Responsibility | Owned data | Inbound interfaces | Outbound interfaces | Dependencies | Failure mode | Owner |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

### Architecture decisions

| Decision | Context | Options considered | Decision | Consequences | Owner | Evidence |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 인터페이스 계약

| Interface | Owner | Input | Output | Failure behavior | Traceability |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 의존성

| dependency | purpose | credential/preflight | fallback | owner |
|---|---|---|---|---|
|  |  |  |  |  |

## 데이터와 프롬프트 경계

- trusted input:
- untrusted input:
- secret source:
- redaction rule:
- prompt boundary:
- prompt injection handling:

## 되돌리기 어려운 작업과 복구

- destructive command:
- migration:
- external side effect:
- backup/recovery:
- rollback owner:

## 지원 문서

endpoint-level, file-level, environment-specific detail이 이 root contract를 너무 길게 만들 때만 contract, API example, schema, vendor note, implementation design, operation supporting doc을 만든다. `00-project-index.md`에 등록한다.

- Use `reference/implementation/` for public API, internal service contract, schema, data dictionary, queue/event contract, external vendor dependency, or CLI command contract.
- Use `reference/implementation/` for module decomposition, migration plan, data flow, implementation alternatives, or cross-cutting technical design.
- Use `reference/decisions/` when detailed ADR-style records would make this root contract too long.

root docs는 architecture intent와 decision boundary를 담는다. 상세 API와 implementation example은 supporting doc에 둔다.
