# agentOS

agentOS는 로컬 에이전트 워크플로우를 위한 독립 Python CLI를 제공합니다.
profile, routine, knowledge, Discord, runtime data는 최초 설치에서 자동 생성하거나
활성화하지 않습니다.

사전 준비물은 `bash`, `git`, `python3`, `uv`입니다.

```bash
git clone https://github.com/gabrielwithappy/agentOS.git
cd agentOS
uv run agentos setup
uv run agentos doctor
uv run agentos run --once "hello from AgentOS"
uv run agentos hook list
bash scripts/verify-public-test-suite.sh
```

각 명령은 `PASS`로 끝납니다. 실패하면 원인을 수정한 뒤 같은 명령을 다시 실행합니다.

자동화에는 `agentos run --once "prompt" --json`을 사용합니다. command grammar,
session, hook, 복구, raw token 개인정보 경계는 `docs/cli-reference.md`를 참고하세요.
