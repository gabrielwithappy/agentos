# 시작 가이드

AgentOS 저장소에 오신 것을 환영합니다! 

현재 AgentOS는 가볍고 이식성 높은 **Portable AgentCore** 기능을 중심으로 구성되어 있습니다. 향후 `agent-harness`가 제공하던 풍부한 다중 에이전트 관리 기능과 CLI(`aha`) 기능들이 점진적으로 AgentOS 환경으로 통합(마이그레이션)될 예정입니다.

## 초기 설치 및 검증

AgentOS 환경을 셋업하려면 저장소 루트에서 다음 명령어들을 순서대로 실행하세요.

```bash
uv run agentos setup
bash scripts/verify-public-test-suite.sh
```

- `uv run agentos setup`: AgentOS 실행에 필요한 필수 의존성 패키지와 환경을 구성합니다.
- `verify-public-test-suite.sh`: 현재 시스템 환경이 공개 배포 및 실행에 적합한지 테스트합니다.

터미널에 `PASS agentos-public-suite`가 출력되면 설치와 기본 검증이 완벽하게 성공한 것입니다!
(만약 검사가 실패한다면, 출력된 오류 조건과 로그를 확인하고 조치한 뒤 같은 스크립트를 다시 실행하세요.)

## 기능 마이그레이션 안내 (Agent Harness -> AgentOS)

현재 버전의 AgentOS는 초기 설치 시 프로필(profile), 루틴(routine), 지식 베이스(knowledge), Discord 연동 데이터를 자동으로 생성하지 않습니다. 

이러한 확장 기능들은 기존 `agent-harness` 프로젝트에서 사용되던 기능들이며, 향후 업데이트를 통해 점진적으로 AgentOS 내부로 마이그레이션 및 정식 지원될 예정입니다. (예: 계획 문서는 이제 `docs/exec-plans/`가 아닌 `.agentos/project/exec-plans/` 경로에 저장됩니다.)

## 다음에 할 일

초기 설치와 테스트가 무사히 끝났다면, 현재 상태(예: 테스트 PASS 로그)를 기록해 두는 것을 권장합니다. 이를 통해 다음 작업을 맡은 에이전트나 협업자가 현재 저장소의 준비 상태를 명확히 인지하고 개발을 이어받을 수 있습니다.
