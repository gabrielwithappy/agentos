# 벤더 중립 대시보드 자동 동기화 훅 배선 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-01<br>
> reviewed: true<br>
> usability_review_required: true<br>
> user_request: exec-plan 문서를 작성해도 GitHub 대시보드에 자동으로 반영되지 않는 문제를 조사한 결과, PostToolUse 훅 미배선(3개 벤더 전부) + `_try_dashboard_sync()`의 이중 no-op(.env 미로드, `agentos` PATH 부재) + 문서로만 존재하는 수동 지침이라는 3중 구조적 원인을 확인함. 이를 고치는 계획 문서를 작성하되, Gate 2 서브에이전트 리뷰는 이번 세션이 아니라 다른 세션에서 진행하기로 함.<br>
> active_agent: Claude Code<br>
> active_session: f145077e-dbba-4d91-8e7c-412b076b55b9<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg03-6Y<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** exec-plan 파일이 `active/`에 생성·수정되면, Claude Code/Codex/Gemini(Antigravity) 중 어느 벤더에서 실행하든 GitHub 대시보드가 조용히 실패하지 않고 실제로 반영되게 한다.

**사용자 결과:** 계획 문서를 쓰거나 고치기만 하면(별도 `agentos dashboard sync-plan` 수동 실행 없이) GitHub Projects 보드 카드가 자동으로 최신 상태를 반영한다. 이는 세 벤더 CLI 어디서 작업하든 동일하게 동작한다.

**진행 상태:** Gate 2 1차 리뷰(독립 서브에이전트 3명) 완료, 전원 FAIL 지적 사항 전부 반영 완료(파생 복사본 대신 어댑터 소스 수정 포함), 2차 Gate 2 리뷰 대기 중. (최초 작성 시점의 "이 세션에서는 구현하지 않는다"는 계획은 이후 세션에서 Gate 2 리뷰 + 구현을 함께 진행하기로 변경됨.)

**아키텍처:** 이미 존재하는 `.agents/hooks/scripts/dashboard_sync_on_plan_write.py`(PostToolUse 훅 본체, 이미 fail-open으로 작성됨)와 `plan_lifecycle.py::_try_dashboard_sync()`(실제 동기화 트리거)는 그대로 재사용한다. 세 벤더 설정 파일(`.claude/settings.json`, `.codex/hooks.json`, `.gemini/plugins/agentos-unified-hooks/main.py`)은 이미 PreToolUse에서 Edit/Write류 도구를 `check-alignment.py`로 분기시키는 검증된 패턴을 갖고 있으므로, PostToolUse에도 동일한 matcher/tool-name으로 `dashboard_sync_on_plan_write.py`를 추가 배선한다(새 배선 방식을 발명하지 않음). `_try_dashboard_sync()`는 `.env` 미로드와 `agentos` PATH 부재라는 두 개의 독립적인 조용한 실패 원인을 각각 고친다.

**기술 스택:** Python 3.9~3.11 호환 표준 라이브러리, 기존 Claude Code JSON hook 설정, Codex JSON hook 설정, Gemini(Antigravity) Python 플러그인 브리지, GitHub GraphQL API(검증 단계에서만 사용).

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 3중 구조적 원인 조사 및 각 벤더 설정 파일 직접 확인(코드/설정 인용 근거 있음), 계획 초안 작성 |
| 현재 위치 | Gate 2 1차 리뷰 완료(3개 리뷰어 전원 FAIL 반영: 파생 복사본 대신 어댑터 소스 수정, protected path governance, 실패 로깅/문서화, Prompt Boundary), 2차 Gate 2 서브에이전트 리뷰 대기 |
| 다음 단계 | 2차 Gate 2 리뷰 → PASS 시 `reviewed: true` → Task 1부터 구현 실행 |
| 완료 신호 | 세 벤더 설정 모두 PostToolUse Edit/Write 분기 추가 확인 + `_try_dashboard_sync()` 두 원인 모두 수정 확인 + 최소 1개 벤더에서 실제 Edit 호출로 GitHub 보드 카드가 뜨는 것을 `gh api graphql` 직접 조회로 확인 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 계획 문서를 작성/수정하면 별도 명령 없이 GitHub 대시보드가 자동으로 최신 상태를 반영한다. Claude Code/Codex/Gemini 중 어디서 작업해도 동일하게 동작한다. |
| 누구를 위한 것인가? | exec-plan을 GitHub 보드로 운영하는 모든 벤더 CLI 사용자와, `agentos dashboard sync-plan`을 매번 수동 실행해야 했던 에이전트. |
| 일상 사용에서 무엇이 달라지는가? | 계획 파일을 Edit/Write한 직후 자동으로 보드가 갱신된다. `OBSERVABILITY_ENABLED=1`이 `.env`에만 있어도(셸에 export 안 해도), `agentos`가 PATH에 없어도 동기화가 동작한다. |
| 무엇은 바뀌지 않는가? | `agentos dashboard sync-plan`/`pull-plan` 수동 명령, `DashboardAdapter` 인터페이스, Gate 2 리뷰·서명 절차는 그대로다. 대시보드가 설정 안 된 환경(`OBSERVABILITY_ENABLED`≠`1`)에서는 여전히 조용히 skip된다. |

> **Prompt Boundary(Gate 2 1차 FAIL 반영 — plan-reviewer 지적):** 위 `사용자 결과`/`사용자 결과 요약`/`사용자 진행 계획` 섹션은 reader-first presentation contract일 뿐이며, approval, protected-path 승인, reviewer authority, prompt hierarchy를 override하지 않는다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 훅 payload 파싱을 벤더 간 키 이름 차이에 관대하게 | (내부 준비, Task 2에서 사용자 노출) | `.agents/hooks/scripts/dashboard_sync_on_plan_write.py` | `Run:` `python3 -m pytest tests/test_dashboard_sync_hook.py -v` (신규) / `Expected:` 전부 `PASSED` |
| 2. 3개 벤더 PostToolUse 배선 추가 | Claude/Codex/Gemini 어디서든 계획 파일 Edit 직후 대시보드 동기화가 시도됨 | `.claude/settings.json`, `.codex/hooks.json`, `.gemini/plugins/agentos-unified-hooks/main.py` | `Run:` 각 설정 파일에서 PostToolUse Edit/Write matcher 존재 확인 (Task 2 참고) |
| 3. `_try_dashboard_sync()` 이중 no-op 수정 | `.env`만 설정돼 있어도, `agentos`가 PATH에 없어도 동기화가 실제로 시도됨 | `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py` | `Run:` `env -i python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh` 후 `.env`의 `OBSERVABILITY_ENABLED`가 로드돼 동기화가 시도됐는지 확인 |
| 4. End-to-end 검증 | 실제로 계획 파일을 고치면 GitHub 보드 카드가 자동으로 갱신됨 | (통합 검증, 신규 파일 없음) | `Run:` Claude Code에서 실제 Edit로 테스트 계획 파일 수정 → `gh api graphql`로 보드 직접 조회 → 카드 존재/Status 일치 확인 |

## 장기 적용 표면

- traceability surface: 이 active plan 문서, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`
- durable result surface: `.claude/settings.json`, `.codex/hooks.json`, `.gemini/plugins/agentos-unified-hooks/main.py`, `.agents/hooks/scripts/dashboard_sync_on_plan_write.py`, `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py`, `docs/observability-setup.md`(자동 동기화 동작을 문서화) — 실제로 동작하는 훅 배선과 그 문서
- documentation-only exception: 없음 — 코드/설정 변경이 durable result다.

---

## File Structure

- 수정: `.agents/hooks/scripts/dashboard_sync_on_plan_write.py` — `_touched_paths()`가 `file_path` 외에 벤더별로 다를 수 있는 키(`path` 등)도 허용하도록 확장. (정확한 Codex/Gemini payload 키 이름은 Task 1에서 best-guess로 확정하고, 실제 라이브 검증은 Task 4의 codex-gemini-live-runtime 게이트로 넘긴다 — 아래 의존성 게이트 참고.)
- 생성: `tests/test_dashboard_sync_hook.py` — payload 키 별칭 처리, active-plan-path 판별 로직 단위 테스트.
- 수정: `.agents/hooks/adapters/claude-code/settings.json` — `PostToolUse`에 `matcher: "Replace|Edit|Write.*"` 항목 추가(기존 PreToolUse와 동일 matcher). **(Gate 2 1차 FAIL 반영 — plan-reviewer/principle-auditor 지적: `.claude/settings.json`은 `scripts/install-hooks.sh`가 이 어댑터 템플릿에서 `cp`로 생성하는 파생 복사본이라 직접 고치면 다음 `agentos setup`/`install-hooks.sh` 실행 시 되돌아간다. 반드시 소스인 이 파일을 고친다.)**
- 수정: `.agents/hooks/adapters/codex/hooks.json` — `PostToolUse`에 `matcher: "write_to_file|replace_file_content|multi_replace_file_content"` 항목 추가(기존 PreToolUse와 동일 matcher). **(동일 이유로 `.codex/hooks.json`이 아닌 이 소스 파일을 고친다.)**
- 수정: `.agents/hooks/adapters/agy/main.py` — `post_tool_call()`에 `tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]` 분기 추가(기존 `pre_tool_call()`과 동일 tool-name 목록), 함수 인자로 이미 갖고 있는 `tool_args`를 JSON payload로 구성해 `subprocess.run(..., input=...)`으로 전달. **(동일 이유로 `.gemini/plugins/agentos-unified-hooks/main.py`가 아닌 이 소스 파일을 고친다.)**
- 실행: `bash scripts/install-hooks.sh` — 위 세 소스 변경을 `.claude/settings.json`/`.codex/hooks.json`/`.gemini/plugins/agentos-unified-hooks/main.py`(파생 복사본)에 반영. Task 2 Step 4에서 diff로 동기화 여부를 검증한다.
- 수정: `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py` — `_try_dashboard_sync()`가 `.env`를 직접 로드하고, `agentos` PATH 탐색 실패 시 리포 상대경로 `<root>/.venv/bin/agentos` → `uv run agentos` 순으로 폴백하며, 실패 시 `agentos.log`에 원인을 남긴다. **이 파일은 `.agents/skills/harness/*` protected path이므로 Task 3에 governance Step을 포함한다(Gate 2 1차 FAIL 반영 — principle-auditor 지적).**
- 수정: `docs/observability-setup.md` — "계획 문서 저장 시 자동 동기화" 동작, 그 전제조건(`OBSERVABILITY_ENABLED=1`), 실패 시 확인 경로(`agentos.log`)와 기존 수동 `sync-plan` 섹션으로의 상호 참조를 문서화(Task 3 Step 5).

---

## Task 상세 구현 계획

### Task 1: 훅 payload 파싱을 벤더 간 키 이름 차이에 관대하게 만들기

**파일:**
- 수정: `.agents/hooks/scripts/dashboard_sync_on_plan_write.py`
- 생성: `tests/test_dashboard_sync_hook.py`

**사용자에게 보이는 마일스톤:** (내부 준비 단계, Task 2에서 사용자 노출)

- [ ] **Step 1 (Gate 2 1차 FAIL 반영 — plan-reviewer 지적: "확정" 표현이 실제로 검증되지 않은 추측을 검증된 것처럼 서술함):** `_touched_paths()`가 `tool_input`에서 `file_path` 외에 `path`, `target_file` 등 흔히 쓰이는 대체 키도 확인하도록 확장한다. Claude Code는 `file_path`가 확인된 키(PreToolUse alignment 훅이 이미 이 키로 잘 동작 중)지만, Codex/Gemini의 실제 PostToolUse payload 키 이름은 이 저장소에 기존 선례가 없다(PreToolUse 쪽 `check-alignment.py`가 payload를 아예 안 읽기 때문). 아래 의존성 게이트(`codex-gemini-live-runtime`)의 preflight(`which codex; which gemini`)는 **바이너리 존재 여부만 확인하며 payload 키 스키마를 검증하지 않는다** — 이 사실을 숨기지 않는다. `path`/`target_file`은 여러 도구 호출 스키마에서 흔히 쓰이는 이름을 기반으로 한 best-guess 별칭 목록이며, 라이브 검증은 Task 4 Step 3에서 해당 벤더 CLI가 이 세션에서 실행 가능한 경우에만 이루어진다. 실행 불가능하면 이 키 목록은 "정적 검증만 통과, 실제 스키마 미확인"으로 계획 문서에 정직하게 남긴다(Task 4 Step 3과 동일 원칙).

```python
_FILE_PATH_KEYS = ("file_path", "path", "target_file")

def _touched_paths(payload: dict) -> list[str]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    paths = []
    for key in _FILE_PATH_KEYS:
        if key in tool_input:
            paths.append(str(tool_input[key]))
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                for key in _FILE_PATH_KEYS:
                    if key in edit:
                        paths.append(str(edit[key]))
    return paths
```

- [ ] **Step 2:** `tests/test_dashboard_sync_hook.py`에 `_touched_paths()`가 세 키 별칭 모두를 인식하는지, active-plan 경로가 아닌 파일은 걸러지는지, `tool_name`이 Edit류가 아니면 즉시 종료하는지 단위 테스트를 추가한다.

Run: `python3 -m pytest tests/test_dashboard_sync_hook.py -v`
Expected: 전부 `PASSED`

---

### Task 2: 3개 벤더 설정에 PostToolUse Edit/Write 분기 추가

**파일:**
- 수정: `.agents/hooks/adapters/claude-code/settings.json`, `.agents/hooks/adapters/codex/hooks.json`, `.agents/hooks/adapters/agy/main.py` (벤더 어댑터 소스 — `scripts/install-hooks.sh`가 여기서 `.claude/settings.json`/`.codex/hooks.json`/`.gemini/plugins/agentos-unified-hooks/main.py`로 복사한다)

**사용자에게 보이는 마일스톤:** Claude/Codex/Gemini 어디서든 계획 파일 Edit 직후 대시보드 동기화가 시도됨

**Gate 2 1차 FAIL 반영 — plan-reviewer/principle-auditor 지적:** 최초 초안은 `.claude/settings.json`/`.codex/hooks.json`/`.gemini/plugins/agentos-unified-hooks/main.py`를 직접 수정하는 것으로 계획했다. 이 세 파일은 `scripts/install-hooks.sh`가 `.agents/hooks/adapters/{claude-code,codex,agy}/*`에서 `cp`로 생성하는 **파생 복사본**이며(직접 `diff`로 현재 byte-identical임을 확인함), `AGENTS.md` Rule 9는 "어댑터 로직을 수정한 후에는 반드시 `agentos setup`을 실행하여 훅 연결 상태를 갱신해야 한다"고 명시한다. 파생 복사본만 고치면 다음 `agentos setup`/`install-hooks.sh` 실행 시 이 배선이 조용히 되돌아간다 — 이 계획이 고치려는 문제(조용한 no-op)를 다른 경로로 재발시키는 것이므로, 아래 Step들은 소스 파일을 고치고 `install-hooks.sh`로 파생 복사본을 재생성한다.

- [ ] **Step 1 (Claude):** `.agents/hooks/adapters/claude-code/settings.json`의 `hooks.PostToolUse` 배열에 아래 항목을 추가한다(기존 PreToolUse의 `"Replace|Edit|Write.*"` matcher와 동일하게 맞춤).

```json
{
  "matcher": "Replace|Edit|Write.*",
  "hooks": [
    {
      "type": "command",
      "command": "/bin/bash -lc 'root=\"${CLAUDE_PROJECT_DIR:-}\"; if [[ -z \"$root\" ]]; then root=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"; fi; python3 \"$root/.agents/hooks/scripts/dashboard_sync_on_plan_write.py\" \"$root\"'"
    }
  ]
}
```

Run: `python3 -c "import json; d=json.load(open('.agents/hooks/adapters/claude-code/settings.json')); print(any(e.get('matcher')=='Replace|Edit|Write.*' for e in d['hooks']['PostToolUse']))"`
Expected: `True`

- [ ] **Step 2 (Codex):** `.agents/hooks/adapters/codex/hooks.json`의 `hooks.PostToolUse` 배열에 아래 항목을 추가한다(기존 PreToolUse의 `"write_to_file|replace_file_content|multi_replace_file_content"` matcher와 동일하게 맞춤).

```json
{
  "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
  "hooks": [
    {
      "type": "command",
      "command": "/bin/bash -lc 'root=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"; python3 \"$root/.agents/hooks/scripts/dashboard_sync_on_plan_write.py\" \"$root\"'",
      "statusMessage": "Syncing dashboard after plan edit"
    }
  ]
}
```

Run: `python3 -c "import json; d=json.load(open('.agents/hooks/adapters/codex/hooks.json')); print(any('write_to_file' in e.get('matcher','') for e in d['hooks']['PostToolUse']))"`
Expected: `True`

- [ ] **Step 3 (Gemini):** `.agents/hooks/adapters/agy/main.py`의 `post_tool_call(tool_name, tool_args, tool_result)`에 아래 분기를 추가한다(기존 `pre_tool_call()`의 tool_name 목록과 동일).

```python
elif tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
    root = get_workspace_root()
    script_path = os.path.join(root, ".agents/hooks/scripts/dashboard_sync_on_plan_write.py")
    if os.path.exists(script_path):
        payload = json.dumps({"tool_name": tool_name, "tool_input": tool_args})
        subprocess.run(
            [sys.executable, script_path, root],
            input=payload,
            capture_output=True,
            text=True,
            env=os.environ,
        )
```

(`import json`을 파일 상단에 추가한다.) `tool_args`의 실제 키 이름(`file_path`/`path`/`target_file` 등)은 Task 1에서 정한 best-guess 별칭 목록을 그대로 쓰며, 라이브 스키마 확인은 Task 4 Step 3의 범위다(Task 1 Step 1 참고).

Run: `grep -n "write_to_file.*replace_file_content" .agents/hooks/adapters/agy/main.py`
Expected: `post_tool_call` 함수 내부에 최소 1개 매치

- [ ] **Step 4 (Gate 2 1차 FAIL 반영 — plan-reviewer/principle-auditor 지적: 파생 복사본에도 반영 + 재클로버 방지 검증):** `bash scripts/install-hooks.sh`를 실행해 Step 1-3의 소스 변경을 `.claude/settings.json`/`.codex/hooks.json`/`.gemini/plugins/agentos-unified-hooks/main.py`(파생 복사본)에 반영하고, 소스와 복사본이 다시 byte-identical한지 `diff`로 직접 확인한다(추정하지 않는다).

Run: `bash scripts/install-hooks.sh && diff .agents/hooks/adapters/claude-code/settings.json .claude/settings.json && diff .agents/hooks/adapters/codex/hooks.json .codex/hooks.json && diff .agents/hooks/adapters/agy/main.py .gemini/plugins/agentos-unified-hooks/main.py && echo ALL_SYNCED`
Expected: `install-hooks.sh`가 exit 0으로 끝나고, 세 `diff` 모두 출력 없음(동일), 마지막 줄에 `ALL_SYNCED`

---

### Task 3: `_try_dashboard_sync()` 이중 no-op 수정 + Protected Path Governance + 사용법 문서화

**파일:**
- 수정: `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py`
- 수정: `docs/observability-setup.md` (Step 5, Gate 2 2차 FAIL 반영 — plan-reviewer 지적: 누락되어 있었음)

**사용자에게 보이는 마일스톤:** `.env`만 설정돼 있어도, `agentos`가 PATH에 없어도 동기화가 실제로 시도됨

- [ ] **Step 1:** `_try_dashboard_sync()`가 호출 시점에 `.env`를 직접 로드하도록 고친다(이미 `agentos/observability/setup.py::load_env_file()`이 하는 것과 동일한 최소 파싱을 인라인으로 둔다 — `agentos` 패키지를 import 의존성으로 새로 추가하지 않기 위해 의도적으로 중복한다).

```python
def _load_env_if_needed(root: Path) -> None:
    import os

    if os.environ.get("OBSERVABILITY_ENABLED") == "1":
        return
    env_path = root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v.strip('"\''))
```

- [ ] **Step 2:** `_try_dashboard_sync()`에서 위 함수를 호출한 뒤, `agentos`가 PATH에 없으면 순서대로 폴백한다: (1) 리포 루트 기준 `.venv/bin/agentos`(이 checkout이 `uv sync`/`uv tool install --force .`로 이미 준비돼 있다면 존재), (2) `uv`가 PATH에 있으면 `uv run agentos`.

**`sys.executable -m agentos.cli`로 폴백하면 안 된다** — 이 훅은 `.claude/settings.json`/`.codex/hooks.json`에 하드코딩된 시스템 `python3`로 실행되는데(예: 이 개발 환경은 Python 3.9.6), 그 인터프리터에는 `typer` 등 `agentos`의 런타임 의존성이 설치돼 있지 않아 `import agentos.cli`가 `ModuleNotFoundError`로 실패한다(직접 재현 확인함). `.venv/bin/agentos`나 `uv run agentos`는 프로젝트가 관리하는 가상환경을 쓰므로 이 문제가 없다.

```python
def _resolve_agentos_cmd(root: Path) -> list[str] | None:
    import shutil

    agentos_bin = shutil.which("agentos")
    if agentos_bin:
        return [agentos_bin]

    venv_bin = root / ".venv" / "bin" / "agentos"
    if venv_bin.is_file():
        return [str(venv_bin)]

    uv_bin = shutil.which("uv")
    if uv_bin:
        return [uv_bin, "run", "agentos"]

    return None


def _log_dashboard_sync_failure(returncode: int | None, output: str) -> None:
    """Best-effort: persist a failed auto-sync attempt to agentos.log.

    docs/observability-setup.md already promises sync-plan failures land in
    "CLI 콘솔과 agentos.log". This PostToolUse hook has no console a human
    watches, so without this the auto-sync path would be strictly less
    debuggable than the manual command it wraps (Gate 2 1차 FAIL — usability-reviewer).
    """
    try:
        import logging
        import sys

        repo_root = Path(__file__).resolve().parents[5]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from agentos.terminal.logging_setup import configure_logging

        configure_logging()
        logging.getLogger("agentos.dashboard_sync_hook").warning(
            "[Observability Warning] 자동 dashboard sync-plan 실패(exit=%s): %s",
            returncode,
            output.strip()[:500],
        )
    except Exception:
        pass


def _try_dashboard_sync(root: Path) -> None:
    import os
    import subprocess

    _load_env_if_needed(root)
    if os.environ.get("OBSERVABILITY_ENABLED") != "1":
        return

    base_cmd = _resolve_agentos_cmd(root)
    if base_cmd is None:
        return

    try:
        result = subprocess.run(
            base_cmd + ["dashboard", "sync-plan", "--all"],
            cwd=root,
            capture_output=True,
            timeout=10,
            check=False,
            text=True,
        )
        combined_output = (result.stdout or "") + (result.stderr or "")
        # `sync-plan --all` catches per-file adapter errors and always exits 0
        # (agentos/commands/dashboard.py: the --all loop wraps each _do_sync()
        # in try/except and never re-raises), so returncode alone misses the
        # realistic failure case. Scan for the command's own failure markers
        # instead (Gate 2 2차 FAIL 반영 — usability-reviewer 지적: 아래 참고).
        if (
            result.returncode != 0
            or "동기화 실패" in combined_output
            or "Failed to sync" in combined_output
        ):
            _log_dashboard_sync_failure(result.returncode, combined_output)
    except Exception as exc:
        _log_dashboard_sync_failure(None, str(exc))
```

Run: `python3 -c "
import sys
sys.path.insert(0, '.agents/skills/harness/writing-plans/scripts')
from plan_lifecycle import _resolve_agentos_cmd
from pathlib import Path
print(_resolve_agentos_cmd(Path('.')))
"`
Expected: `agentos`가 PATH에 없는 이 환경에서 `['<repo-root>/.venv/bin/agentos']`가 출력됨(빈 리스트나 `None`이 아님)

Run: `env -i PATH="$PATH" python3 -c "
import sys
sys.path.insert(0, '.agents/skills/harness/writing-plans/scripts')
from plan_lifecycle import _load_env_if_needed
from pathlib import Path
import os
_load_env_if_needed(Path('.'))
print(os.environ.get('OBSERVABILITY_ENABLED'))
"`
Expected: `.env`에 설정된 값(예: `1`)이 출력됨(이전에는 `None`이었던 것과 대조)

- [ ] **Step 3 (Gate 2 1차 FAIL 반영 — usability-reviewer 지적: 자동 동기화 실패가 발견 불가능함 / Gate 2 2차 FAIL 반영 — usability-reviewer 지적: `sync-plan --all`은 개별 어댑터 실패를 삼키고 항상 exit 0을 반환하므로 `returncode != 0`만으로는 실제 실패를 못 잡음):** `agentos/commands/dashboard.py`의 `sync_plan` `--all` 분기는 각 파일의 `_do_sync()`를 `try/except`로 감싸고 재발생시키지 않으므로(파일별 실패는 콘솔에 `동기화 실패: ...`만 출력하고 루프는 계속 진행), `_try_dashboard_sync()`는 `returncode != 0` 또는 캡처된 출력에 `동기화 실패`/`Failed to sync` 마커가 있는지로 판정한다("대시보드가 설정되어 있지 않아 건너뜁니다" 같은 의도된 skip 메시지와는 겹치지 않는 marker이므로 정상 skip을 실패로 오판하지 않는다). 이 판정이 `agentos.log`에 실제로 기록되는지, 일부러 깨뜨린 `sync-plan` 호출(예: 존재하지 않는 project number)로 확인한다.

Run: `python3 -c "
import sys
sys.path.insert(0, '.agents/skills/harness/writing-plans/scripts')
from plan_lifecycle import _log_dashboard_sync_failure
_log_dashboard_sync_failure(1, 'synthetic test failure for Gate 2 verification')
" && grep -n "synthetic test failure for Gate 2 verification" ~/.agentos/logs/agentos.log`
Expected: `grep`가 방금 기록한 `[Observability Warning] 자동 dashboard sync-plan 실패(exit=1): synthetic test failure...` 줄을 찾아냄(빈 결과 아님)

- [ ] **Step 4 (Gate 2 1차 FAIL 반영 — principle-auditor 지적: `.agents/skills/harness/*` protected path인데 governance Step 누락):** 이 Task가 수정하는 `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py`는 `.agents/agents/harness/plan-reviewer.md`가 정의하는 protected path(`​.agents/skills/harness/*`)에 해당한다. `.agents/_version.json`의 `authorized_architects`를 확인하고(선행 계획 `2026-08-01-gate2-hash-normalization-fix.md`가 이미 `claude`를 추가해 top-level/`distribution` 양쪽에 존재함을 재확인), `sync-manifest --check`를 실행해 이 변경이 하네스 무결성을 깨지 않는지 검증한다. 이번 변경은 `authorized_architects` 자체를 건드리지 않으므로 `--update`는 필요하지 않지만, 그 사실을 실행으로 확인한다(추정하지 않는다). `principle-auditor` 구조 감사는 이 계획의 Gate 2 리뷰 라운드가 그 역할을 겸한다.

Run: `python3 -c "import json; d=json.load(open('.agents/_version.json')); print('claude' in d['authorized_architects'], 'claude' in d['distribution']['authorized_architects'])" && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `True True` 출력, 이어서 `🏆 [PASS] 하네스 무결성 확인 완료.`(exit 0)

- [ ] **Step 5 (Gate 2 1차 FAIL 반영 — usability-reviewer 지적: File Structure가 약속한 `docs/observability-setup.md` 변경을 실행할 Task가 없었음 + 상호 참조 누락):** `docs/observability-setup.md`의 기존 `## agentos dashboard sync-plan` 섹션 바로 아래에 `## 계획 문서 저장 시 자동 동기화` 섹션을 추가한다. 포함 내용:
  - 동작 설명: `.claude`/`.codex`/`.gemini` 중 어느 벤더에서 `active/` 하위 계획 파일을 Edit/Write해도 PostToolUse 훅이 자동으로 `sync-plan --all`을 시도한다.
  - 전제조건: `OBSERVABILITY_ENABLED=1`(`.env` 또는 셸 환경변수 둘 다 인식).
  - **보드가 안 바뀔 때 확인할 것(신규, usability 지적 반영):** ① `~/.agentos/logs/agentos.log`에서 `[Observability Warning] 자동 dashboard sync-plan 실패` 검색, ② 위 기존 `## agentos dashboard sync-plan` 섹션의 수동 명령 `agentos dashboard sync-plan --all`로 즉시 재시도(자동 동기화가 막혀도 수동 경로는 항상 열려 있음을 명시적으로 링크).
  - 자동 동기화는 fail-open이라 실패해도 파일 편집 자체를 막지 않는다는 것을 명시.

Run: `grep -n "계획 문서 저장 시 자동 동기화\|agentos.log" docs/observability-setup.md`
Expected: 새 섹션 제목과 `agentos.log` 언급이 모두 최소 1줄 이상 매치

---

### Task 4: End-to-end 검증

**파일:** 없음(통합 검증)

**사용자에게 보이는 마일스톤:** 실제로 계획 파일을 고치면 GitHub 보드 카드가 자동으로 갱신됨

- [ ] **Step 1:** 이 세션이 실행 중인 벤더 CLI(Claude Code/Codex/Gemini) 하나에서, 테스트용 계획 파일을 실제 Edit 도구로 수정해 PostToolUse 훅이 진짜로 발동하는지 확인한다(배선 코드만 보고 "될 것"이라고 추정하지 않는다).
- [ ] **Step 2:** `gh api graphql`로 GitHub Projects 보드를 직접 조회해(`totalCount` 확인 후 전체 items 스캔 — 이전 세션에서 `first:50`으로 잘라서 새 카드를 놓친 전례가 있으니 페이지네이션/전체 개수를 반드시 확인할 것) 해당 카드가 실제로 존재하고 Status가 로컬 계획 문서 상태와 일치하는지 확인한다.
- [ ] **Step 3 (가능한 범위까지):** 이 세션에서 직접 실행할 수 없는 벤더(Codex/Gemini는 별도 CLI 런타임이 필요해 이 세션에서 실제 기동이 불가능할 수 있음)는 설정 파일의 JSON/코드 정합성 검증(Task 2의 각 Run:)까지만 하고, 실제 실행 확인이 안 됐다는 사실을 계획 문서에 정직하게 남긴다. 두 벤더 모두 실행 불가능하다면 최소 1개 벤더의 실제 E2E와 나머지 벤더의 정적 검증을 완료 기준으로 삼는다.

Run: (Step 1에서 실행한 벤더에 맞는 Edit 명령) 후 `gh api graphql -f query='query($owner:String!,$number:Int!){user(login:$owner){projectV2(number:$number){items(first:100){totalCount nodes{content{...on DraftIssue{title}} fieldValueByName(name:"Status"){...on ProjectV2ItemFieldSingleSelectValue{name}}}}}}}' -f owner="$OBSERVABILITY_GITHUB_OWNER" -F number="$OBSERVABILITY_GITHUB_PROJECT_NUMBER"`
Expected: 응답 JSON의 `nodes` 목록에 테스트 계획 문서의 제목이 존재

- [ ] **Step 4 (Gate 2 1차 FAIL 반영 — usability-reviewer 지적: 성공 경로만 검증되고 "설정은 됐는데 조용히 실패하는" 시나리오가 한 번도 확인되지 않음 / Gate 2 2차 FAIL 반영 — usability-reviewer 지적: 최초 수정은 `returncode != 0`에만 의존했는데 `sync-plan --all`은 개별 어댑터 실패를 삼키고 항상 exit 0을 반환해 이 negative-path 검증 자체가 실패를 못 잡았을 것이라는 코드 추적 지적. Task 3 Step 3에서 `동기화 실패`/`Failed to sync` 텍스트 마커 판정으로 고쳤으므로, 이 Step은 그 고친 로직이 진짜 실패 시나리오에서도 동작하는지 재확인한다):** 일부러 `OBSERVABILITY_GITHUB_PROJECT_NUMBER`를 존재하지 않는 값으로 바꾼 뒤 계획 파일을 Edit해 자동 동기화를 실패시키고, `agentos.log`에 실패 흔적이 실제로 남는지 확인한다. 확인 후 원래 값으로 되돌린다.

Run: `OBSERVABILITY_GITHUB_PROJECT_NUMBER=999999 <Step 1과 동일한 벤더 Edit 명령으로 계획 파일 재수정>; sleep 2; grep -n "Observability Warning.*자동 dashboard sync-plan 실패" ~/.agentos/logs/agentos.log | tail -5`
Expected: 방금 실패가 `agentos.log`에서 확인됨(빈 결과 아님) — 사용자가 board가 안 움직일 때 확인할 곳이 실제로 존재함을 증명

---

## 의존성 분석

- 외부 의존성: 아래에 선언함
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption. Task 4는 라이브 GitHub GraphQL API 호출을 실제로 수행하므로(Task 1-3의 `Run:`은 전부 로컬/mock), 의존성 게이트로 선언한다.

## 의존성 게이트

### github-graphql-api-read
- name: github-graphql-api-read
- type: external-service
- required: false (Gate 2 1차 FAIL 반영 — plan-reviewer 지적: `required: true`이면 그 preflight는 파일을 건드리기 전 Task 0에 있어야 하는데, 이 의존성은 실제로 Task 4의 E2E 검증에만 필요하고 Task 1-3의 구현/단위 테스트는 필요 없다. 존재하지도 않는 필요를 `required: true`로 잘못 표시하는 대신, Task 4 자체의 preflight(아래 `Run:`)로 그 지점에서 게이팅한다 — 별도 Task 0을 추가하는 것보다 단순하다.)
- purpose: GitHub Projects v2 보드에 실제로 카드가 생성/갱신됐는지 CLI 종료 코드가 아니라 API 응답으로 직접 확인하기 위함(이전 세션에서 CLI 성공 메시지만 믿었다가 실제로는 페이지네이션 때문에 카드를 못 찾았던 전례가 있어, 이번에는 신뢰하지 않고 직접 조회를 필수 단계로 둠).
- preflight:
  Run: `gh auth status`
  Expected: `✓ Logged in to github.com account ... Token scopes: ... 'project' ...`
- fallback:
  available: true
  trigger: `gh` 미인증 또는 `project` scope 없음
  action: Task 4를 "정적 배선 검증까지만 완료, 라이브 카드 확인은 보류"로 표시하고 계획을 완료 처리하지 않는다.
  limits: 실제 GitHub 반영 여부를 확인 못 한 채로는 이 계획을 "완료"로 닫지 않는다.
  verification:
    Run: `gh auth status`
    Expected: 실패 시 위 fallback 경로로 진행
- failure_behavior: use_fallback

### codex-gemini-live-runtime
- name: codex-gemini-live-runtime
- type: live-runtime
- required: false
- purpose: Task 2의 Codex/Gemini 배선이 실제 해당 CLI에서 발동하는지 라이브로 확인하려면 그 벤더의 CLI 런타임이 필요하다. 이 세션(Claude Code)에서는 기동할 수 없을 가능성이 높다.
- preflight:
  Run: `which codex; which gemini`
  Expected: 둘 다 없거나 하나만 있을 수 있음 — 있는 경우에만 해당 벤더 라이브 검증을 시도
- fallback:
  available: true
  trigger: 해당 벤더 CLI가 이 세션에서 실행 불가능
  action: 그 벤더는 Task 2의 정적 JSON/코드 검증(Run:)까지만 완료로 인정하고, "실제 실행 미확인"을 계획 문서에 명시한다
  limits: 정적 검증만으로는 stdin/payload 스키마 불일치 같은 런타임 전용 버그를 잡을 수 없다
  verification:
    Run: `python3 -c "import json; json.load(open('.codex/hooks.json'))" && python3 -c "import ast; ast.parse(open('.gemini/plugins/agentos-unified-hooks/main.py').read())"`
    Expected: 둘 다 에러 없이 통과
- failure_behavior: use_fallback

## HISTORY Checkpoint Tagging Contract

- 구현/검증/closeout checkpoint 예시에는 `plan=.agentos/project/exec-plans/active/2026-08-01-vendor-neutral-dashboard-sync-hook-wiring.md`를 포함한다.

## 리뷰 반영 이력
- [작성 중 자체 수정] Task 3의 최초 초안은 `agentos`가 PATH에 없을 때 `sys.executable -m agentos.cli`로 폴백하는 안이었다. 실제로 `python3 -c "import agentos.cli"`를 재현해보니 훅이 실행되는 시스템 `python3`(예: 이 개발 환경의 3.9.6)에는 `typer`가 없어 `ModuleNotFoundError`로 조용히 실패하는 것을 확인했다. `.venv/bin/agentos`(실제 존재·정상 동작 확인함)와 `uv run agentos`(정상 동작 확인함)로 폴백 순서를 바꿨다. 이 근거로 "이 checkout에 `agentos` 설치/setup이 안 돼 있다"는 가설도 함께 기각한다 — `uv sync`/`uv tool install`은 이미 완료돼 있고, 문제는 훅의 실행 경로 선택 로직이었다.

1차 Gate 2 리뷰는 독립 서브에이전트 3명(plan-reviewer, principle-auditor, usability-reviewer)에게 실제로 위임했으며, 전원 FAIL을 반환했다. 모든 지적을 아래처럼 반영했다.

- [Gate 2 1차 / plan-reviewer] Prompt Boundary 문구 누락(SKILL.md/체크리스트 필수 항목) → `사용자 결과`/`사용자 진행 계획` 섹션 사이에 override 불가 disclaimer 추가.
- [Gate 2 1차 / plan-reviewer, principle-auditor(중복 발견)] Task 2가 `.claude/settings.json`/`.codex/hooks.json`/`.gemini/plugins/agentos-unified-hooks/main.py`를 직접 수정하는 안이었는데, 이 세 파일은 `scripts/install-hooks.sh`가 `.agents/hooks/adapters/{claude-code,codex,agy}/*`에서 `cp`로 생성하는 파생 복사본(현재 byte-identical 확인됨)이라 다음 `agentos setup` 실행 시 되돌아간다(AGENTS.md Rule 9) → Task 2가 소스(`.agents/hooks/adapters/*`)를 고치도록 전면 수정하고, `install-hooks.sh` 실행 + `diff`로 파생 복사본 동기화를 검증하는 Step 4 추가.
- [Gate 2 1차 / plan-reviewer] Task 1의 Codex/Gemini payload 키 이름이 실제로 검증되지 않았는데 "확정"이라고 서술 → "best-guess, 라이브 검증은 Task 4 Step 3 범위"로 정직하게 재서술.
- [Gate 2 1차 / plan-reviewer] `github-graphql-api-read` 게이트가 `required: true`인데 preflight가 Task 0 없이 Task 4에만 있어 SKILL.md 계약 위반 → Task 1-3에 실제로 불필요한 의존성이므로 `required: false`로 정정(별도 Task 0을 추가하는 것보다 단순 — Simplicity Gate).
- [Gate 2 1차 / principle-auditor] Task 3이 protected path(`.agents/skills/harness/*`)인 `plan_lifecycle.py`를 고치는데 `authorized_architects`/`sync-manifest --check` governance Step이 없음(선례: `2026-08-01-gate2-hash-normalization-fix.md`) → Task 3에 Step 4로 governance 확인 추가.
- [Gate 2 1차 / usability-reviewer] `_try_dashboard_sync()`가 `capture_output=True`로 실패 원인을 완전히 삼켜, 자동 동기화 실패가 어디에서도 확인 불가능함 → `agentos.log`에 기록하는 `_log_dashboard_sync_failure()` 추가(Task 3 코드) + 합성 테스트(Step 3) + Task 4에 실제 실패를 유도하는 negative-path E2E Step 4 추가.
- [Gate 2 1차 / usability-reviewer] File Structure가 약속한 `docs/observability-setup.md` 변경을 실행할 Task가 원래 없었음(gap) + 기존 수동 `sync-plan` 경로로의 상호 참조 누락 → Task 3에 Step 5로 문서화 추가(agentos.log 확인 경로 + 수동 재시도 링크 포함).

수정 완료 후 Gate 0 재검토 → 통과. 2차 Gate 2 리뷰(위 수정 사항이 실제로 반영됐는지 재확인)를 다시 독립 서브에이전트 3명에게 위임했다. principle-auditor는 PASS/CLEAN, plan-reviewer와 usability-reviewer는 FAIL.

- [Gate 2 2차 / plan-reviewer] Task 3의 `**파일:**` 목록에 Step 5가 실제로 수정하는 `docs/observability-setup.md`가 빠져 있음(File Structure에는 있었음) → Task 3 파일 목록에 추가.
- [Gate 2 2차 / usability-reviewer, 코드 추적으로 새로 발견] `agentos/commands/dashboard.py`의 `sync_plan --all` 분기를 직접 읽어보니, 개별 파일 동기화 실패를 `try/except`로 삼키고 재발생시키지 않아 **항상 exit 0을 반환**한다는 것을 확인. Task 3 Step 3(1차 수정)의 `_try_dashboard_sync()`는 `result.returncode != 0`에만 의존했으므로, Task 4 Step 4의 negative-path 검증(잘못된 project number)이 실제로는 `agentos.log`에 아무것도 기록하지 못했을 것이라는 지적 → `_try_dashboard_sync()`를 `returncode != 0` **또는** 캡처된 출력에 `동기화 실패`/`Failed to sync` 텍스트 마커가 있는지로 판정하도록 수정(이 마커들은 `agentos/commands/dashboard.py`/`notifier.py`의 실제 실패 출력 문자열과 정확히 일치, "대시보드 미설정" skip 메시지와는 겹치지 않아 오탐 없음). Task 3 Step 3와 Task 4 Step 4 설명도 이 근거로 갱신.

수정 완료 후 Gate 0 재검토 → 통과. 3차 Gate 2 리뷰(위 수정 사항이 실제로 반영됐는지 재확인) 진행 예정.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
