# agentOS

agentOS는 이식 가능한 agentcore만 최초 설치합니다. profile, routine, knowledge,
Discord, runtime data는 생성하거나 활성화하지 않습니다.

사전 준비물은 `bash`, `git`, `python3`입니다.

```bash
git clone https://github.com/gabrielwithappy/agentOS.git
cd agentOS
bash setup.sh
bash scripts/verify-public-test-suite.sh
```

각 명령은 `PASS`로 끝납니다. 실패하면 원인을 수정한 뒤 같은 명령을 다시 실행합니다.
