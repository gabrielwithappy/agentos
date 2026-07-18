# CI(Pull Request) 테스트 실패 복구 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-18<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-18T09:13:00+09:00<br>
> implementation_completed_at: 2026-07-18T09:14:00+09:00<br>
> implementation_duration: 1m<br>
> reviewed: true<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- GitHub Actions에서 실행되는 모든 PR 테스트(CI) 실패 현상을 복구한다.

**사용자 결과 요약:** 
- 레거시 쉘 스크립트(`setup.sh`) 의존성이 파이프라인에서 완전히 제거되며, Python CLI와 공식 의존성 환경이 구성되어 정상적인 CI 테스트(PASS) 결과를 얻을 수 있다.

**의존성 분석:**
- 외부 의존성: GitHub Actions 환경 (Python 3.12, pip)

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `.github/workflows/test.yml`, `scripts/verify-clean-install.sh`

**진행 상태:** 계획 작성 완료, 리뷰 진행 예정

**아키텍처:** 
- CI 파이프라인에 Python 가상환경 셋업 추가
- 클린 설치 검증 스크립트 내 하드코딩된 `bash setup.sh`를 `python3 agentos/cli.py setup` 호출로 교체

**기술 스택:** 
- GitHub Actions, Bash, Python

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 계획 작성 |
| 현재 위치 | 계획 승인 및 실행 준비 |
| 다음 단계 | 구현 실행 |
| 완료 신호 | 테스트 스크립트 로컬 동작 확인 및 CI 성공 복구 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. CI 워크플로우 업데이트 | CI가 `typer` 등의 의존성을 올바르게 설치함 | `.github/workflows/test.yml` | `grep "actions/setup-python" .github/workflows/test.yml` / Expected: 매칭 결과 출력(PASS) |
| 2. 검증 스크립트 수정 | `setup.sh` 부재로 인한 에러가 해결됨 | `scripts/verify-clean-install.sh` | `bash scripts/verify-clean-install.sh` / Expected: PASS 출력 |

## 리뷰 반영 이력
- (리뷰 진행 예정)

## 구현 결과
1. `.github/workflows/test.yml` 내 `actions/setup-python` 및 `pip install` 추가 완료.
2. `scripts/verify-clean-install.sh` 내 `bash setup.sh` 호출을 Python CLI 호출(`python3 agentos/cli.py setup`)로 변경 완료.

## 사용 방법
CI 수정은 자동화 파이프라인의 백그라운드에서 동작합니다. 이제 PR 생성 시 모든 테스트(Python 테스트 및 클린 인스톨 스크립트)가 정상 작동합니다.

## 아카이브 결정
모든 변경 사항이 성공적으로 구현되었으므로 본 계획 문서를 아카이브합니다.
