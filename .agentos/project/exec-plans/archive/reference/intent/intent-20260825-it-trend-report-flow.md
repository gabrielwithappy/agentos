# Intent Sheet: it-trend-report knowledge flow

**날짜:** 2026-08-25  
**요청자 의도 요약:** `it-trend-report` 스킬이 실행 근거를 `skills/it-trend-report/runs/YYYY-MM-DD/`에 남기고 검토된 IT trend 결과를 `docs/knowledge/concepts/it-trend-reports/`에 올바르게 저장하는지 점검하고 수정한다.

## 가설
> 날짜·저장 경로를 저장소 루트 기준으로 고정하고 자동 원격 변경을 제거하면, 실행 환경과 무관하게 재현 가능한 IT trend 파이프라인이 되고 장기지식 저장 경계가 보존된다.

## Plan Quality Gate
- [ ] Run: `python3 -m unittest discover -s knowledge-agent/skills/it-trend-report/tests -v` Expected: 모든 테스트 PASS
- [ ] Run: `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py knowledge-agent/skills/it-trend-report` Expected: `Skill is valid!`
- [ ] Run: `! rg -n 'runs/today|/root/workspace|\["git"|git", "(push|commit|config|add)' knowledge-agent/skills/it-trend-report/scripts` Expected: 출력 없음
- [ ] Run: `python3 -S knowledge-agent/skills/knowledge-curator/scripts/knowledge.py validate --project knowledge-agent/docs/knowledge` Expected: JSON `"ok": true`, exit 0

## 범위 제약
- 포함: `knowledge-agent/skills/it-trend-report/SKILL.md`, `README.md`, 실행 스크립트, 해당 skill의 smoke tests
- 제외: 기존 knowledge 문서 내용, 원격 push, 자동 Git commit, 외부 API 인증, `knowledge-curator` CLI 구현

## 기술 스택 제약
- Python 3 표준 라이브러리 테스트, 기존 PyYAML/BeautifulSoup 실행 의존성, Markdown/OKF v0.2

## Worktree Decision
- 필요 여부: 불필요
- 이유: 기존 변경을 보존하는 전용 feature branch에서 작업한다.
- ownership: `feature/it-trend-report-knowledge-flow`

## 우선순위
- 데이터 보존과 경로 정확성, 원격 부작용 제거를 우선한다.
