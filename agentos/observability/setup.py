import os
import subprocess
from pathlib import Path
from agentos.observability.notifier import notifier
from agentos.observability.adapters.github import GithubDashboardAdapter

def get_gh_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
            token = result.stdout.strip()
        except Exception:
            pass
    return token

def load_env_file(filepath: Path) -> None:
    if filepath.exists():
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v.strip('"\'')

def append_env_file(filepath: Path, key: str, value: str) -> None:
    with open(filepath, "a") as f:
        f.write(f'{key}="{value}"\n')

def setup_observability() -> None:
    env_path = Path.cwd() / ".env"
    load_env_file(env_path)

    if os.environ.get("OBSERVABILITY_ENABLED") == "1":
        token = get_gh_token()
        owner = os.environ.get("OBSERVABILITY_GITHUB_OWNER", "")
        project_number = os.environ.get("OBSERVABILITY_GITHUB_PROJECT_NUMBER", "")

        # Interactive Wizard
        import sys
        if sys.stdout.isatty() and sys.stdin.isatty():
            updated = False
            if not owner:
                owner = input("\n[Observability Wizard] 대상 GitHub Projects v2 소유자(owner login)를 입력하세요 (예: gabrielwithappy): ").strip()
                if owner:
                    os.environ["OBSERVABILITY_GITHUB_OWNER"] = owner
                    append_env_file(env_path, "OBSERVABILITY_GITHUB_OWNER", owner)
                    updated = True

            if not project_number:
                project_number = input("[Observability Wizard] 대상 GitHub Projects v2 프로젝트 번호를 입력하세요 (예: 6): ").strip()
                if project_number:
                    os.environ["OBSERVABILITY_GITHUB_PROJECT_NUMBER"] = project_number
                    append_env_file(env_path, "OBSERVABILITY_GITHUB_PROJECT_NUMBER", project_number)
                    updated = True

            if updated:
                print(f"[Observability Wizard] 설정이 {env_path} 에 저장되었습니다.\n")

        if token and owner and project_number:
            adapter = GithubDashboardAdapter(token=token, owner=owner, project_number=project_number)
            notifier.register_adapter(adapter)
        else:
            import logging
            logging.getLogger(__name__).warning("[Observability Warning] GitHub 설정이 불완전하여 대시보드 연동이 비활성화되었습니다.")
