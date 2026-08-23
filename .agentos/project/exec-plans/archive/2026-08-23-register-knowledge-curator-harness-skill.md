---
status: 완료
date: 2026-08-23
reviewed: true
usability_review_required: true
user_request: knowledge-curator를 harness skill로 등록한다.
active_agent: codex
active_session:
dashboard_item_id:
implementation_started_at:
implementation_completed_at:
implementation_duration:
---

# knowledge-curator harness skill 등록 구현 계획

**목표:** 기존 standalone `knowledge-curator` bundle을 harness skill registry에 등록한다.

**사용자 결과 요약:** harness 환경에서 knowledge-curator skill을 직접 발견·사용할 수 있으며, 기존 catalog standalone skill과 실행 내용은 동일하게 유지된다.

## 의존성 분석

- 외부 의존성: 없음
- 보호 경로 권한: `.agents/_version.json`의 `codex` authorized architect 권한 확인

## 장기 적용 표면

- Traceability Surface: 이 계획, Intent Sheet, manifest, `HISTORY.md`
- Durable Result Surface: `.agents/skills/harness/knowledge-curator/`

**진행 상태:** 구현 및 검증 완료

**아키텍처:** catalog bundle을 harness skill namespace에 동일 내용으로 등록한다. 두 surface는 parity 검증으로 drift를 탐지한다.

**기술 스택:** Markdown, Python stdlib, Bash, JSON

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 기존 standalone bundle과 manifest 구조 확인 |
| 완료됨 | source bundle 및 protected path 조사 |
| 현재 위치 | Gate 2 리뷰 대기 |
| 다음 단계 | 리뷰 후 bundle 복사 및 manifest sync |
| 완료 신호 | harness bundle 존재, parity·help·manifest check PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Harness 등록 | skill이 harness namespace에서 발견됨 | `.agents/skills/harness/knowledge-curator/**` | path/help PASS |
| 2. 무결성 고정 | source와 등록 bundle이 동일하고 manifest가 일치함 | `.agents/skills/harness/_version.json` | `diff -ru`, sync manifest PASS |

## File Structure

- 생성: `.agents/skills/harness/knowledge-curator/**` - harness용 standalone bundle
- 수정: `.agents/skills/harness/_version.json` - skill manifest
- 유지: `catalog/skills/knowledge-curator/**` - catalog source bundle

## Task 0: Gate 2 리뷰 및 protected path 확인

**파일:** `.agents/traces/audit-plan-review-register-knowledge-curator-harness-skill.md`, `.agents/traces/audit-principle-register-knowledge-curator-harness-skill.md`, `.agents/traces/audit-usability-register-knowledge-curator-harness-skill.md`

- [x] **Step 1:** 계획과 `.agents/_version.json`의 authorized architect를 검토한다.

Run: `jq -e '.distribution.authorized_architects | index("codex")' .agents/_version.json >/dev/null && test -f .agents/traces/audit-plan-review-register-knowledge-curator-harness-skill.md && test -f .agents/traces/audit-principle-register-knowledge-curator-harness-skill.md && test -f .agents/traces/audit-usability-register-knowledge-curator-harness-skill.md`
Expected: `PASS protected-path-review`

## Task 1: Harness bundle 등록

**파일:** `.agents/skills/harness/knowledge-curator/**`

- [x] **Step 1:** catalog의 standalone bundle을 harness namespace에 복사한다.

Run: `diff -ru catalog/skills/knowledge-curator .agents/skills/harness/knowledge-curator`
Expected: no output

## Task 2: Manifest sync 및 실행 확인

**파일:** `.agents/skills/harness/_version.json`

- [x] **Step 1:** authorized `codex`로 manifest를 갱신하고 integrity를 검사한다.

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: update succeeds and final output contains `[PASS]`

- [x] **Step 2:** 등록된 bundle의 CLI help를 실행한다.

Run: `python3 -S .agents/skills/harness/knowledge-curator/scripts/knowledge.py --help`
Expected: exit code 0

## 리뷰 반영 이력

- Gate 2 artifact 생성 후 verdict를 기록한다.

## 구현 결과

- `catalog/skills/knowledge-curator/`를 `.agents/skills/harness/knowledge-curator/`에 등록했다.
- catalog와 harness bundle의 recursive parity를 확인했다.
- harness skill manifest에 `knowledge-curator`를 추가했다.

## 완료 증거

- PASS `diff -ru catalog/skills/knowledge-curator .agents/skills/harness/knowledge-curator`
- PASS `sync-manifest.sh --update codex`
- PASS `sync-manifest.sh --check`
- PASS `python3 -S .agents/skills/harness/knowledge-curator/scripts/knowledge.py --help`

## 아카이브 결정

사용자 검토 및 PR/병합 결정 전까지 active에 유지한다.

## 사용 방법

Harness skill path: `.agents/skills/harness/knowledge-curator/SKILL.md`

## 아카이브 결정

사용자 검토 및 PR/병합 결정 전까지 active에 유지한다.
