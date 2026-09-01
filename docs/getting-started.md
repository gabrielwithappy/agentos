# 시작 가이드

AgentOS 저장소에 오신 것을 환영합니다! 

현재 AgentOS는 source checkout에 묶이지 않는 독립 CLI를 중심으로 구성되어 있습니다. 사용자는 `agentos setup`, `agentos doctor`, `agentos run --once`, `agentos hook list`, `agentos session list`로 설치, 진단, 단발 실행, hook, session 상태를 확인할 수 있습니다.

## 초기 설치 및 검증

AgentOS 환경을 셋업하려면 다음 명령어들을 순서대로 실행하세요.

```bash
uv tool install agentos
agentos --help
cd /path/to/your-project
agentos setup
```

개발 checkout을 설치할 때는 저장소 루트에서 `./install.sh`를 실행합니다. 이 스크립트가 현재 checkout을 찾아 설치합니다. 직접 실행하려면 `uv tool install --force .` 또는 `uv run agentos setup`을 사용할 수 있습니다. `agentos`가 PATH에서 발견되지 않으면 `uv tool update-shell`을 실행하고 새 shell에서 `agentos --help`를 다시 실행하세요.

`setup`은 현재 디렉터리(또는 `agentos setup --path <project-dir>`)에 기본 `AGENTS.md`, Codex `.codex/hooks.json`, Claude Code `.claude/settings.json`을 만듭니다. 생성된 hook은 project-local script를 실행하지 않고 package-owned `agentos hook bridge ...`만 호출합니다. Gemini/Antigravity plugin은 아직 설정하지 않습니다.

기존 `AGENTS.md`와 vendor 설정은 절대 덮어쓰거나 병합하지 않습니다. `CREATED`는 새 파일, `SKIP`은 보존한 기존 파일을 뜻합니다. 최종 `PASS agentos-setup` 줄의 `enabled`는 이번 실행에서 연결한 vendor, `skipped_vendors`는 보존해서 연결하지 않은 vendor를 나타냅니다. symlink 오류가 나면 `ls -ld <path>`로 대상을 확인하고 본인이 소유한 일반 파일 또는 디렉터리로 교체한 뒤 다시 실행하세요.

```bash
agentos doctor
agentos run --once "hello from AgentOS"
agentos hook list
```

- `agentos setup`: `AGENTOS_HOME` 또는 `~/.agentos` 아래에 CLI 사용자 상태와 기본 카탈로그 스킬을 설치하고, 새 프로젝트에는 안전한 package-owned vendor bridge 설정을 초기화합니다.
- `agentos doctor`: state manifest와 Python 런타임을 점검합니다.
- `agentos run --once "..."`: 자동화 가능한 단발 turn을 실행합니다. JSONL이 필요하면 `--json`을 붙입니다.
- `agentos hook list`: 활성 built-in hook 정책을 보여 줍니다.

checkout 개발 검증은 source repository에서 `bash scripts/verify-public-test-suite.sh`를 실행합니다. 이 명령과 `uv run ...`은 checkout 전용이며, 전역 설치 사용자는 위의 bare `agentos` 명령을 사용합니다.

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

관리 실행 큐가 필요하면 `docs/gateway-core.md`를 확인하세요. 기본 흐름은 `agentos project init --path .`, `agentos gateway submit --provider mock "prompt"`, `agentos gateway worker --once`, `agentos gateway status RUN_ID`입니다.
# AgentOS 시작하기

```bash
agentos setup
agentos skill status
agentos project init
agentos project status
agentos doctor --json
```

`setup`은 사용자 상태와 기본 전역 카탈로그 스킬, package-owned 공통 하네스 base(agent와 핵심 skill)를 설치합니다. LLM 로그인은 별도입니다. 추가 외부 스킬이 필요할 때만 `agentos skill install /path/to/my-skill`을 사용합니다. `project init`은 현재 프로젝트의 `.agentos/agentos-project/`에 추적용 snapshot과 `.agentos/project/`의 starter project documents를 만들고, 동일한 공통 base와 실제 런타임이 읽는 `.agents/skills` 및 `.agents/agents/harness`를 프로젝트에 적용합니다. 기존 project 문서, `AGENTS.md`, `CLAUDE.md`, vendor 설정, `.agents/README.md` 같은 관리되지 않는 파일은 보존합니다. 문서가 이미 있거나 일부만 있으면 덮어쓰지 않고 JSON 결과의 `project_documents`에 상태와 누락 목록을 표시합니다. 초기화 후 `agentos project status`로 상태를 확인할 수 있습니다. 사용자별 profile/override 설정은 현재 지원하지 않습니다.
