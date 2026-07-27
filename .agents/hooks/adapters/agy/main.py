import os
import subprocess
import sys

def get_workspace_root():
    """Finds the git repository root which is the workspace root."""
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL)
        return root.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return os.getcwd()

# Standard Antigravity Python Plugin Hook Interfaces
def pre_tool_call(tool_name, tool_args):
    """Bridge for PreToolUse (e.g., check-careful.sh)"""
    if tool_name == "run_command":
        root = get_workspace_root()
        script_path = os.path.join(root, ".agents/hooks/scripts/check-careful.sh")
        if os.path.exists(script_path):
            result = subprocess.run(["bash", script_path], env=os.environ)
            if result.returncode != 0:
                print("AgentOS Unified Hook: Pre-tool-call rejected by check-careful.sh", file=sys.stderr)
                sys.exit(result.returncode)

def post_tool_call(tool_name, tool_args, tool_result):
    """Bridge for PostToolUse (e.g., post_tool_use_review.py)"""
    if tool_name == "run_command":
        root = get_workspace_root()
        script_path = os.path.join(root, ".agents/hooks/scripts/post_tool_use_review.py")
        if os.path.exists(script_path):
            subprocess.run([sys.executable, script_path], env=os.environ)

def on_session_stop(session_data):
    """Bridge for Stop Review Gate"""
    root = get_workspace_root()
    script_path = os.path.join(root, ".agents/hooks/scripts/stop_review_gate.py")
    if os.path.exists(script_path):
        subprocess.run([sys.executable, script_path], env=os.environ)
