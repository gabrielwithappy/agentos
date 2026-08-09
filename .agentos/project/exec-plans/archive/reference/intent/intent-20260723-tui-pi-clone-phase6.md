# Intent Sheet: pi TUI 클로닝 Phase 6

> **상태:** 완료

**날짜:** 2026-07-23  
**요청자 의도 요약:** Phase 5 완료 후 pi TUI를 AgentOS TUI로 계속 이식할 수 있도록 장기 로드맵과 여러 기능을 묶은 첫 구현 계획을 만든다.

## 가설
> pi TUI의 입력 상호작용 계층(능력 선언, 키바인딩, 자동완성)을 AgentOS Textual TUI에 맞는 독립 계약으로 정리하면, 이후 기능 이식이 개별 핸들러에 누적되지 않고 검증 가능한 단계로 진행될 것이다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?
- [ ] Run: `test -d /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src && rg -q "interface AutocompleteProvider" /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/autocomplete.ts && rg -q "class KeybindingsManager" /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/keybindings.ts && echo "PASS pi-reference-input-contract"` Expected: `PASS pi-reference-input-contract`
- [ ] Run: `uv run pytest tests/test_tui_cli.py -q` Expected: `PASS` with no test failures.
- [ ] Run: `rg -q "Phase 6" .agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md && rg -q "자동완성" .agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md && echo "PASS pi-clone-roadmap-mapped"` Expected: `PASS pi-clone-roadmap-mapped`

## 범위 제약 (Scope Fence)
- 포함: Phase 5 완료 확인, pi 참조 checkout revision 고정, pi 기능 매핑 로드맵, AgentOS TUI의 capability registry, 선언형 키바인딩 계약, slash-command/argument 자동완성 계층, 관련 사용자 문서와 Pilot 테스트.
- 제외: pi TypeScript 런타임의 직접 복사, provider credential/LLM transport 변경, 세션 JSONL 스키마 변경, 파일 첨부의 실제 멀티모달 전송, terminal image/diff/compaction 구현, Phase 5 `/settings` 훅 토글 UI의 중복 수정.

## 기술 스택 제약
- Python 3.12+, Textual, pytest/Pilot, 기존 `uv` 환경만 사용한다.
- pi는 read-only 설계 증거이며, 구현은 AgentOS의 Python/Textual 관례로 재구성한다.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 계획 전용 브랜치 `plan/tui-pi-clone-phase6`가 현재 checkout의 미커밋 Phase 4 변경을 보존하며, 병렬 구현을 시작하지 않는다.
- ownership: `plan/tui-pi-clone-phase6` branch = 이 계획 문서 작성 소유.

## 우선순위
- 장기 구조 정비 우선: 이후 pi TUI 기능 이식의 공통 기반을 먼저 만들되, 첫 구현에는 키바인딩과 slash-command/argument 자동완성이라는 사용자 체감 기능을 함께 포함한다.
