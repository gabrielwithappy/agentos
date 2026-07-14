# 시작 가이드

처음에는 아래에서 사용 중인 제품을 고르세요. 두 제품은 이름이 비슷하지만 설치 후 제공하는 범위가 다릅니다.

## agent-harness를 사용하나요?

agent-harness는 전역 `aha` 명령으로 profile을 준비하고, 작업할 프로젝트에 연결해 개발 작업을 검증하는 흐름입니다.

저장소 루트에서 다음을 실행합니다.

```bash
bash setup.sh
export PATH="${PREFIX:-$HOME/.local}/bin:$PATH"
aha onboard --yes
aha attach --project "$PWD" --yes
aha doctor --project "$PWD"
```

마지막 명령이 성공하면 현재 프로젝트 연결 상태를 확인한 것입니다. `aha`를 찾지 못하면 같은 터미널에서 위 PATH 설정을 다시 적용합니다. `aha doctor --project "$PWD"`가 실패하면 출력의 차단 이유를 확인한 뒤 `aha help doctor`를 읽고 같은 명령을 다시 실행합니다.

## agentOS를 사용하나요?

agentOS는 portable agentcore만 설치합니다. 초기 설치는 AHA CLI, profile, routine, knowledge, Discord 데이터를 만들지 않습니다.

저장소 루트에서 다음을 실행합니다.

```bash
bash setup.sh
bash scripts/verify-public-test-suite.sh
```

`PASS agentos-public-suite`가 출력되면 설치와 공개 배포 검사가 성공한 것입니다. 검사가 실패하면 출력된 조건을 고친 뒤 같은 검사를 다시 실행합니다.

## 다음에 할 일

어느 제품을 선택했는지와 마지막 확인 명령의 결과를 함께 기록하면, 다음 작업을 맡은 에이전트나 협업자가 현재 상태를 빠르게 이어받을 수 있습니다.
