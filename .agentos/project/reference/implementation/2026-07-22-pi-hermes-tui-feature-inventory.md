# pi · hermes TUI 기능 인벤토리 및 AgentOS 이식 매핑

- Expansion Trigger: Phase 3 계획 수립 전 pi와 hermes TUI 전체 기능 인벤토리 요구 (§3.3 Durable Knowledge Gate — Phase 2 이후 재참조 필요성 높음)
- parent root doc: `03-system-contract.md`
- reason for creation: Phase 1·2 이식 이후 미구현 항목들을 Phase 3+ 계획에서 재조사 없이 재참조하기 위함. Phase 2 closeout에서 확인된 남은 격차와 새로 발견된 hermes 패턴을 단일 문서로 통합.
- owner: AgentOS TUI 구현 파트
- freshness rule: pi 또는 hermes 소스가 크게 변경되거나 AgentOS TUI가 새로운 Phase를 완료할 때 해당 섹션을 갱신.
- status: 현재 (Current) — 2026-07-22 신규 작성
- source evidence:
  - `references/pi/packages/tui/src/` (16개 파일)
  - `references/pi/packages/coding-agent/src/modes/interactive/` (components/ 40개 파일 포함)
  - `references/hermes-agent/ui-tui/src/` (components/ 28개 파일 포함)
- links back to 요구사항, decisions, risks, or verification:
  - `.agentos/project/reference/implementation/2026-07-21-pi-tui-architecture-and-code-analysis.md` (이전 인벤토리 — Phase 1·2 범위)
  - `.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase2.md` (Phase 2 closeout)
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, or reviewer authority

---

## 요약: AgentOS 현재 TUI 구현 상태 (2026-07-22 기준)

Phase 1·2를 거쳐 AgentOS TUI에 구현된 기능:

| 기능 | 파일 | 상태 |
|------|------|------|
| 키보드 단축키 헬퍼 (`/hotkeys`) | `app.py`, `commands.py` | 완료 |
| 테마 전환기 (`/theme`) | `widgets.py` (ThemeScreen), `commands.py` | 완료 |
| 푸터 git 브랜치 + 사용량 | `state.py` (TuiStatus), `widgets.py` (StatusFooter) | 완료 |
| Tool call 시각적 테두리 | `widgets.py` (ChatMessage CSS) | 완료 |
| Reasoning/tool 이벤트 타입 | `llm/types.py`, `renderers.py` | 완료 |
| 스트리밍 취소 / 로딩 인디케이터 | `app.py` (Worker.cancel + `_loading_message`) | 완료 |
| `parent_turn_id` 분기 데이터 모델 | `terminal/events.py` | 완료 |
| `/tree` ASCII 분기 탐색기 | `renderers.py` (render_turn_tree) | 완료 |
| 도구별 커스텀 렌더러 (`TOOL_RENDERERS`) | `renderers.py` | 완료 (아키텍처 + mock 예시) |
| `/tools`, `/usage`, `/clear`, `/exit` | `commands.py`, `app.py` | 완료 |

---

## 1. pi TUI — Phase 3 이후 미구현 후보 (상세)

### 1.1 분기 생성 UI (Branch Fork UI)
- **pi 구현:** `interactive-mode.ts`에서 사용자가 이전 턴을 선택하고 새 메시지를 보내면 새 분기가 생성됨. `SessionSelectorComponent`의 포커스/키보드 탐색으로 분기 진입점 제어.
- **hermes 유사 패턴:** `spawnHistoryStore.ts` — 서브에이전트 스폰 이력을 저장하며, 부모-자식 관계를 선형이 아닌 트리로 관리.
- **AgentOS 현황:** `parent_turn_id` 데이터 모델은 준비됨. 분기를 **만드는** UI(이전 턴으로 되돌아가 재입력)만 없음.
- **구현 비용:** 중(Medium) — `Transcript` 위젯에서 과거 `ChatMessage`를 클릭/선택하는 이벤트 처리와 `new_turn_id` + `parent_turn_id` 연결 로직이 필요.
- **선행 조건:** 없음 (데이터 모델 완료).
- **추정 난이도:** ★★★☆☆

### 1.2 고도화된 Diff 렌더러
- **pi 구현:** `diff.ts` — `unified` 또는 `side-by-side` 형식으로 파일 변경사항을 색상 하이라이팅하여 렌더링. 삭제 라인은 빨간색, 추가 라인은 녹색.
- **hermes 유사 패턴:** 없음 (hermes는 코드 편집 도구 없음).
- **AgentOS 현황:** `render_event()`에서 `tool_result`를 평문으로 렌더링하는 것 외에 diff 표현 없음.
- **선행 조건:** AgentOS에 파일 수정 도구(write_file, apply_patch 등)가 먼저 추가되어야 활용처가 생김. 현재는 활용처 없음.
- **추정 난이도:** ★★☆☆☆ (렌더러 자체는 쉬움; 활용처 마련이 선행 조건)

### 1.3 이미지 프로토콜 지원 (Kitty / Sixel)
- **pi 구현:** `terminal-image.ts` — Kitty Image Protocol을 지원하여 터미널 내 이미지 인라인 표시. 이미지 크기 감지, 청크 전송, 픽셀 정렬 처리.
- **hermes 유사 패턴:** `appLayout.tsx`의 `PetPane` — Kitty placeholder(`\u{10eeee}`)로 이미지 공간 예약. `petSprite.tsx`에서 애니메이션 마스코트 이미지 표시.
- **AgentOS 현황:** 없음.
- **선행 조건:** 터미널 환경 감지 (`$TERM=xterm-kitty` 확인), Textual의 Sixel 지원 버전 확인 필요.
- **추정 난이도:** ★★★★☆ (터미널 호환성 이슈 큼)

### 1.4 자동완성 (Autocomplete)
- **pi 구현:** `autocomplete.ts` (23,208 bytes) + `fuzzy.ts` — 슬래시 커맨드, 파일 경로, 멘션(@)에 대한 퍼지 검색 기반 자동완성 드롭다운.
- **AgentOS 현황:** `/` 입력 시 `CommandPaletteScreen` 모달이 열리나, 퍼지 검색 없음. `matching_commands()`는 단순 prefix/substring 매칭.
- **hermes 패턴:** `createSlashHandler.ts`의 카탈로그 alias 기반 자동완성. 정확 매치 → prefix 매치 → 모호성 경고 순으로 처리.
- **구현 방향:** 현재 `CommandPaletteScreen`에서 `OptionList` 위젯을 실시간 필터링으로 교체. 퍼지 매칭 라이브러리(`thefuzz` 등) 추가 또는 직접 구현.
- **추정 난이도:** ★★★☆☆

### 1.5 모델 선택기 (`/model`)
- **pi 구현:** `model-selector.ts` (12,320 bytes) — 실시간 검색, 스코프 필터(All/Scoped), 선택 시 세션에 적용.
- **hermes 패턴:** `modelPicker.tsx` (21,666 bytes) — 모델 목록 + 검색 입력 + 스크롤 가능한 리스트 오버레이.
- **AgentOS 현황:** `--provider` CLI 인수로만 지정 가능. 세션 중 전환 불가.
- **선행 조건:** LLM provider 런타임 스위칭 지원. 현재 `stream_once(provider=...)` 형태이므로 세션 내 provider 변경은 `app.py`의 `self.provider` 업데이트 + 이후 턴 호출만으로 가능.
- **추정 난이도:** ★★★☆☆

### 1.6 설정 관리 UI (`/settings`)
- **pi 구현:** `settings-selector.ts` (26,595 bytes), `settings-list.ts` (7,905 bytes) — 터미널 내 설정 편집기 (key-value 목록, 토글, 범위 슬라이더).
- **hermes 패턴:** `useConfigSync.ts` (9,273 bytes) — 게이트웨이로부터 config를 주기적으로 동기화하고 변경 시 재반영.
- **AgentOS 현황:** 없음. 설정은 CLI 인수 + 환경변수로만 가능.
- **추정 난이도:** ★★★★☆

### 1.7 세션 압축 (Compaction) 인디케이터
- **pi 구현:** `compaction-summary-message.ts` — context window가 가득 찼을 때 자동 압축이 일어났음을 알리는 시스템 메시지.
- **hermes 패턴:** `trajectory_compressor.py` — 긴 대화 이력을 요약/압축하는 서버사이드 로직.
- **AgentOS 현황:** context 압축 로직 없음. 관련 기능이 추후 추가될 경우 인디케이터 표시 필요.
- **추정 난이도:** ★★☆☆☆ (UI 측만 보면 쉬움; 백엔드 압축 로직이 선행 조건)

---

## 2. hermes TUI — AgentOS에서 참고할 추가 패턴

### 2.1 인디케이터 스타일 선택 (`kaomoji` / `emoji` / `ascii` / `unicode`)
- **hermes 구현:** `appChrome.tsx`의 `renderIndicator()` — 4가지 스타일(kaomoji 얼굴 회전, emoji 이모지, ascii 스피너, unicode 브라이유 스피너). 사용자 설정으로 변경 가능.
- **AgentOS 현황:** `_loading_message`에 `Thinking...` 고정 텍스트 표시.
- **구현 방향:** `ThinkingIndicator` 위젯에 스피너 스타일 옵션 추가. Textual의 `LoadingIndicator` 대신 커스텀 위젯으로 교체하여 스타일 선택 지원.
- **추정 난이도:** ★★☆☆☆

### 2.2 알림 배너 (Notice / Toast)
- **hermes 구현:** `interfaces.ts`의 `Notice` 타입 — `sticky` (상시 표시) / `ttl` (N초 후 사라짐) 두 종류. 레벨별 색상 (`error`=빨강, `warn`=노랑, `info`=파랑, `success`=초록).
- **AgentOS 현황:** 오류는 `ChatMessage`로 대화창에 추가됨. 별도 알림 배너 없음.
- **구현 방향:** Textual의 내장 `app.notify("message", severity="error")` 호출로 즉시 구현 가능.
- **추정 난이도:** ★☆☆☆☆

### 2.3 서브에이전트 트리 시각화 (Spawn History)
- **hermes 구현:** `thinking.tsx`의 `buildSubagentTree()` — 서브에이전트 호출 깊이, 토큰 사용량, Hotness(부하) 표시. 브라이유 스피너로 진행 중 서브에이전트 표시.
- **AgentOS 현황:** 없음. AgentOS는 단일 에이전트 아키텍처.
- **선행 조건:** 멀티에이전트 오케스트레이션 지원이 먼저 필요. 단기 이식 후보 아님.
- **추정 난이도:** ★★★★★

### 2.4 텍스트 입력 고급 기능 (textInput.tsx)
- **hermes 구현:** `textInput.tsx` (1,441 lines) — 멀티라인 입력, 선택 영역 복사(Shift+Click), 클립보드 읽기/쓰기, IME 지원, 음성 입력 토글키, grapheme 단위 커서 이동.
- **AgentOS 현황:** `Composer`(TextArea 기반)에서 기본 멀티라인, 단축키(Ctrl+K/U/W/Y/Z) 지원. **[Phase 4 완료]** Composer의 `Ctrl+C`/`Ctrl+V`는 Textual 기본 클립보드 연동으로 이미 동작; 대화 이력 메시지는 `Tab`/`Shift+Tab` 포커스 이동 + `c` 키로 시스템 클립보드(OSC 52)에 복사 가능해짐(`agentos/terminal/tui/{widgets,app}.py`).
- **구현 방향:** Textual의 `TextArea`는 자체 IME/유니코드를 지원. 클립보드 통합은 Textual 내장 `App.copy_to_clipboard()`(OSC 52, `textual>=6.0.0`으로 이미 충족)로 구현 완료 — 별도 `pyperclip` 등 신규 패키지 불필요했음. 남은 항목: 음성 입력 토글키(별도 STT 서브시스템 필요, 미착수), grapheme 단위 커서 이동 전면 재작업(미착수).
- **추정 난이도:** ★★☆☆☆ (클립보드 하위 항목은 Phase 4로 해소됨)

### 2.5 스트리밍 마크다운 점진적 렌더링
- **hermes 구현:** `streamingMarkdown.tsx` (6,348 bytes) — 스트리밍 중에도 완성된 마크다운 블록(헤딩, 코드, 테이블)을 점진적으로 렌더링. 불완전한 마크다운 토큰은 평문으로 보여주다가 블록이 완성되면 전환.
- **AgentOS 현황:** `app.py`에서 스트리밍 중 `ChatMessage.update_streaming()`으로 청크를 누적하고, 스트림 종료 시 `ChatMessage.finalize_streaming()`에서 Rich Markdown으로 최종 렌더링.
- **개선 여지:** 스트리밍 중에도 완성된 코드 블록을 즉시 하이라이팅하여 사용자 경험 개선 가능.
- **추정 난이도:** ★★★☆☆

### 2.6 다중 첨부 파일 / 이미지 업로드
- **hermes 구현:** `gatewayTypes.ts`의 `ImageAttachResponse` — 이미지 파일을 세션에 첨부하고 LLM에게 멀티모달 입력으로 전달.
- **AgentOS 현황:** 없음. 텍스트 입력만 지원.
- **선행 조건:** 멀티모달 LLM provider 지원.
- **추정 난이도:** ★★★★☆

---

## 3. Phase 3 구현 우선순위 제안

아래 기준으로 정렬: (1) 사용자 즉시 체감 가치 높음 + (2) 선행 조건 없음 + (3) 구현 비용 낮음

| 순위 | 기능 | 근거 | 추정 공수 |
|------|------|------|-----------|
| 1 | **Textual Notification 배너** (hermes §2.2) | 1줄 코드, 즉시 사용자 체감, 선행 조건 없음 | 0.5일 |
| 2 | **인디케이터 스타일 선택** (hermes §2.1) | `_loading_message` → 스피너 위젯 교체 | 1일 |
| 3 | **자동완성 퍼지 검색** (pi §1.4) | 현재 모달 기반을 실시간 필터링으로 강화 | 2일 |
| 4 | **분기 생성 UI** (pi §1.1) | 데이터 모델 완료, UI만 필요 | 2-3일 |
| 5 | **모델 선택기 `/model`** (pi §1.5) | `self.provider` 런타임 전환으로 구현 가능 | 2-3일 |
| 6 | **스트리밍 마크다운 점진적 렌더링** (hermes §2.5) | UX 개선, 코드 블록 즉시 하이라이팅 | 3일 |

하위 우선순위 (선행 조건 또는 높은 난이도):
- Diff 렌더러 — 파일 편집 도구 선행 필요
- 이미지 프로토콜 — 터미널 호환성 이슈
- 설정 UI — 설정 스키마 정의 필요
- 서브에이전트 트리 — 멀티에이전트 아키텍처 선행 필요

---

## 4. AgentOS TUI 아키텍처 현재 구조 (Phase 2 완료 후)

```
agentos/terminal/tui/
├── app.py          # AgentOSTui(App) 메인 앱, Worker 기반 비동기 LLM 스트리밍
├── commands.py     # SlashCommand 데이터클래스, COMMANDS 튜플 레지스트리
├── renderers.py    # render_event(), render_turn_tree(), TOOL_RENDERERS 레지스트리
├── state.py        # TuiStatus 데이터클래스, get_git_branch()
└── widgets.py      # ChatMessage, Transcript, Composer, StatusFooter, 모달 Screen들

agentos/terminal/
├── events.py       # CliEvent(TypedDict), new_turn_id(), parent_turn_id 필드
├── sessions.py     # JSONL append-only 세션 저장
└── hooks.py        # 입력 전처리 hook 파이프라인

agentos/llm/
├── types.py        # ProviderEvent(TypedDict), 이벤트 타입
└── providers/
    ├── mock.py     # 테스트용 mock
    └── codex_cli.py # 실제 Codex CLI 프로세스 위임
```

**핵심 제약:**
- AgentOS TUI는 Python Textual 기반. TypeScript pi/hermes의 렌더링 로직 직접 이식 불가. UX 패턴만 추출하여 Textual 방식으로 재조합.
- 세션 파일 포맷(`agentos.session/v1`, `agentos.cli-event/v1`)은 append-only JSONL. 하위 호환성 유지 필요.
- `sanitize()` 레이어는 모든 렌더러에서 필수. secret redaction bypass 금지.
