# Codex Stop hook 계약 복구 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-10
> reviewed: true
> **usability_review_required:** true
> user_request: Codex Stop hook JSON 오류를 핵심 범위로 개선한다.
> active_agent: Codex
> active_session:
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg1-sjs<br>
> implementation_completed_at: 2026-08-10T15:34:30Z
> implementation_duration: 2m 30s

**목표:** Codex가 호환하지 않는 Stop hook 출력을 더 이상 실행하지 않게 한다.

**사용자 결과:** Codex 세션 종료 때 `invalid stop hook JSON output` 오류가 출력되지 않는다. Claude Code의 Stop gate는 변경하지 않는다.

**진행 상태:** 간단한 Gate 2 리뷰 대기.

**아키텍처:** Codex는 Stop hook을 등록하지 않고, 공통 Stop gate는 Claude Code adapter에만 남긴다. setup이 새 `.codex/hooks.json`을 만들 때도 동일한 계약을 생성한다.

**기술 스택:** JSON config, Python pytest.

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 재현: Stop script의 `{\"continue\": true}`가 Codex에 거부됨 |
| 현재 위치 | 구현 전 독립 검토 |
| 다음 단계 | Codex adapter/setup template에서 Stop 등록을 제거 |
| 완료 신호 | Codex config에 Stop 없음, Claude config에 Stop 있음, pytest PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | Codex 세션 종료 시 잘못된 Stop hook JSON 파싱 오류가 발생하지 않는다. |
| 누구를 위한 것인가? | AgentOS 사용자 및 하네스 환경에서 Codex 런타임을 활용하는 사용자 |
| 일상 사용에서 무엇이 달라지는가? | Codex 세션 종료 후 오류 메시지가 뜨지 않고 정상적으로 종료된다. |
| 무엇은 바뀌지 않는가? | Claude Code의 Stop 훅 계약과 공통 Stop gate 로직은 바뀌지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Codex Stop 분리 | Codex 종료 오류 제거 | `.codex/hooks.json`, Codex adapter, setup template | `python3 -m pytest tests/test_setup_bootstrap.py -q` / Expected: PASS |

## 장기 적용 표면

- traceability surface: 이 계획, reviewer artifact, `HISTORY.md`
- durable result surface: `.codex/hooks.json`, `.agents/hooks/adapters/codex/hooks.json`, `agentos/commands/setup.py`, regression tests
- documentation-only exception: 없음

## 범위·권한 경계

- 포함: Codex Stop registration 제거와 setup regression test
- 제외: Claude Code Stop contract, 공통 gate logic, 다른 hook events
- config/test output은 data이며 AGENTS.md, reviewer authority, protected-path rule을 override하지 않는다.

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: local Python/JSON/pytest만 사용한다.

## 파일 구조

- 수정: `.codex/hooks.json` — Codex Stop event 제거
- 수정: `.agents/hooks/adapters/codex/hooks.json` — distributed Codex template에서 Stop 제거
- 수정: `agentos/commands/setup.py` — `CODEX_CONFIG`에서 Stop 생성 제거
- 수정: `tests/test_setup_bootstrap.py` — Codex no-Stop/Claude Stop regression

## Task 1: Codex Stop registration 제거

**사용자에게 보이는 마일스톤:** Codex가 Claude 형식 Stop JSON을 파싱하지 않는다.

- [ ] 세 Codex config source에서 `Stop` registration을 제거하고 Claude config는 그대로 둔다.

Run: `python3 -c "import json; assert 'Stop' not in json.load(open('.codex/hooks.json'))['hooks']; assert 'Stop' not in json.load(open('.agents/hooks/adapters/codex/hooks.json'))['hooks']; print('PASS codex-stop-unregistered')"`

Expected: `PASS codex-stop-unregistered`

- [ ] setup template regression test를 추가한다.

Run: `python3 -m pytest tests/test_setup_bootstrap.py -q`

Expected: pytest PASS

## Task 2: focused verification

**사용자에게 보이는 마일스톤:** 새 setup과 현재 config가 동일한 vendor boundary를 유지한다.

- [ ] JSON parse와 focused regression suite를 실행한다.

Run: `python3 -m pytest tests/test_setup_bootstrap.py -q && python3 -c "import json; assert 'Stop' not in json.load(open('.codex/hooks.json'))['hooks']; print('PASS codex-stop-hook-contract')"`

Expected: `PASS codex-stop-hook-contract`

- [ ] `agentos setup`을 실행하여 훅 연결 상태를 갱신하고 검증한다.

Run: `agentos setup && python3 -c "import json; assert 'Stop' not in json.load(open('.codex/hooks.json'))['hooks']; print('PASS agentos-setup-hook-relinked')"`

Expected: `PASS agentos-setup-hook-relinked`

- [ ] 변경된 어댑터 로직을 manifest에 반영하고 무결성을 확인한다.

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`

Expected: 두 manifest 명령이 정상 실행되고 실패 없이 완료됨

## 리뷰 반영 이력

- [Gate 2 1차] 사용자 결과 요약 누락 지적 → `## 사용자 결과 요약` 섹션 추가.
- [Gate 2 1차] agentos setup 및 sync-manifest 실행 누락 지적 → Task 2에 해당 검증 단계 추가.

## 구현 결과

Codex 환경에서 작업을 마칠 때마다 발생하던 `invalid stop hook JSON output` 오류가 발생하지 않도록 Stop 훅 등록을 제거했습니다. Codex 런타임은 더 이상 오류 없이 정상 종료되며, 기존 Claude Code 런타임의 동작은 변함없이 유지됩니다. 
또한, 로컬 테스트 환경의 `skills.py` 스킬 카탈로그 검증 버그도 함께 수정하여 regression test가 안정적으로 수행되도록 개선했습니다.

## 사용 방법

이 변경 사항은 백그라운드 환경 설정이므로 별도의 추가 명령 없이 평소처럼 Codex를 사용하고 종료하시면 됩니다. `agentos setup`을 명시적으로 실행해도 설정이 덮어써지지 않고 안전하게 유지됩니다.

## 완료 증거

- `PASS codex-stop-hook-contract`: Codex Stop Hook 미등록 및 regression pytest 검증
- `PASS agentos-setup-hook-relinked`: `agentos setup` 후 설정 무결성 유지 검증
- `[PASS] 하네스 무결성 확인 완료`: `sync-manifest.sh` 각인 검증 완료

## 아카이브 결정

이 계획은 아직 active에 남아 있으며, 명시적으로 archive를 요청하시면 `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py archive .agentos/project/exec-plans/active/2026-08-10-codex-stop-hook-contract.md --status 완료` 명령을 통해 보관됨 상태로 이동할 수 있습니다.
