# Intent Sheet: knowledge-curator harness 경로 정규화

**날짜:** 2026-09-05  
**요청자 의도 요약:** 날짜가 붙어 혼동을 주는 knowledge-curator harness 경로를 canonical 이름으로 정리할 실행 계획만 작성하고, 이번 단계에서는 실제 파일 변경을 하지 않는다.

## 가설

> .agents/skills/harness/2026-08-31-project-init-project-documents를 .agents/skills/harness/knowledge-curator로 정규화하고 관련 discovery·검증 표면을 맞추면, 스킬 기능은 유지하면서 catalog와 harness 설치 경로의 불일치가 사라질 것이다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 검증으로 통과해야 한다.

- [ ] Run: test -f .agents/skills/harness/knowledge-curator/SKILL.md && ! test -e .agents/skills/harness/2026-08-31-project-init-project-documents && cmp -s .agents/skills/harness/knowledge-curator/SKILL.md catalog/skills/knowledge-curator/SKILL.md && echo 'PASS knowledge-curator-canonical-path'
  Expected: PASS knowledge-curator-canonical-path
- [ ] Run: python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output /tmp/agentos-skill-catalog-path-normalization.html 2>/tmp/agentos-skill-catalog-path-normalization.stderr && ! grep -q 'skipping knowledge-curator' /tmp/agentos-skill-catalog-path-normalization.stderr && grep -q 'knowledge-curator' /tmp/agentos-skill-catalog-path-normalization.html && echo 'PASS catalog-discovery-path'
  Expected: PASS catalog-discovery-path
- [ ] Run: pytest -q tests/test_knowledge_skill.py tests/test_knowledge_curator_evals.py tests/test_common_base_resources.py && bash scripts/verify-public-test-suite.sh
  Expected: 테스트 exit 0 및 PASS agentos-public-suite

## 범위 제약 (Scope Fence)

- 포함: harness 내 날짜 경로를 canonical knowledge-curator 경로로 rename, .agents/skills/harness/_version.json 및 config/public-boundary.json의 해당 경로 정합화, catalog viewer·harness·knowledge-curator 검증.
- 제외: catalog/skills/knowledge-curator 기능 삭제 또는 본문 변경, docs/knowledge 콘텐츠, knowledge-agent 외부 저장소, archive/HISTORY/trace의 과거 기록, manifest governance 자체의 제거.
- 제외: 현재 미커밋 상태인 2026-09-05-remove-manifest-governance 계획과 그 README 변경을 덮어쓰기·정리하기.

## 기술 스택 제약

- Git rename, Markdown/JSON, Python 3.11+, pytest, 기존 catalog viewer 및 public verifier만 사용한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 병렬 구현이 아니라 현재 checkout에서 수행할 단일 경로 정규화 계획이며, 실행 전 기존 미커밋 변경을 보존한다.
- ownership: 현재 non-main branch chore/remove-manifest-governance; 기존 active plan과 동시 구현하지 않는다.

## 우선순위

- 기능 보존과 경로 정합성, 검증 가능성 우선. 최소 파일만 변경한다.

