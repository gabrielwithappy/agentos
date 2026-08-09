# AgentOS 부트스트랩 컨텍스트 안전장치 및 가시성 개선 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-25<br>
> reviewed: true (plan-reviewer PASS, principle-auditor PASS, usability-reviewer PASS — 증거: `.agents/traces/reviews/2026-07-25-agentos-bootstrap-context-safety-and-visibility/{plan-reviewer,principle-auditor,usability-reviewer}.json`)<br>
> implementation_started_at: 2026-07-25T00:00:00Z<br>
> implementation_completed_at: 2026-07-25T00:00:00Z<br>
> implementation_duration: (같은 세션 내 연속 구현)<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `2026-07-24-agentos-pi-bootstrap-context` 계획으로 구현된 AGENTS.md/CLAUDE.md 자동 로딩에, 조상 디렉토리 순회로 신뢰할 수 없는 상위 디렉토리의 악성 지침 파일을 그대로 시스템 프롬프트에 태울 수 있는 위험과, 파일 크기 제한이 없어 거대한 컨텍스트 파일이 매 세션 토큰 예산을 무한정 잠식할 수 있는 문제를 해결한다. hermes-agent(레퍼런스)의 실제 방어 설계를 근거로 삼는다.

**사용자 결과 요약:**
- 최종 결과: AGENTS.md/CLAUDE.md 내용에 프롬프트 인젝션으로 의심되는 패턴(예: "이전 지침을 무시하라", 알려진 C2 프레임워크 이름, 역할극 하이재킹 시도, 시스템 프롬프트 유출 유도)이 있으면 그 파일은 시스템 메시지에 원문 그대로 들어가지 않고 `[BLOCKED: <파일명> contained potential prompt injection (<탐지 항목>). Content not loaded.]` 문구로 대체된다. 사용자는 `/status`에서 어떤 파일이 차단됐는지, 어떤 패턴이 매칭됐는지 확인할 수 있다. 또한 컨텍스트 파일이 과도하게 크면(이번 범위는 고정 20,000자 캡 — 아래 "이번 범위에 포함하지 않는 것" 참조) 전체를 넣는 대신 앞부분+뒷부분만 남기고 "전체를 보려면 이 경로를 확인하라"는 안내가 삽입된다. **이 스캔은 정규식 기반 best-effort 완화 장치이지 보증이 아니다** — hermes-agent 자신도 이를 "advisory guard, not archival search"로 규정한다(패턴을 정교하게 우회하는 입력은 통과할 수 있음). 다만 시크릿 마스킹(`redact_text()`)과 마찬가지로 아무 방어도 없는 것보다는 명백히 낫다. **오탐으로 자신의 정상적인 파일이 차단된 경우의 복구 경로**: `/status`가 어떤 패턴 카테고리(예: `known_c2_framework`, `role_hijack` — 실제 매칭된 원문 문구 자체가 아니라 공격 유형 식별자)가 매칭됐는지 보여주므로, 이 계획이 나열한 예시 어휘(C2 프레임워크 이름, 역할극 하이재킹 문구 등)를 단서로 파일에서 해당 문구를 찾아 수정/삭제하면 다음 세션부터 정상 로드된다 — `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1`(부트스트랩 전체를 끄는 기존 opt-out)까지 갈 필요는 없는, 최소 단위의 복구 경로다.
- 대상 독자: AgentOS CLI/TUI로 반복 세션을 여는 개발자 및 프로젝트 유지관리자. 특히 신뢰할 수 없는 저장소를 클론해 작업하거나, 공유 모노레포/홈 디렉토리 상위에 다른 사람이 심어둔 `AGENTS.md`가 있을 수 있는 환경의 사용자.
- 일상 사용의 변화: 정상적인 `AGENTS.md`/`CLAUDE.md`(일반적인 프로젝트 지침 — "간결하게 답하라", "테스트를 먼저 실행하라" 등)는 지금처럼 아무 변화 없이 그대로 로드된다. 오직 실제 공격 패턴에 해당하는 어휘(알려진 C2 프레임워크 이름, 역할극 하이재킹 유도, 시스템 프롬프트 유출 유도, 고전적 "지침 무시" 문구 등 — 이번 범위인 `context`/`all` 스코프에 속하는 패턴만)가 포함된 파일만 차단되며, "you must"처럼 흔한 지시형 문장만으로는 절대 차단되지 않는다(오탐 방지 원칙, hermes-agent의 실사용 검증된 패턴 세트를 그대로 참고). **SSH 백도어 경로(`~/.ssh/authorized_keys` 등) 탐지는 이번 범위에 포함되지 않는다** — hermes-agent에서 이 패턴은 메모리 쓰기/스킬 설치 전용인 `strict` 스코프에 속하며, 이번 계획은 `strict` 스코프를 이식하지 않기 때문이다(아래 "이번 범위에 포함하지 않는 것" 참조).
- 바뀌지 않는 경계: `2026-07-24-agentos-pi-bootstrap-context`에서 만든 발견 규칙(조상 디렉토리 순회, 디렉토리당 첫 매치, opt-out 환경변수, 배너/`/status` 가시성)은 이번 계획에서 변경하지 않는다. `redact_text()` 시크릿 마스킹, `TRUSTED_SYSTEM_SOURCE` 신뢰 경계도 그대로 유지한다. 이번 계획은 `discover_context_files()`가 반환한 content를 `build_bootstrap_message()`가 조립하기 전 단계에 스캔/캐핑 레이어를 끼워 넣는 것으로 한정하며, 스킬 메타데이터(`discover_skills()`)나 `@`-include 지원은 이번 범위에 포함하지 않는다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 순수 정규식 패턴 매칭과 문자열 처리만 필요하며 네트워크 호출이 없다.
- 검증 근거: `agentos/conversation/bootstrap.py`(`2026-07-24-agentos-pi-bootstrap-context`로 신규 구현, 아직 커밋 전 — `discover_context_files()`/`build_bootstrap_message()`/`ContextFile` 확인 완료), `agentos/llm/redaction.py:24`(`redact_text()` — 기존 시크릿 마스킹, 이번 스캔과 병행 적용).
- **hermes-agent 레퍼런스 절대 경로**: `/home/gabriel/agent/prj-agent/agentos-workspace/references/hermes-agent`(Python, `agentos` 저장소와 형제 디렉토리, git submodule 아님, read-only 참고 자료). 핵심 근거 파일: `tools/threat_patterns.py`(284줄, 패턴 라이브러리 — `_PATTERNS` 리스트 63-135행, `INVISIBLE_CHARS` 141-159행, `_compile()`의 스코프 병합 로직 167-200행), `agent/prompt_builder.py`(`_scan_context_content` 50-66행 — 스캔 후 차단 로직, `_dynamic_context_file_max_chars` 1195-1228행 — 컨텍스트 윈도우 비례 캐핑, `_truncate_content` 1788-1826행 — head/tail truncation, `_record_truncation_warning`/`drain_truncation_warnings` 1230-1252행 — ContextVar 기반 경고 수집), `agent/system_prompt.py:539`(`agent._emit_status(warning)` — truncation 경고를 사용자 채널로 흘려보내는 지점), `run_agent.py:887`(`_emit_status()` — CLI에는 verbose/quiet 무관 항상 노출, 게이트웨이에는 `status_callback("lifecycle", ...)`). 상세 비교 분석은 `.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md`에 영속화되어 있다(리뷰어는 이 파일을 함께 참조할 것).
- 이 조사에서 pi(`/home/gabriel/agent/prj-agent/agentos-workspace/references/pi`)는 프롬프트 인젝션 스캔이나 동적 truncation을 지원하지 않음을 이미 확인했다(`2026-07-24-agentos-pi-bootstrap-context` 계획 문서 및 리서치 파일 참조) — 이번 계획은 pi가 아니라 hermes-agent의 설계를 근거로 한다.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거. 근거 리서치는 `.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md`(이미 존재, 갱신 불필요).
- Durable Result Surface: `agentos/conversation/bootstrap.py`(신규 `scan_context_content()`/`cap_context_content()` 또는 유사 함수, `build_bootstrap_message()`에서 호출), 신규 `agentos/conversation/threat_patterns.py`(패턴 라이브러리, hermes-agent `tools/threat_patterns.py` 구조를 Python으로 이식), `agentos/terminal/interaction.py`/`agentos/terminal/tui/app.py`(`/status`가 차단/잘림 이벤트를 보여주도록 확장), `docs/cli-reference.md`, `tests/test_conversation_bootstrap.py`(신규 테스트 케이스 추가), `tests/test_threat_patterns.py`(신규, 패턴 라이브러리 자체 단위 테스트).

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기 중 (사용자 지시에 따라 하네스 에이전트 핵심 리뷰로 진행)

**아키텍처:**
- **신규 `agentos/conversation/threat_patterns.py`**: hermes-agent의 `tools/threat_patterns.py` 구조를 그대로 이식하되 AgentOS 코드 스타일에 맞춘다.
  - `_PATTERNS: list[tuple[str, str, str]]` — `(regex, pattern_id, scope)` 튜플. `scope`는 `"all"`(모든 곳 적용) / `"context"`(컨텍스트 파일 — 경고만 기본, 이번 범위는 컨텍스트 파일 전용이므로 `strict` 스코프는 이식하지 않는다 — 아래 비목표 참조) 2단계만 우선 지원한다(`strict`는 메모리/스킬 설치 등 AgentOS에 아직 없는 기능에 대응하므로 이번 범위 밖).
  - 오탐 방지 원칙을 그대로 따른다: "you must"/"act as" 같은 흔한 지시형 문장은 패턴에 넣지 않고, C2 프레임워크 이름(Cobalt Strike, Sliver, Havoc, Metasploit 등)·역할극 하이재킹 유도·시스템 프롬프트 유출 유도처럼 명확히 공격 전용인 어휘에만 앵커링한다. **SSH 백도어 경로(`authorized_keys`, `~/.ssh` 등)는 hermes에서 `strict` 스코프(메모리 쓰기/스킬 설치 전용)에 속하므로 이번 범위(`context`/`all` 스코프만 이식)에는 포함하지 않는다** — 아래 "이번 범위에 포함하지 않는 것" 참조.
  - 정규식 backtracking 방어를 위해 `(?:\w+\s+){0,8}` 형태의 bounded filler만 사용(무제한 `*` 반복 금지) — hermes-agent가 이미 이 이유로 패턴을 리팩터한 전례(`_FILLER` 정의의 주석)를 그대로 따른다.
  - `INVISIBLE_CHARS`(zero-width space/joiner, bidirectional override/isolate 등)도 이식해 비가시 유니코드로 지침을 숨기는 공격을 탐지한다.
  - `MAX_SCAN_CHARS`(hermes 기본 65,536)로 스캔 대상 길이를 제한해 정규식 스캔 자체가 DoS 벡터가 되지 않게 한다.
  - `scan_for_threats(content: str, scope: str) -> list[str]` — 매칭된 `pattern_id` 목록을 반환하는 순수 함수(hermes와 동일한 인터페이스 감각).
- **`agentos/conversation/bootstrap.py` 수정**:
  - `build_bootstrap_message()`가 `redact_text()` 적용 **이전에** 각 `ContextFile.content`에 대해 `scan_for_threats(content, scope="context")`를 호출한다. 위협이 발견되면 hermes와 동일하게 `f"[BLOCKED: {path.name} contained potential prompt injection ({', '.join(findings)}). Content not loaded.]"`로 그 파일의 content를 대체하고, `ContextFile`에 `blocked: bool`/`blocked_reasons: list[str]` 필드를 추가해 `/status`가 참조할 수 있게 한다(현재 `skipped`/`skip_reason`과 별개 필드 — "읽기 실패"와 "내용이 위험해서 차단"은 사용자에게 다른 의미이므로 구분).
  - 파일 크기 캐핑: hermes의 `_dynamic_context_file_max_chars()`를 참고해, `ConversationRuntime`이 이미 알고 있는 provider/model 정보로부터 컨텍스트 윈도우 크기를 얻을 수 있는 경로가 있는지 먼저 확인한다(`agentos/llm/registry.py` 또는 provider 메타데이터). 없으면 hermes와 동일하게 고정 20,000자 floor로 시작하고, 향후 model registry에 context_length가 노출되면 그 값에 비례해 확장하는 구조로 설계한다(이번 범위는 고정 캡으로 시작 — 아래 비목표 참조). 캡을 넘으면 head/tail만 남기고 `"[...truncated {filename}: kept {head}+{tail} of {total} chars. 전체가 필요하면 이 경로를 확인하라: {path}]"` 형태의 마커를 삽입한다.
  - 스캔/캐핑 결과(차단됨/잘림)를 `ContextFile`의 필드로 반환해, 호출부(`interaction.py`/`tui/app.py`)가 이미 구현된 `/status` 확장에 자연스럽게 이어붙일 수 있게 한다(기존 `bootstrap_context_paths`/`bootstrap_skill_names` metadata 패턴과 동일한 방식으로 `bootstrap_blocked_files`/`bootstrap_truncated_files`를 `ConversationMessage.metadata`에 추가).
- **`/status` 확장**: `agentos/terminal/interaction.py`와 `agentos/terminal/tui/app.py`의 기존 부트스트랩 상태 출력(`_bootstrap_status_text()` 등, `2026-07-24-agentos-pi-bootstrap-context`에서 이미 구현)에 "차단된 파일" 및 "잘린 파일" 섹션을 추가한다. hermes와 달리 AgentOS는 이미 "항상 배너 + `/status` 전체 노출" 방식을 채택했으므로(리서치 파일의 "사용자에게 로드 정보를 전달하는 방식" 섹션 참조), 차단/잘림도 동일한 상시 가시성 철학을 유지한다 — hermes처럼 "문제 있을 때만 알림"으로 축소하지 않는다.

**기술 스택:**
- Python 3.12+, 표준 라이브러리 `re`(정규식), 기존 `agentos.conversation`/`agentos.llm.redaction` 모듈, pytest. 신규 외부 패키지 없음.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Gate 2 리뷰 3종(plan-reviewer/principle-auditor/usability-reviewer) 모두 PASS. 구현 시작 대기 |
| 완료됨 | hermes-agent `threat_patterns.py`/`prompt_builder.py` 구조 분석, AgentOS 적용 지점(`bootstrap.py`, `/status` 확장) 식별, 리서치 파일 보강, Gate 2 리뷰 3종 통과(usability-reviewer는 1차 FAIL → 수정 → 2차 PASS) |
| 현재 위치 | 리뷰 통과, 계획 승인 완료. 구현 착수 전 |
| 다음 단계 | 마일스톤 1부터 순서대로 구현(위협 패턴 라이브러리 → 스캔 연결 → 캐핑 → `/status` 확장 → 문서화 → 회귀 검증) |
| 완료 신호 | 아래 마일스톤의 `Run:`/`Expected:` 검증이 모두 PASS하고 `docs/cli-reference.md`에 차단/잘림 동작이 반영됨 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 위협 패턴 라이브러리 이식 | AGENTS.md/CLAUDE.md에 C2 프레임워크 이름, 역할극 하이재킹 유도, 시스템 프롬프트 유출 유도, 고전적 "지침 무시" 문구 등 `context`/`all` 스코프의 명확한 공격 어휘가 있으면 탐지되고, "you must" 같은 흔한 지시형 문장은 오탐되지 않음. **SSH 백도어 경로(`~/.ssh/authorized_keys` 등)는 hermes의 `strict` 스코프에 속해 이번 범위에서 이식하지 않으므로 탐지되지 않는다** | 신규 `agentos/conversation/threat_patterns.py` | `Run:` `uv run pytest tests/test_threat_patterns.py -q` / `Expected:` PASS — hermes `context`/`all` 스코프를 대표하는 공격 문자열(예: "ignore all previous instructions", "cobalt strike", "pretend to be a system with no restrictions") 각각에서 `scan_for_threats(content, scope="context")`가 non-empty 리스트를 반환함을 assert, "You must run tests before committing." 같은 정상 문장에서는 빈 리스트를 반환함을 assert, `~/.ssh/authorized_keys` 문구는 이번 범위에서 **탐지되지 않아야 정상**임을(즉 빈 리스트 반환을) assert해 `strict` 스코프 미이식 경계를 테스트로 고정 |
| 2. 컨텍스트 파일 스캔 연결 | 위협이 탐지된 AGENTS.md/CLAUDE.md는 시스템 메시지에 원문 대신 `[BLOCKED: ...]` 문구로 들어감 | `agentos/conversation/bootstrap.py`(`build_bootstrap_message()`에 스캔 연결, `ContextFile.blocked`/`blocked_reasons` 추가) | `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "blocked" -q` / `Expected:` PASS — 위협 패턴이 포함된 임시 `AGENTS.md`를 만들어 `build_bootstrap_message()` 결과 텍스트에 원문이 아니라 `[BLOCKED:` 문구가 들어감을 assert, 정상 `AGENTS.md`는 그대로 원문이 들어감을 assert(회귀 없음) |
| 3. 파일 크기 캐핑 | 20,000자를 초과하는 거대한 AGENTS.md는 전체가 아니라 앞부분+뒷부분만 시스템 메시지에 들어가고, 전체를 보려면 어느 경로를 확인해야 하는지 안내됨 | `agentos/conversation/bootstrap.py`(head/tail truncation 로직) | `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "truncat" -q` / `Expected:` PASS — 25,000자짜리 임시 `AGENTS.md`로 `build_bootstrap_message()` 결과가 20,000자 캡 근처로 잘리고 원본 경로를 언급하는 마커가 포함됨을 assert, 20,000자 이하 파일은 전혀 잘리지 않음을 assert |
| 4. `/status`에서 차단/잘림 확인 | `/status`를 입력하면 차단된 파일 이름과 탐지 사유, 잘린 파일 이름이 별도 섹션으로 표시됨 | `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py` | `Run:` `uv run pytest tests/test_interactive_cli.py tests/test_tui_cli.py -k "blocked_status or truncated_status" -q` / `Expected:` PASS — 위협 패턴이 포함된 AGENTS.md로 세션을 시작해 `/status` 출력에 차단 파일명과 사유가 나타남을 assert |
| 5. 문서화 | `docs/cli-reference.md`에 차단/잘림 동작과 그 이유(보안, 토큰 예산)가 설명됨 | `docs/cli-reference.md` | `Run:` `grep -n "BLOCKED\|prompt injection\|truncat" docs/cli-reference.md` / `Expected:` 관련 설명 줄이 출력됨 |
| 6. 전체 회귀 검증 | 기존 부트스트랩 기능(발견, 배너, opt-out, 세션 지속성)이 깨지지 않음 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` `2026-07-24-agentos-pi-bootstrap-context` 완료 시점 통과 건수(315) 이상 PASS, 신규 실패 없음. `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` / `Expected:` PASS(secret redaction 회귀 없음, 이번 스캔이 redaction 순서/경로를 깨지 않음을 확인) |

## 이번 범위에 포함하지 않는 것 (명시적 제외)

참조: `.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md`

- **`strict` 스코프 패턴(메모리 쓰기/스킬 설치 차단)** — AgentOS에는 hermes의 메모리 시스템(`SOUL.md`/`USER.md` 쓰기)이나 스킬 설치 시점 스캔이 아직 없다. 이번 범위는 컨텍스트 파일(`context` 스코프에 해당하는 패턴)에만 적용하고, 스킬 설치(`agentos skill install`) 시점 스캔은 별도 계획에서 다룬다.
- **모델 컨텍스트 윈도우에 실제로 비례하는 동적 캡** — hermes는 `context_length`를 실시간으로 읽어 20K~500K 사이로 캡을 조정하지만, AgentOS의 provider/model registry에 context_length가 아직 노출되어 있는지 확인이 필요하다. 이번 범위는 hermes의 floor 값(20,000자) 고정 캡으로 시작하고, model registry 연동은 그 값이 실제로 존재함을 확인한 뒤 후속 계획에서 다룬다.
- **`config.yaml` 유사 사용자 오버라이드(`context_file_max_chars` 커스텀 설정)** — 이번 범위는 고정 캡만 제공하고, 사용자가 직접 캡을 조정하는 설정 항목은 실사용 피드백을 본 뒤 별도로 다룬다.
- **`@`-include 재귀 전개** — `2026-07-24-agentos-pi-bootstrap-context`에서 이미 별도 후속 계획으로 분리하기로 결정된 사항이며, 이번 계획과 무관하다(pi도 hermes도 미지원 확인 완료).
- **hermes의 "문제 있을 때만 알림" 철학 채택** — AgentOS는 이미 "항상 배너 + `/status` 전체 노출" 방식을 채택했고, 이번 계획도 차단/잘림 정보를 동일하게 상시 노출한다. hermes처럼 평상시 침묵하다 문제 시에만 알리는 방식으로 축소하지 않는다(위 아키텍처 섹션에 근거 명시).

## 리뷰 반영 이력
- 초안 작성 — 2026-07-25. `2026-07-24-agentos-pi-bootstrap-context` 완료 후 실사용 중 발견된 갭(조상 디렉토리 순회로 인한 인젝션 위험, 파일 크기 무제한)을 계기로, hermes-agent(`/home/gabriel/agent/prj-agent/agentos-workspace/references/hermes-agent`)의 `tools/threat_patterns.py`/`agent/prompt_builder.py`/`agent/system_prompt.py`를 직접 읽고 패턴 라이브러리 설계와 사용자 가시성 철학을 조사, `.agents/traces/research/2026-07-24-agentos-pi-bootstrap-context-hermes-comparison.md`에 상세 기록 후 이 계획에 반영.
- `plan-reviewer` 리뷰 — 2026-07-25, PASS. hermes-agent/AgentOS 소스 인용 라인 전체 대조 검증, 리서치 파일 재도출 없이 정확히 참조 확인.
- `principle-auditor` 리뷰 — 2026-07-25, PASS(승인). Simplicity 스코프다운(고정 캡, `strict` 스코프 미이식)이 근거 있음을 `agentos/llm/registry.py`에 `context_length` 필드 부재를 직접 grep으로 확인해 검증. 비차단 권고 1건: 정규식 스캔이 "보증"이 아니라 "best-effort mitigation"임을 계획에 명시할 것 → "사용자 결과 요약"에 hermes-agent의 "advisory guard, not archival search" 표현을 인용해 반영함(위 수정).
- 1차 `usability-reviewer` 리뷰 — 2026-07-25, FAIL. 핵심 사유: 마일스톤 1의 검증 예시와 "사용자 결과 요약"/아키텍처 섹션이 `~/.ssh/authorized_keys` 같은 SSH 백도어 경로를 이번 범위(`context`/`all` 스코프)에서 탐지되는 예시로 들었으나, 실제로 이 패턴은 hermes-agent에서 `strict` 스코프(메모리 쓰기/스킬 설치 전용) 소속이고 이 계획은 `strict` 스코프를 이식하지 않기로 이미 결정했다 — 즉 계획이 스스로의 범위 결정과 모순되는 탐지 동작을 사용자에게 약속하고 있었음. 부차 사유: 오탐으로 정상 파일이 차단됐을 때 `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1`(전체 opt-out) 외의 복구 경로가 명시되어 있지 않음. → SSH 관련 예시를 "사용자 결과 요약"(20행)/아키텍처(38행)/마일스톤 1(68행) 세 곳 모두에서 제거하고 `context`/`all` 스코프에 실제로 존재하는 예시(C2 프레임워크 이름, 역할극 하이재킹, 프롬프트 유출 유도, 고전적 지침 무시 문구)로 교체했으며, 마일스톤 1 검증에 "`~/.ssh/authorized_keys` 문구는 이번 범위에서 탐지되지 않아야 정상"이라는 negative assertion을 추가해 `strict` 스코프 미이식 경계를 테스트로 고정함. 복구 경로는 "사용자 결과 요약"에 "매칭된 문구를 수정/삭제하면 다음 세션부터 정상 로드된다"는 최소 단위 복구 안내를 추가해 해소함.
- 2차 `usability-reviewer` 재검토 — 2026-07-25, PASS. SSH 스코프 모순 수정과 복구 경로 추가가 4개 섹션(사용자 결과 요약/아키텍처/마일스톤 1/리뷰 반영 이력) 모두에서 일관되게 반영됐음을 확인. 비차단 권고 1건: "사용자 결과 요약"이 `/status`가 "매칭된 문구"를 보여준다고 했으나 아키텍처(`blocked_reasons`)는 `pattern_id` 카테고리 라벨만 반환하도록 설계되어 있어 정밀도 차이가 있음 → "실제 매칭된 원문이 아니라 공격 유형 식별자"임을 명시하고 계획이 나열한 예시 어휘를 단서로 찾도록 문구를 정밀화함(위 수정).

## 구현 결과

전체 6개 마일스톤 순서대로 구현, 모든 `Run:`/`Expected:` 검증 PASS:

1. **`agentos/conversation/threat_patterns.py`(신규)** — hermes-agent `tools/threat_patterns.py`에서 `all`/`context` 스코프 패턴만 이식(`strict` 스코프인 SSH 백도어/시크릿/exfil-URL 패턴은 제외). `scan_for_threats(content, scope)`, `INVISIBLE_CHARS`, `MAX_SCAN_CHARS=65,536`, bounded filler(`(?:\w+\s+){0,8}`) 포함. `Run:` `uv run pytest tests/test_threat_patterns.py -q` → `Expected:` PASS → **결과: 7 passed**(오탐 방지 케이스, SSH negative assertion 포함).
2. **`agentos/conversation/bootstrap.py` 수정** — `ContextFile`에 `blocked`/`blocked_reasons`/`truncated` 필드 추가. `scan_and_cap_context_file()`이 `redact_text()` 이전에 스캔을 수행하고, 위협 발견 시 `[BLOCKED: <filename> contained potential prompt injection (...). Content not loaded.]`로 치환. `build_bootstrap_message()`의 `metadata`에 `bootstrap_blocked_files`/`bootstrap_truncated_files` 추가. `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "blocked" -q` → **PASS**(1 passed).
3. **파일 크기 캐핑** — `MAX_CONTEXT_FILE_CHARS=20,000`(hermes floor 고정값), head 12,000/tail 6,000자만 남기고 `[...truncated {filename}: kept {head}+{tail} of {total} chars. See full file at: {path}]` 마커 삽입. `Run:` `uv run pytest tests/test_conversation_bootstrap.py -k "truncat" -q` → **PASS**(2 passed).
4. **`/status` 확장** — `agentos/terminal/interaction.py`와 `agentos/terminal/tui/app.py` 양쪽에 `bootstrap_blocked_files`/`bootstrap_truncated_files` 섹션(경로 + 매칭된 pattern_id) 추가. `Run:` `uv run pytest tests/test_interactive_cli.py tests/test_tui_cli.py -k "blocked_status or truncated_status" -q` → **PASS**(2 passed).
5. **문서화** — `docs/cli-reference.md`에 "Prompt-injection scanning and size caps" 섹션 신설(차단 예시, 복구 경로, 캐핑 동작 설명). `Run:` `grep -n "BLOCKED\|prompt injection\|truncat" docs/cli-reference.md` → 관련 줄 출력 확인.
6. **전체 회귀 검증** — `Run:` `uv run pytest tests/ -q` → **328 passed**(베이스라인 315 + 신규 13, 실패 없음). `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q` → **16 passed**(secret redaction 회귀 없음).

**계획 대비 추가 작업**: `config/public-boundary.json`에 신규 `agentos/conversation/threat_patterns.py`/`tests/test_threat_patterns.py` 경로를 allowlist에 등록(계획 문서에는 명시되지 않았으나 공개 저장소 boundary 스캔 통과에 필요). `Run:` `python3 scripts/security/scan-public-boundary.py` → `PASS public-boundary worktree=318 staged=14`.

**이전 계획(`2026-07-24-agentos-pi-bootstrap-context`)의 미커밋 구현**도 이번 세션에서 함께 확인·유지됨(`agentos/conversation/bootstrap.py` 기본 구조, `persistence.py`/`sessions.py`/`tui/app.py`/`interaction.py`의 부트스트랩 배너·상태 로직) — 이번 계획은 그 위에 스캔/캐핑 레이어만 추가.

**구현 완료 후 사용자 재확인 과정에서 발견한 갭(추가 수정)**: `2026-07-24-agentos-pi-bootstrap-context`가 legacy interactive fallback(`interaction.py`)에는 세션 시작 시 `_print_bootstrap_banner()`를 붙였지만, 실제 기본 진입점인 TUI(`agentos/terminal/tui/app.py`의 `AgentOSTui`/`run_tui()`)에는 시작 배너가 전혀 없어 사용자가 `/status`를 직접 입력하기 전까지는 어떤 컨텍스트가 로드됐는지 전혀 알 수 없었음 — 이번 계획의 "항상 배너 + `/status` 전체 노출" 상시 가시성 철학(아키텍처 섹션 명시)에 위배되는 기존 갭. `AgentOSTui.compose()`가 만드는 초기 transcript 텍스트에 `_bootstrap_banner_text()`(신규, `_print_bootstrap_banner()`와 동일 문구 포맷 재사용)를 붙여 세션 시작과 동시에 "부트스트랩 컨텍스트: N개 파일, M개 스킬 로드됨 — /status로 확인" 요약이 보이도록 수정, 차단/잘림 파일이 있으면 "(차단 N건, 잘림 M건)"을 요약에 덧붙임. `Run:` `uv run pytest tests/test_tui_cli.py -k "startup_shows_bootstrap or startup_banner_reports" -q` → **PASS**(2 passed, 신규 테스트: 정상 로드 시 배너에 "부트스트랩 컨텍스트"/"1개 파일"/"/status" 노출 확인, 위협 패턴 파일 로드 시 배너에 "차단 1건" 노출 확인). `Run:` `uv run pytest tests/test_tui_cli.py -q` → **PASS**(84 passed, opt-out 시 배너 미노출 기존 테스트 포함 회귀 없음). `Run:` `uv run pytest tests/ -q` → **330 passed**(전체 회귀 없음).

**후속 확장: `@`-include 재귀 전개 구현(2026-07-25, 사용자 요청)**: 이번 계획의 "이번 범위에 포함하지 않는 것"에서 명시적으로 제외됐던 `@`-include(이 저장소 자신의 `CLAUDE.md`가 `@AGENTS.md`/`@.agents/vendors/claude.md` 형태로 사용 중인 Claude Code 고유 문법)를 사용자 요청으로 구현. pi/hermes-agent 둘 다 이 문법을 지원하지 않아(기존 리서치로 확인됨) 이식이 아니라 신규 설계였음. 핵심 설계 결정(사용자 확인): include가 참조 가능한 경로 범위를 "발견된 컨텍스트 파일이 위치한 디렉토리 자신과 그 하위"로 제한(공식 Claude Code의 `@~/anything`/절대경로 지원보다 좁음) — 신뢰할 수 없는 조상 디렉토리의 `AGENTS.md`가 `@~/.ssh/id_rsa` 같은 줄로 임의 파일을 시스템 프롬프트에 유출시키는 것을 막기 위함(이번 계획 전체의 위협 모델과 동일선상).

구현: `agentos/conversation/bootstrap.py`에 `_expand_includes()`(재귀 전개, `MAX_INCLUDE_DEPTH=5`) 신규 추가, `_find_context_file_in_dir()`에서 파일을 읽은 직후(스캔/캐핑 이전) 호출해 확장된 텍스트가 이후 위협 스캔·크기 캐핑 대상이 되도록 배치. 안전장치 4종: (1) 경로 탈출 차단 — 상대경로(`../`)든 절대경로(`/etc/hostname`)든 신뢰 루트를 벗어나면 `[INCLUDE_BLOCKED: ... escapes trusted context root]`, (2) 순환 참조 차단 — `visited` 집합으로 재방문 시 `[INCLUDE_SKIPPED: ... circular reference]`, (3) 깊이 제한 — `MAX_INCLUDE_DEPTH` 초과 시 `[INCLUDE_BLOCKED: ... exceeds max include depth]`, (4) 존재하지 않는/읽기 실패 파일 — 예외를 던지지 않고 `[INCLUDE_BLOCKED: ... could not be read]`로 치환해 나머지 부트스트랩을 막지 않음. `docs/cli-reference.md`에 "`@`-include expansion" 섹션 신설. artifact=agentos/conversation/bootstrap.py,docs/cli-reference.md,tests/test_conversation_bootstrap.py verification=PASS `uv run pytest tests/test_conversation_bootstrap.py -k "include" -q`(7 passed — 정상 확장, 상대/절대경로 탈출 차단, 순환 참조 스킵, 깊이 제한, 존재하지 않는 파일); PASS `uv run pytest tests/ -q`(336 passed, 베이스라인 330 대비 신규 7건, 회귀 없음); PASS `python3 scripts/security/scan-public-boundary.py`(worktree=318, staged=14); 수동 재현으로 이 저장소 자신의 `CLAUDE.md`(`@AGENTS.md`+`@.agents/vendors/claude.md`)가 원본 37자 → 확장 후 8,845자로 정상 전개됨을 직접 확인(단, 실제 세션 부트스트랩에서는 이 저장소 루트에 `AGENTS.md`가 이미 있어 디렉토리당 첫 매치 규칙상 `CLAUDE.md` 자체는 선택되지 않음 — 이는 include 기능과 무관한 기존 우선순위 동작).

## 사용 방법

- 평상시: `AGENTS.md`/`CLAUDE.md`가 정상 문구만 담고 있으면 지금까지와 동일하게 그대로 로드된다.
- 위협 패턴이 매칭되면 해당 파일의 content가 `[BLOCKED: ...]`로 치환되어 시스템 메시지에 들어가고, `/status`에서 파일명과 매칭된 pattern_id를 확인할 수 있다.
- 20,000자를 넘는 파일은 앞부분+뒷부분만 남고 원본 경로를 안내하는 마커가 삽입되며, `/status`의 `bootstrap_truncated_files`에서 확인 가능하다.
- 오탐 복구: `/status`가 보여주는 pattern_id(예: `known_c2_framework`)를 단서로 해당 문구를 파일에서 찾아 수정하면 다음 세션부터 정상 로드된다. `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1`(전체 opt-out)까지 갈 필요 없음.

## 아카이브 결정

2026-07-26 아카이브. Gate 2 리뷰 3종(plan-reviewer/principle-auditor/usability-reviewer) 모두 PASS(증거: `.agents/traces/reviews/2026-07-25-agentos-bootstrap-context-safety-and-visibility/`), 6개 마일스톤 및 후속 확장(TUI 시작 배너, `@`-include 재귀 전개) `Run:`/`Expected:` 검증 전부 PASS, 전체 테스트 스위트 336 passed, public-boundary 스캔 PASS로 완료 확인. 사용자 확인 후 상태를 '완료'로 갱신하고 `plan_lifecycle.py archive`로 `active/` → `archive/` 이동.
