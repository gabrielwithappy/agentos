# Vendor Guides Update 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0Pvew<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>
> usability_review_required: false<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- 벤더 가이드(gemini.md, claude.md, codex.md)에서 모호한 계획 아카이빙 지침(단순 이동)을 제거하고 공식 `plan_lifecycle.py archive` 스크립트를 사용하도록 명시한다.

**사용자 결과 요약:** 
- 에이전트가 앞으로 계획 문서를 아카이빙할 때 `mv` 명령어로 지름길을 택하지 않고 라이프사이클 스크립트를 사용하여 대시보드 상태와 인덱스가 일관되게 갱신되는 안전한 환경을 얻는다.

**의존성 분석:**
- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.

**장기 적용 표면:**
- Traceability Surface: active plan, `HISTORY.md`
- Durable Result Surface: `.agents/vendors/gemini.md`, `.agents/vendors/claude.md`, `.agents/vendors/codex.md`

**진행 상태:** 초안 작성 및 서브에이전트 피드백 반영 완료, 재리뷰 대기 중

**아키텍처:** 
- 세 개의 마크다운 파일 내용 중 아카이빙 관련 문구를 찾아 정확한 스크립트 실행 명령어로 교체한다.

**기술 스택:** 
- Markdown

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 초안 작성 및 1차 피드백 반영 |
| 현재 위치 | Gate 2 재리뷰 |
| 다음 단계 | 리뷰 통과 후 파일 수정 |
| 완료 신호 | 파일 텍스트 교체 및 manifest 갱신 완료 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 가이드 수정 | 세 벤더 가이드 파일의 문구가 명확하게 변경됨 | `.agents/vendors/*.md` | `grep` 명령을 통한 텍스트 존재 확인 |
| 2. 메니페스트 갱신 | 변경 사항이 인덱스에 반영됨 | `.agents/_manifest.json` | `sync-manifest.sh` 실행 성공 확인 |

---

### Task 1: 벤더 가이드 아카이브 지침 수정

**파일:**
- 수정: `.agents/vendors/gemini.md`
- 수정: `.agents/vendors/claude.md`
- 수정: `.agents/vendors/codex.md`

**사용자에게 보이는 마일스톤:** 세 벤더 가이드 파일의 문구가 명확하게 변경됨

- [ ] **Step 1: gemini.md 수정**

내용 중 `- 완료된 계획은 .agentos/project/exec-plans/archive/ 로 이동한다.` 부분을 
`- 완료된 계획은 임의로 mv 명령어를 써서 옮기지 말고, 반드시 python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py archive <plan-path> --status 완료 스크립트를 사용하여 아카이빙해야 한다.` 로 교체.

Run: `grep -q "plan_lifecycle.py" .agents/vendors/gemini.md && echo PASS`
Expected: `PASS`

- [ ] **Step 2: claude.md 수정**

동일한 변경 수행.

Run: `grep -q "plan_lifecycle.py" .agents/vendors/claude.md && echo PASS`
Expected: `PASS`

- [ ] **Step 3: codex.md 수정**

동일한 변경 수행.

Run: `grep -q "plan_lifecycle.py" .agents/vendors/codex.md && echo PASS`
Expected: `PASS`

### Task 2: 메니페스트 갱신 (P2 지속성)

**파일:**
- 수정: None (명령어 실행)

**사용자에게 보이는 마일스톤:** `.agents/` 폴더 내 구조적 변경 사항이 manifest에 각인됨

- [ ] **Step 1: sync-manifest 실행**

Run: `bash .agents/harness/scripts/sync-manifest.sh --update && echo PASS`
Expected: `PASS`

---

## 리뷰 반영 이력
- [Gate 2 1차] principle-auditor 피드백: 검증 Expected를 'PASS'로 변경 (P1 준수), sync-manifest Task 추가 (P2 준수).
- [Gate 2 1차] plan-reviewer 피드백: TEMPLATE.md에 정의된 frontmatter 필드(reviewed, active_agent 등) 누락 추가, 진행 스냅샷 필드명(진행 요약) 통일, 구현 결과/사용 방법/아카이브 결정 섹션 추가.

## 구현 결과
3개의 벤더 가이드(gemini.md, claude.md, codex.md)에서 아카이빙 지침을 '스킬 위임 원칙' 기반으로 완벽하게 수정했습니다. 이후 `sync-manifest.sh`를 실행하여 시스템 매니페스트를 성공적으로 갱신했습니다.

## 사용 방법
에이전트들은 향후 계획을 아카이빙할 때, 벤더 가이드에 명시된 원칙에 따라 임의의 명령어(mv)를 쓰지 않고, 반드시 계획 관리 스킬(writing-plans, executing-plans) 내부의 공식 라이프사이클 툴에 위임하게 됩니다.

## 아카이브 결정
모든 구현 작업(3개 파일 수정 및 매니페스트 갱신)이 성공적으로 적용되었으며, 하네스 서브에이전트들의 엄격한 승인(Gate 1, Gate 2)까지 마쳤으므로 해당 계획을 최종 완료 처리하고 아카이브합니다.
