---
name: careful
description: 파괴적 Bash 명령(rm -rf, DROP TABLE, git push --force 등)을 PreToolUse hook으로 차단. 되돌리기 어려운 명령 실행 전 구조적 안전장치. AGENT.md Rule 2 텍스트 지침의 구조적 보완.
model: sonnet
---

# careful — 파괴적 명령 차단 Hook

## 목적

AGENT.md Rule 2("되돌리기 어려운 행동은 기록하고 확인받아라")는 텍스트 지침이다.
루프 고압 상황에서 에이전트가 무시할 수 있으므로, hook으로 구조적으로 차단한다.

## 차단 대상

| 패턴 | 이유 |
|------|------|
| `rm -rf` | 재귀 강제 삭제 — 복구 불가 |
| `DROP TABLE / DATABASE` | 데이터 손실 |
| `git push --force` / `git push -f` | 원격 히스토리 덮어쓰기 |
| `git reset --hard` | 미커밋 변경사항 폐기 |
| `TRUNCATE TABLE` | 테이블 데이터 삭제 |
| `mkfs.*` | 디스크 포맷 |

## Safety Review Surface

- command/path safety review surface는 기존 차단 범위를 약화하지 않는지 확인한다.
- destructive command 변경은 `rm -rf`, `DROP TABLE`, `DROP DATABASE`, `git push --force`, `git push -f`, `git reset --hard`, `TRUNCATE TABLE`, `mkfs.*` regression evidence를 포함해야 한다.
- protected path bypass, secret leakage, environment filtering, prompt injection 검토는 reviewer 계약에서 다루며, 이 hook은 irreversible Bash command 차단에만 집중한다.
- hook 출력 계약은 위험 명령에서 JSON `decision=block`과 `careful-dangerous-command` reason을 제공하고, 허용 명령은 exit 0으로 조용히 통과한다.

## Hook 등록 방법

`settings.json`의 `hooks.PreToolUse` 섹션에 다음을 추가:

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "bash .agents/skills/harness/careful/bin/check-careful.sh"
  }]
}
```

## 차단 해제

차단된 명령을 꼭 실행해야 할 경우:
1. 의도를 명시적으로 사용자에게 설명하고 승인받기
2. 승인 근거와 실행 범위를 기록하기
3. 승인 후 사용자가 직접 터미널에서 실행하거나, 승인된 범위 안에서 재시도하기

## 비활성화

hook을 일시 비활성화하려면 `settings.json`에서 해당 hook 항목 제거.
