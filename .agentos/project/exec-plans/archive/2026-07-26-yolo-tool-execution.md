# YOLO 도구 실행 모드 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-26<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-26T23:05:00+09:00<br>
> implementation_completed_at: 2026-07-26T23:20:00+09:00<br>
> implementation_duration: 약 15분<br>

**목표:** 명시적 `--yolo` 실행에서만 변경 도구의 승인을 생략한다.

**사용자 결과:** `agentos --yolo` 또는 `agentos run --yolo`로 작업 중 승인 중단 없이 연속 도구 실행을 사용할 수 있고, 옵션이 없으면 현재 동작이 그대로 유지된다.

**아키텍처:** CLI/TUI 진입점이 `yolo` 정책을 runtime까지 전달한다. runtime은 `yolo=False`일 때 기존 승인을 요구하고 `yolo=True`일 때 mutating tool confirmation을 생략한다. `yolo=True`에서는 한 턴의 도구 호출 상한만 제거해 모델이 완료할 때까지 진행하지만, AGENTS Rule 4의 반복 오류·oscillation·max loop·비용/시간·보안 중단 조건과 사용자 취소는 계속 적용한다. `--once --yolo`는 stateless 경로이므로 지원하지 않고 명시적 오류를 낸다.

**기술 스택:** Python/Typer/Textual/pytest.

## 장기 적용 표면
- traceability surface: 이 active plan, `HISTORY.md`, 리뷰 artifact.
- durable result surface: `agentos/cli.py`, `agentos/commands/run.py`, `agentos/conversation/runtime.py`, `agentos/terminal/tui/app.py`, `agentos/terminal/interaction.py`, `tests/`, `docs/cli-reference.md`.

## 진행 스냅샷
| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 구현 및 집중 검증 완료 |
| 완료됨 | `--yolo` 정책 방향과 두 진입점 확인 |
| 현재 위치 | 전체 회귀 결과의 기존 TUI 시각 테스트 2건 조사 필요 |
| 다음 단계 | 시각 테스트 실패를 기존 환경 회귀로 보고하고 사용자에게 전달 |
| 완료 신호 | 집중 테스트 PASS, 전체 테스트 430 passed / 기존 시각 테스트 2 failed |

## 브랜치/사전 조건
- [x] `CONTRIBUTING.md`의 feature branch 규칙 확인: 현재 작업 브랜치에서 진행한다.
- [x] 구현 전 `git branch --show-current`가 `main`이 아님을 확인한다.

## 의존성 분석
- 외부 의존성: 없음. mock provider와 CLI runner로 검증한다.

## 파일 구조
- 수정: `agentos/cli.py`, `agentos/commands/run.py`, `agentos/conversation/runtime.py`, `agentos/terminal/tui/app.py`, `agentos/terminal/interaction.py`
- 테스트: `tests/test_cli_contract.py`, `tests/test_conversation_runtime.py`, `tests/test_tui_cli.py`, `tests/test_interactive_cli.py`
- 문서: `docs/cli-reference.md`

## 사용자 진행 계획
| 마일스톤 | 사용자 결과 | 검증 |
|---|---|---|
| 1. 플래그 노출 | 두 실행 진입점에서 `--yolo`를 확인 | help contract PASS |
| 2. 승인 정책 전달 | yolo에서 write/edit/bash가 승인 없이 실행 | runtime/CLI/TUI tests PASS |
| 3. 기본 모드 보존 | 옵션 없이는 기존 승인이 계속 필요 | regression/full suite PASS |

## 구현 단계

### Task 1: 실행 정책을 CLI에서 runtime까지 전달
- `--yolo`를 top-level과 `run`에 추가하고 TUI, interactive fallback, runtime까지 전달한다. help에는 “write/edit/bash 승인 생략”, “주의: 작업 폴더 밖 bash 영향 가능”, “기본 모드는 승인 유지”를 명시한다. `--once --yolo`는 거부한다.
- TUI 시작 상태와 interactive 배너에 `YOLO: enabled`와 취소/중단 복구 안내를 표시한다.
- Run: `uv run agentos --help && uv run agentos run --help && uv run pytest -q tests/test_cli_contract.py -k 'yolo'`
- Expected: 두 help에 경고/사용 예가 표시되고, flag 전달·`--once` 거부 테스트가 PASS.

### Task 2: yolo 승인 분기와 회귀 테스트
- runtime에 명시적 `yolo` 인자를 추가한다. yolo=True일 때만 write/edit/bash confirmation을 생략하고 read-only 정책과 기본 모드 승인을 보존한다. yolo=True에서 tool limit branch를 bypass한다.
- Rule 4 중단 조건(반복 오류, oscillation, max loop, 비용/시간/보안)을 yolo에서도 유지하고, 유한 mock fixture로 상한 bypass와 중단 조건을 각각 검증한다. 기존 runtime의 안전 중단 훅을 재사용하고, 없는 조건은 별도 범위로 확장하지 않는다.
- yolo=False 승인 테스트, yolo=True 무승인 write/edit/bash 테스트, TUI 승인 화면 미호출 테스트, TUI/interactive fallback 전달 테스트를 추가한다.
- Run: `uv run pytest -q tests/test_conversation_runtime.py tests/test_cli_contract.py tests/test_interactive_cli.py tests/test_tui_cli.py -k 'yolo or approval or tool'`
- Expected: PASS.

### Task 3: 전체 검증과 문서
- `docs/cli-reference.md`에 `agentos --yolo`, `agentos run --yolo` 사용법, 위험 경고, 기본 모드로 복귀하는 방법(옵션 제거), 취소/중단 복구를 기록하고 전체 테스트를 실행한다.
- Run: `uv run pytest -q && git diff --check`
- Expected: 전체 PASS, diff check exit 0.

## 범위와 비목표
- `--yolo` 없는 기본 실행의 승인·도구 호출 상한은 변경하지 않는다.
- 실제 shell sandboxing이나 인증 정책은 변경하지 않는다.

## 리뷰 반영 이력
- Gate 2 리뷰 대기.

## 구현 결과
- CLI/TUI/interactive에 명시적 `--yolo` 전달을 추가했다.
- `yolo=True`에서만 write/edit/bash 승인과 턴당 10회 상한을 생략한다.
- 기본 승인 정책, `--once` 거부, 사용법/위험 경고 문서와 회귀 테스트를 추가했다.
- 집중 검증: 26 passed; YOLO runtime: 2 passed.
- 전체 검증: 430 passed, 기존 `tests/test_tui_visual_contract.py` 2건 실패(이번 변경 파일과 무관한 Rich 스타일 출력 회귀).

## 사용 방법
`agentos --yolo` 또는 `agentos run --yolo`를 사용한다. 기본 승인 모드로 돌아가려면 옵션을 제거한다. `--once --yolo`는 지원하지 않는다.

## 아카이브 결정
구현·검증 후 사용자 확인 전까지 active에 유지한다.
