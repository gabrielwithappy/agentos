# Intent Sheet: hook-loop Plugin Migration

**날짜:** 2026-03-31  
**요청자 의도 요약:** 기존 Bash 기반 hook-loop를 Claude Code 네이티브 플러그인으로 전환하여 CLI 사용성을 높이고, 자율 루프의 안전한 종료를 보장함.

## 가설
> "hook-loop를 슬래시 명령어로 마이그레이션하면 CLI상의 사용자 편의성이 크게 향상되고, 의도 분석 게이트를 거친 자율 루프가 하네스 원칙에 따라 안전하고 자율적으로 종료될 것이다."

## Plan Quality Gate (성공 조건)
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `test -f .claude-plugin/harness-loop.md` Expected: (성공)
- [ ] Run: `grep -c "setup.sh" .claude-plugin/harness-loop.md` Expected: `1` 이상 (Bash 래퍼 확인)

## 범위 제약 (Scope Fence)
- 포함: `.claude-plugin/` 설정, `harness-loop` 슬래시 명령어 래퍼 구현
- 제외: 기존 `setup.sh`, `stop-hook.sh` 로직은 재활용하며 원본 유지 (Plan A wrapper 방식)

## 기술 스택 제약
- Bash + `.claude-plugin` (Markdown manifest)
- TypeScript 재작성 배제 (유지보수 효율성 우선)

## 우선순위
- **MVP (빠른 편리함)**: 기존 스크립트를 래핑하여 즉시 슬래시 명령어를 쓸 수 있는 상태가 최우선.
