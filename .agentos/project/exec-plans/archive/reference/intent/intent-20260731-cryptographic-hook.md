# Intent Sheet: 암호학적 서명을 이용한 훅 구조 강화

**날짜:** 2026-07-31
**요청자 의도 요약:** 메인 에이전트가 `reviewed: true` 텍스트나 리뷰 증거 문서를 위조하여 구현을 임의로 진행하는 문제를 방지하기 위해, 시스템 레벨의 비밀키와 암호학적 서명을 활용한 리뷰 훅 구조(2번째 방법)를 구축한다.

## 가설
> 메인 에이전트의 접근이 차단된 환경변수/시스템 파일에서 비밀키를 로드하고, 전용 리뷰 스크립트가 서브에이전트 검증 후 생성한 서명(Signature)과 해시(Hash)를 `check-alignment.py`가 수학적으로 검증하면, 에이전트의 임의 위조 및 룰 우회를 원천적으로 차단할 수 있을 것이다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `python3 .agents/hooks/scripts/check-alignment.py` Expected: `AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing.` (서명이 없는 계획 문서에 대해 차단 메시지 출력 후 `echo $?`가 `1` 반환)
- [ ] Run: `python3 -c "import os; print(os.path.exists('.agentos/secret.key') or os.path.exists('.agentos/config.json'))"` Expected: `True` (시스템 비밀키 파일 생성 여부 확인)
- [ ] Run: `cat .agents/skills/harness/writing-plans/SKILL.md | grep "request_review.py"` Expected: SKILL.md 가이드에 전용 리뷰 요청 스크립트 사용 지침이 포함되어 있음

## 범위 제약 (Scope Fence)
- 포함: `.agents/hooks/scripts/check-alignment.py` 검증 로직 변경, 비밀키 생성 및 서명 로직 모듈(`agentos/observability` 또는 별도 유틸) 추가, 리뷰 전용 요청 스크립트(`.agents/skills/harness/writing-plans/scripts/request_review.py` 등) 작성, `SKILL.md` 업데이트.
- 제외: `agentos` 핵심 데몬(Daemon) 아키텍처 재구축, 외부 모델 라우팅 로직 변경.

## 기술 스택 제약
- 순수 Python 내장 모듈(`hashlib`, `hmac`, `json` 등) 사용.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 진행 중인 다른 병렬 작업과 충돌하지 않으며, 현재 checkout 내에서 독립적 스크립트 추가 및 수정으로 해결 가능.

## 우선순위
- 에이전트의 통제권 우회를 막기 위한 보안성과 신뢰성(Reliability) 확보 최우선.
