# pi TUI 아키텍처 및 AgentOS 적용 코드 분석

- Expansion Trigger: `pi TUI 격차 해소 Phase 1` 계획 수립 중, 향후 참조를 위한 아키텍처 인벤토리 문서화 필요
- parent root doc: `03-system-contract.md`
- reason for creation: AgentOS TUI와 pi TUI 간의 기능 격차를 분석하고, 향후 이식 가능한 기능들의 우선순위와 아키텍처 구조를 보존하기 위함.
- owner: AgentOS TUI 구현 파트
- freshness rule: pi TUI의 추가적인 분석이 이루어지거나 AgentOS TUI가 크게 변경될 때 갱신.
- status: 현재 (Current)
- source evidence: `references/pi/packages/tui`, `references/pi/packages/coding-agent/src/modes/interactive` 소스 코드 기반
- links back to 요구사항, decisions, risks, or verification: `.agentos/project/exec-plans/active/2026-07-21-tui-pi-clone-phase1.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, or reviewer authority

---

## 1. 개요 및 설계 철학

`pi` 도구의 TUI(터미널 사용자 인터페이스)는 TypeScript 기반으로 작성되었으며, 약 3만 줄 이상의 코드와 40개 이상의 자체 UI 컴포넌트로 구성된 강력하고 복잡한 시스템입니다.
기성 TUI 라이브러리(예: Textual, Ink 등)에 의존하기보다, 자체적인 저수준 터미널 렌더링 엔진을 바닥부터 구축하여 터미널 환경을 완벽하게 제어하려는 특징을 보입니다.

## 2. pi TUI 핵심 아키텍처 (저수준 구현부)

### 자체 렌더링 엔진 및 차분 렌더러 (`tui.ts`, `terminal.ts`)
- pi는 터미널 화면 전체를 매번 다시 그리는 대신, 화면의 변경된 부분만 계산하여 업데이트하는 독자적인 렌더링 시스템을 가지고 있습니다.
- **AgentOS 적용 분석:** AgentOS는 현재 Python의 `Textual` 프레임워크를 기반으로 하고 있습니다. Textual이 자체적으로 고성능 렌더링과 차분 업데이트, 리플로우(reflow)를 처리하므로, pi의 저수준 렌더러 로직을 AgentOS에 이식할 필요는 없습니다.

### 입력 처리 및 상태 관리 (`stdin-buffer.ts`, `keys.ts`)
- 원시(raw) stdin 이벤트를 캡처하여 키스트로크를 해석하고 이스케이프 시퀀스를 수동으로 파싱합니다.
- 복잡한 터미널 모디파이어(Shift, Ctrl, Alt 등) 처리 로직이 존재합니다.
- **AgentOS 적용 분석:** Textual의 내장 키 바인딩 및 이벤트 핸들링으로 완전히 대체 가능합니다.

## 3. UI/UX 컴포넌트 기능 인벤토리

pi의 대화형 모드(`interactive-mode.ts` 등)에서 제공하는 주요 사용자 컴포넌트를 분류하고, AgentOS(Textual) 환경에서의 적용 가능성을 분석했습니다.

### Phase 1 (즉시/단기 적용 가능 항목)
Textual의 기본 기능을 활용하여 빠르게 구현할 수 있으며 사용자 가치가 높은 항목입니다.

1. **키보드 단축키 헬퍼 (`/hotkeys`)**
   - pi에서는 하단이나 별도 모달로 현재 컨텍스트에 맞는 단축키 가이드를 제공.
   - **적용:** AgentOS에 흩어진 단축키들을 모아 보여주는 표/모달 형태로 쉽게 이식 가능.
2. **테마 전환기 (`/theme`)**
   - pi는 2가지(Light/Dark) 기본 테마 제공.
   - **적용:** Textual은 21종의 풍부한 내장 테마를 갖추고 있으므로, 선택형 모달만 추가하면 pi보다 훨씬 뛰어난 경험 제공 가능.
3. **향상된 푸터 정보 (Git 브랜치, 리소스 사용량)**
   - pi는 화면 구석(푸터 등)에 모델 사용량이나 워크스페이스 상태를 요약해서 노출.
   - **적용:** Textual의 Footer 컴포넌트를 확장하여 Git 브랜치 이름과 누적 입출력(Token/Chars) 사용량을 표시하는 기능으로 이식.
4. **Tool Call (도구 실행) 시각적 피드백 강화**
   - pi는 에이전트의 액션(도구 실행)과 사고(Thinking) 과정을 시각적 박스나 아이콘으로 명확히 구분.
   - **적용:** AgentOS의 `ChatMessage` CSS를 분리하여 `Tool call`/`Tool result`에는 명확한 테두리(Border)를, `Thinking`에는 무채색 처리를 적용해 가독성 향상.

### Phase 2 이후 장기 적용 후보 (중/고 난이도)
구현에 많은 비용이 들거나 추가적인 선행 작업이 필요한 기능들입니다.

**Phase 2 (`2026-07-22-tui-pi-clone-phase2.md`)에서 착수/완료된 항목:**

1. **분기(Branch) 탐색기 트리 뷰 (`/tree`)** — **완료.** 대화 내역의 분기를 ASCII 트리로 시각화하는 `/tree` 명령을 추가했다(`agentos/terminal/tui/renderers.py::render_turn_tree`). 선행 조건으로 세션 이벤트 스키마(`agentos/terminal/events.py`)에 `parent_turn_id` 필드를 추가했다. AgentOS에는 아직 이전 턴으로 되돌아가 새 메시지를 보내는 분기 생성 UI가 없으므로, 현재는 항상 선형 체인(가지가 하나인 트리)으로만 보인다 — `render_turn_tree` 자체는 실제 분기 데이터가 주어지면 올바르게 여러 가지를 렌더링하도록 구현·테스트되어 있어, 분기 생성 UI가 추가되면 별도 수정 없이 바로 동작한다.
2. **도구별 커스텀 렌더러 (Custom Tool Output Renderers)** — **아키텍처 완료 + 예시 1개.** 도구 실행 결과를 도구 이름별로 다르게 렌더링할 수 있는 `TOOL_RENDERERS` 레지스트리와 `register_tool_renderer()`를 `agentos/terminal/tui/renderers.py`에 추가했다. 예시로 mock 공급자의 `mock_tool` 결과를 `| field | value |` 표로 렌더링하는 렌더러 1개를 등록했다. 등록되지 않은 도구는 기존과 동일한 평문(`Tool result: ...`)으로 계속 렌더링된다(회귀 없음). "Plugin 아키텍처 도입이 선행되어야 함"이라던 원래 평가와 달리, 실제로는 `render_event()` 내부의 간단한 dict 레지스트리 조회만으로 충분했다 — 별도의 플러그인 시스템은 필요하지 않았다. 향후 계획에서 파일 목록, 검색 결과 등 추가 렌더러를 점증적으로 등록할 수 있다.

**Phase 2에서도 범위 밖으로 유지된 항목:**

3. **고도화된 Diff 렌더러**
   - 변경된 코드를 나란히(Side-by-side) 또는 인라인(Inline) 색상으로 렌더링.
   - 현재 AgentOS에는 사용자 승인 전 파일을 직접 수정하는 "편집 도구"가 없으므로 아직 활용처가 적음.
4. **이미지 프로토콜 지원 (Kitty Image Protocol 등)**
   - 터미널 내에서 직접 이미지를 보여주는 기능.
   - Textual에서도 일부 픽셀 그래픽/Sixel 지원이 가능하나 특수한 터미널 환경을 요구하므로 호환성 이슈 존재.
5. **분기 생성 UI** (신규 식별, Phase 2 계획 중 발견)
   - 이전 턴으로 되돌아가 새 메시지를 보내 실제 분기를 만드는 사용자 흐름.
   - `/tree`가 읽는 `parent_turn_id` 데이터 모델은 이미 준비되어 있으므로, 분기 생성 UI만 추가하면 `/tree`가 즉시 실제 분기를 보여준다.

**Phase 2에서 신규로 발견되어 함께 구현된 항목 (원래 이 문서에 없었음):**

- **스트리밍 취소 / 로딩 인디케이터** — pi TUI의 `cancellable-loader.ts` 대응 기능. 메시지 전송 후 첫 응답 조각 전까지 `Thinking…` 로딩 표시가 나타나고, 이 상태에서 `Esc`를 누르면 Textual의 `Worker.cancel()`/`is_cancelled` 협조적 취소 메커니즘으로 즉시 턴을 취소하고 `Turn cancelled.`를 표시한다(`agentos/terminal/tui/app.py`).

## 4. 종합 평가

pi TUI는 완벽한 커스텀 엔진을 바탕으로 세밀한 터미널 제어를 이루어냈지만, 그로 인해 막대한 코드 유지보수 비용을 지불하고 있습니다. 
반면 AgentOS는 성숙한 `Textual` 생태계를 기반으로 하므로, pi의 렌더링 로직 자체를 모방할 필요 없이 **"pi가 제공하는 훌륭한 사용자 경험(UX) 패턴"**만을 추출하여 Textual의 컴포넌트로 재조합(Re-composition)하는 전략이 훨씬 효율적입니다.

이를 통해 Phase 1에서는 단축키 통합, 테마 선택, 푸터 확장, 도구 호출 시각화 등 즉각적인 사용자 만족도를 높이는 요소에 집중하고, 향후 도구 확장 아키텍처가 마련되었을 때 커스텀 렌더러나 트리 뷰 등 고도화된 UI 요소를 이식하는 방향으로 나아가야 합니다.
