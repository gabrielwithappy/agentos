# Intent Sheet: 계획 리뷰 게이트 단순화

**작성일:** 2026-09-01
**상태:** 확정된 실행 입력

## 가설

현재의 반복 block은 리뷰 품질 자체보다, 무관한 active plan까지 Stop 훅이 검사하고 일반 계획에도 여러 reviewer·artifact·서명 절차를 동시에 강제하는 구조에서 발생한다. 검사 범위를 현재 계획으로 좁히고 reviewer를 위험·변경 유형에 따라 선택하면, 안전성을 유지하면서 계획 리뷰를 완료할 수 있다.

## Plan Quality Gate

- 리뷰 대기 중인 초안은 `reviewed: true`가 없어도 저장·보완할 수 있다.
- 일반 계획은 독립 `plan-reviewer` 1명의 PASS artifact로 실행 대기 상태가 된다.
- `.agents/` 하네스 계약·보안·보호 경로를 변경하는 계획만 `principle-auditor`를 추가한다.
- user-facing 동작을 변경하는 계획만 `usability-reviewer`를 추가한다.
- Stop 훅은 무관한 plan의 오래된 리뷰 오류로 현재 세션을 전역 차단하지 않으며, 실행 명령과 명시적 completion gate가 대상 plan의 validity를 판단한다.
- focused harness tests와 public verifier가 PASS하고, manifest가 일치한다.

## 범위 제약 (Scope Fence)

포함:
- Stop 훅의 전역 차단 범위 축소
- reviewer 선택 규칙과 계획 템플릿/문서의 정합성 회복
- 중복 audit trace 강제 제거 및 JSON reviewer artifact의 단일 기록면 유지
- 회귀 테스트와 사용자 복구 메시지 정리

제외:
- secret redaction, 작성자와 reviewer 분리, protected-path 승인, 실행 전 plan validity 확인 제거
- 새로운 외부 서비스·MCP·승인 시스템 도입
- 기존 계획의 소급 재리뷰나 archive 정리

## 기술 스택 제약

- 기존 Python 3 CLI/hook, Markdown 계획, pytest/bash harness tests만 사용한다.
- 계획 리뷰와 실행 lifecycle의 기존 명령 표면을 유지하고, 필요한 경우에만 메시지와 판정 범위를 수정한다.

## Worktree Decision

- 현재 checkout의 사용자 변경을 보존하기 위해 feature branch에서 계획을 작성한다.

## 우선순위

- MVP: 반복 block을 제거하고 최소 reviewer 경계를 구현하는 것.
