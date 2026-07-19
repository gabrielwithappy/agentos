# 시작 가이드

AgentOS 저장소에 오신 것을 환영합니다! 

현재 AgentOS는 source checkout에 묶이지 않는 독립 CLI를 중심으로 구성되어 있습니다. 사용자는 `agentos setup`, `agentos doctor`, `agentos run --once`, `agentos hook list`, `agentos session list`로 설치, 진단, 단발 실행, hook, session 상태를 확인할 수 있습니다.

## 초기 설치 및 검증

AgentOS 환경을 셋업하려면 다음 명령어들을 순서대로 실행하세요.

```bash
uv run agentos setup
uv run agentos doctor
uv run agentos run --once "hello from AgentOS"
uv run agentos hook list
bash scripts/verify-public-test-suite.sh
```

- `uv run agentos setup`: `AGENTOS_HOME` 또는 `~/.agentos` 아래에 CLI 사용자 상태만 초기화합니다.
- `uv run agentos doctor`: state manifest와 Python 런타임을 점검합니다.
- `uv run agentos run --once "..."`: 자동화 가능한 단발 turn을 실행합니다. JSONL이 필요하면 `--json`을 붙입니다.
- `uv run agentos hook list`: 활성 built-in hook 정책을 보여 줍니다.
- `verify-public-test-suite.sh`: 현재 시스템 환경이 공개 배포 및 실행에 적합한지 테스트합니다.

터미널에 `PASS agentos-public-suite`가 출력되면 설치와 기본 검증이 성공한 것입니다.
(만약 검사가 실패한다면, 출력된 오류 조건과 로그를 확인하고 조치한 뒤 같은 스크립트를 다시 실행하세요.)

## 대화형과 자동화

TTY 터미널에서 bare `agentos`를 실행하면 대화형 세션이 시작됩니다. pipe나 redirect 환경에서 bare `agentos`는 입력을 기다리지 않고 exit code `2`로 종료하며 `agentos run --once "<prompt>"`를 안내합니다.

```bash
agentos run --once "summarize this project" --json
```

JSONL stdout은 provider event(`start`, `message_delta`, `done`, `error`)만 포함하고, 진단과 복구 안내는 stderr로 분리됩니다.

## Hook과 session

Hook은 `AGENTOS_HOME/config.toml`의 선언형 built-in 정책만 지원합니다. shell command, Python import, project-local code hook은 실행하지 않습니다. `prepend_context_file`은 기본 비활성화이며 `AGENTOS_HOME/context` 바로 아래의 `.md` 파일만 허용합니다.

Session은 `AGENTOS_HOME/sessions`에 사용자 데이터로 저장됩니다. 자동 삭제는 없고, 삭제와 prune은 preview 후 confirmation 또는 `--yes`를 요구합니다.

## 기능 마이그레이션 안내 (Agent Harness -> AgentOS)

현재 버전의 AgentOS는 초기 설치 시 프로필(profile), 루틴(routine), 지식 베이스(knowledge), Discord 연동 데이터를 자동으로 생성하지 않습니다. 

이러한 확장 기능들은 기존 `agent-harness` 프로젝트에서 사용되던 기능들이며, 향후 업데이트를 통해 점진적으로 AgentOS 내부로 마이그레이션 및 정식 지원될 예정입니다. (예: 계획 문서는 이제 `docs/exec-plans/`가 아닌 `.agentos/project/exec-plans/` 경로에 저장됩니다.)

## 다음에 할 일

자세한 command grammar와 recovery matrix는 `docs/cli-reference.md`를 확인하세요.
