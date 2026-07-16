# AgentOS CLI 도입 및 고도화 전략

이 문서는 `references` 폴더 내 여러 프로젝트들의 CLI 구현 방식을 분석하여 장단점을 파악하고, 이를 바탕으로 `agentos` 프로젝트에 가장 적합한 CLI 도입 전략을 제안합니다.

## 1. 프로젝트별 CLI 구현 특징 및 장단점 분석

### 1.1 `hermes-agent` (Python)
- **특징**: `main.py`를 진입점으로 하여 매우 방대하고 다양한 기능(`chat`, `gateway`, `setup`, `honcho`, `doctor` 등)을 서브커맨드 형태로 제공합니다.
- **장점**: 올인원(All-in-one) 도구로서 사용자에게 하나의 진입점으로 수많은 기능을 강력하게 제공할 수 있습니다.
- **단점**: 코드가 단일 모듈에 비대하게 집중될 위험이 있으며(실제 `main.py` 크기가 상당함), 초기 로딩 시간 지연이나 유지보수의 어려움이 발생할 수 있습니다.

### 1.2 `nanobot` (Python + Typer)
- **특징**: Python의 `Typer` 라이브러리를 활용하여 타입 힌트 기반의 현대적이고 깔끔한 CLI를 구축했습니다. `pyproject.toml`의 `[project.scripts]`를 통해 커맨드를 노출합니다.
- **장점**: 직관적인 코드 작성, 자동화된 도움말 문서(Help) 생성, 서브커맨드 추가 및 확장이 매우 쉽습니다.
- **단점**: 사용자가 Python 런타임 및 의존성 환경(가상환경 등)을 별도로 관리해야 합니다.

### 1.3 `opencodex` (TypeScript + Bun)
- **특징**: Bun 런타임 위에서 동작하는 TypeScript 기반 CLI(`src/cli/index.ts`)입니다.
- **장점**: Node/JS/TS 생태계의 다양한 패키지를 활용할 수 있으며, Bun 덕분에 기존 Node.js CLI보다 빠른 실행 속도를 보여줍니다.
- **단점**: 사용자 환경에 Bun 또는 Node 런타임이 설치되어 있어야 합니다.

### 1.4 `oh-my-pi` (Rust)
- **특징**: Rust로 작성된 쉘/CLI 확장 프로젝트입니다. 네이티브 컴파일(Cargo)을 지원합니다.
- **장점**: 실행 속도가 최상급이며 메모리 사용량이 적습니다. 단일 바이너리로 배포하기 가장 유리합니다.
- **단점**: 개발 난이도가 높으며, Python 생태계 중심인 AI 및 LLM 로직과의 직접적인 통합이 비교적 까다로울 수 있습니다.

---

## 2. AgentOS CLI 적용 전략 (결정 사항)

사용자의 결정에 따라, **Python (Typer + Rich 기반)**을 메인 구현 언어 및 프레임워크로 채택하여 CLI를 구축합니다. 이는 현재 Bash 기반의 스크립트들을 통합하고, 향후 Python AI 생태계의 다양한 기능들을 AgentOS에 직접 통합하기 위한 최선의 선택입니다.

### Python 기반 통합 CLI 구현 방향
- **패키지 관리 및 설치**: `uv`를 표준 패키지 매니저로 사용합니다. 기존 `pip`나 `poetry`보다 압도적으로 빠르며, 레퍼런스 프로젝트(`hermes-agent`)에서도 검증된 방식입니다. 개발 시 `uv sync`를 사용하고, 배포 및 설치 시 `uv pip install` 또는 `uv tool install`을 활용합니다.
- **도구 및 프레임워크**: `Typer` (자동 도움말 및 서브커맨드 라우팅), `Rich` (터미널 텍스트 포매팅 및 패널 UI).
- **구조적 모듈화**: `hermes-agent`의 `main.py` 비대화 문제를 교훈 삼아, 각 명령어 군(Command Group)을 별도의 파이썬 모듈로 분리하여 `nanobot` 스타일의 모듈화된 계층 구조를 갖춥니다.
- **실행 환경**: `pyproject.toml`의 `[project.scripts]`를 정의하여 `agentos` 명령어로 시스템 전역에서 접근할 수 있도록 구성합니다.

---

## 3. CLI 명령어(Command) 상세 명세

각 명령어의 목적(Purpose)을 명확히 하고 부작용(Side effects)을 통제하기 위해 다음과 같이 상세 명세를 정의합니다.

### 3.1 `agentos setup` (또는 `init`)
*   **목적**: AgentOS 구동에 필요한 초기 환경 및 디렉토리 구조를 안전하게 구성합니다.
*   **동작**: 
    *   기존 `setup.sh`의 로직을 파이썬으로 이관.
    *   사용자 홈 디렉토리(`~/.agentos`)에 필수 폴더(`.agents`, `core`) 생성.
    *   초기 `manifest.json` 생성 및 검증.
*   **검증 목표**: 명령어 실행 후 지정된 경로에 폴더와 파일이 누락 없이 생성되는지, 기존 파일이 있을 경우 덮어쓰지 않고 안전하게 백업/유지되는지 확인합니다.

### 3.2 `agentos run` (또는 `start`)
*   **목적**: 사용자와 상호작용하는 기본 Agent 세션(대화형 인터페이스)을 시작합니다.
*   **동작**:
    *   설정 파일들을 로드하고 환경 변수를 검사.
    *   터미널에서 LLM과 통신 가능한 Chat Loop 진입 (Typer/Prompt Toolkit 활용).
*   **검증 목표**: 모의(Mock) LLM 응답을 통해 루프가 정상적으로 구동되고 종료(Ctrl+C 또는 exit) 시 리소스가 깔끔하게 정리되는지 확인합니다.

### 3.3 `agentos harness`
*   **목적**: 기존 `harness-loop.sh`를 대체하여, 코어 루프 및 내부 테스트/검증 하네스를 실행합니다.
*   **동작**:
    *   내부 canonical 스크립트(`.agents/skills/harness/harness-loop.sh`)로의 위임 혹은 해당 로직 직접 실행.
*   **검증 목표**: 인자(Arguments)가 하위 하네스 프로세스로 유실 없이 전달되는지, 하네스 프로세스의 종료 코드(Exit code)가 상위로 정확히 전파되는지 확인합니다.

### 3.4 `agentos doctor`
*   **목적**: 현재 환경이 AgentOS를 실행하기에 적합한지 진단합니다.
*   **동작**:
    *   필수 패키지 버전 확인, 환경 변수(`AGENTOS_HOME` 등) 점검, `.agents` 플러그인 폴더 무결성 검사.
*   **검증 목표**: 일부러 환경 변수를 지우거나 폴더 권한을 뺏은 상태에서 `doctor`가 정확한 에러 메시지와 해결책(Remediation)을 출력하는지 단위 테스트합니다.

### 3.5 `agentos skill`
*   **목적**: 에이전트에 새로운 스킬을 추가하거나 목록을 관리합니다.
*   **동작**: `agentos skill list`, `agentos skill add <경로>` 등 서브커맨드 라우팅.
*   **검증 목표**: 스킬 추가 시 올바른 경로(symlink 또는 copy)로 배치되는지, 유효하지 않은 스킬 구조(예: `SKILL.md` 누락)일 때 거부하는지 확인합니다.

---

## 4. 검증 계획 (Verification Plan)

각각의 CLI 명령어가 올바르게 작동하는지 보장하기 위해 다음 두 가지 방식을 병행합니다.

### 4.1 자동화 테스트 (Automated Tests)
- `pytest` 및 Typer의 `CliRunner`를 사용하여 독립된 테스트 환경에서 각 명령어를 실행합니다.
- **테스트 케이스 예시**:
  - `test_cli_setup_creates_directories`: `agentos setup` 시 임시 디렉토리에 정확한 파일 트리가 생성되는가?
  - `test_cli_doctor_missing_env`: 환경 변수가 없을 때 `agentos doctor`가 에러 코드(non-zero)를 반환하는가?
  - `test_cli_harness_delegation`: `agentos harness --test` 호출 시 내부 인자가 올바르게 전달되는가?

### 4.2 수동 검증 (Manual Verification)
- 샌드박스/가상환경 내에서 직접 패키지를 설치(`pip install -e .`)한 후, 터미널에서 사용자가 체감할 수 있는 수준의 수동 테스트 진행.
- **검증 항목**: `Rich` 라이브러리로 출력되는 색상, 테이블, 로딩 스피너 등의 UI가 명확하고 예쁘게 표시되는지 확인.
