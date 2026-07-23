# pi TUI to AgentOS TUI 클로닝 로드맵

- Expansion Trigger: Phase 5 이후 pi TUI 클로닝을 장기 로드맵과 첫 구현 묶음으로 계속하라는 요청
- parent root doc: `03-system-contract.md`
- reason for creation: pi의 기능을 구현 가능성·선행 조건·AgentOS 계약 영향으로 구분해 이후 Phase가 같은 조사를 반복하지 않게 한다.
- owner: AgentOS TUI 구현 파트
- freshness rule: 각 TUI 클로닝 Phase closeout 또는 pi reference revision 변경 시 갱신
- status: 현재 (Current) — 2026-07-23
- source evidence: pi revision `3da591ab`, `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/`, `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/coding-agent/src/modes/interactive/`
- links back to 요구사항, decisions, risks, or verification: `03-system-contract.md`의 AgentOS TUI UX Architecture; `04-safety-risk-verification.md`의 TUI rendering/dependency regression; `.agents/traces/research/2026-07-23-tui-pi-clone-phase6-pi-tui-input-architecture.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, or reviewer authority

## 사용자 목표

AgentOS TUI를 pi의 UX 패턴과 동등한 방향으로 확장하되, TypeScript 런타임을 복사하지 않고 Python/Textual·기존 secret redaction·no-TTY JSONL·세션 JSONL 호환성을 유지한다.

## 구현 로드맵

| Phase | 사용자 결과 | 범위 | 완료 기준 |
|---|---|---|---|
| 5 | TUI 안에서 훅을 확인하고 켜고 끈다 | `/settings` 훅 토글 | Phase 5 계획의 Gate 2 및 구현 검증 |
| 6 | 명령 입력에서 일관된 키 동작과 선택 가능한 자동완성을 사용한다 | capability registry, keybinding action registry, slash/argument completion | focused Pilot tests, public suite, pi source mapping |
| 7 | 파일 관련 입력을 실제 의미와 함께 제안·전달한다 | `@` completion과 attachment contract | multimodal/provider contract이 승인된 별도 계획 |
| 8 | 파일 변경을 안전하게 읽을 수 있다 | typed file-edit event와 diff renderer | file-edit tool contract + secret redaction suite |
| 9 | 긴 대화와 terminal image 환경을 명확히 다룬다 | compaction indicator, image protocol | backend/protocol preflight가 있는 별도 계획 |

## Phase 6 범위

- `TuiCapability` registry로 pi 기능군의 구현·보류 상태, ownership, 근거를 코드와 `/capabilities` 명령에서 같은 데이터로 제공한다.
- `TuiKeybinding` registry로 Composer, transcript, overlay action과 기본 키를 선언하고 충돌을 테스트한다. 키 사용자 설정의 저장·마이그레이션은 포함하지 않는다.
- completion protocol로 slash command와 안전한 argument 후보(theme/provider/session)를 제공한다. `@` 파일 첨부·파일 내용 자동 주입은 포함하지 않는다.
- 기존 Tab 규칙을 보존한다. slash 입력에서는 completion, 일반 입력에서는 Phase 4의 transcript focus cycle이 계속 동작해야 한다.

## 안전 경계

- pi는 read-only 설계 증거다. AgentOS는 pi의 소스·설정·의존성을 직접 복사하거나 실행하지 않는다.
- provider credentials, raw provider stderr, 환경 변수, secret은 completion/capability UI·테스트 출력에 나타나면 안 된다.
- Phase 6은 세션 JSONL 포맷, provider transport, hook configuration schema, Phase 5 `/settings`의 ownership을 바꾸지 않는다.
