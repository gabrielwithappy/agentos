# Intent Sheet: project init 스킬 카탈로그/설치 정합성 개선

**날짜:** 2026-09-04  
**요청자 의도 요약:** `agentos project init`에서 보이는 스킬 목록과 실제 설치 가능한 스킬/카테고리가 어긋나는 문제를 개선하는 실행 계획을 만든다.

## 가설
> `project init` 선택 목록의 기준을 실제 글로벌 설치 가능 스킬과 패키지 카탈로그 메타데이터로 일치시키면, 사용자는 선택 화면에서 보이는 스킬을 그대로 설치할 수 있고 카테고리도 현재 AgentOS 스킬 체계와 맞게 이해할 수 있다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `python3 - <<'PY'
import json
from pathlib import Path
from agentos.terminal.skills import DEFAULT_SKILL_NAMES
items = json.loads(Path("catalog/skills/catalog.json").read_text(encoding="utf-8"))["skills"]
names = {item["name"] for item in items}
missing = sorted(set(DEFAULT_SKILL_NAMES) - names)
uncategorized = sorted(item["name"] for item in items if item["name"] in DEFAULT_SKILL_NAMES and not item.get("category"))
assert not missing, missing
assert not uncategorized, uncategorized
print("PASS catalog-default-skill-metadata-aligned")
PY` Expected: `PASS catalog-default-skill-metadata-aligned`
- [ ] Run: `pytest tests/test_project_skill_selection.py tests/test_project_command.py -q && echo "PASS project-skill-focused-tests"` Expected: `PASS project-skill-focused-tests`
- [ ] Run: `python3 tests/helpers/pty_cli_driver.py --project-skill-selection $(command -v agentos || printf './.venv/bin/agentos')` Expected: `PASS project-skill-selection-tty`
- [ ] Run: `bash scripts/verify-cli-isolated-install.sh` Expected: `PASS agentos-cli-isolated-install`

*판단자가 누구든 동일한 결과를 낸다. "잘 되면"은 기준이 아니다.*

## 범위 제약 (Scope Fence)
- 포함: `catalog/skills/catalog.json`, `agentos/terminal/catalog.py`, `agentos/terminal/skills.py`, `agentos/commands/project.py`, focused tests, isolated install verifier, project requirement/system docs if behavior wording must be clarified.
- 제외: `.agents/skills/harness/**` 구조 변경, 새 스킬 추가, 외부 marketplace 연동, 네트워크 설치, provider/runtime 변경, 기존 optional selector navigation 구현의 불필요한 재작성.

## 기술 스택 제약
- Python stdlib, Typer/Rich 기존 CLI 구조, pytest, bash verifier만 사용한다.
- 새 외부 패키지나 live service 의존성을 추가하지 않는다.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout이 이미 `feature/project-init-toggle-skill-selector` 브랜치이며, 구현 대상이 같은 project-init 영역이다.
- ownership: 현재 브랜치에서 기존 미커밋 변경을 되돌리지 않고 후속 변경을 누적한다.

## 우선순위
- 프로덕션 수준의 안정성과 엣지 케이스 처리 우선: 선택 화면에 보인 스킬이 실제 복사 가능해야 하며, fresh install/isolated install에서도 같은 결과를 검증한다.
