import os
import subprocess
import sys
import time

CONTEXT_REINJECT_MARKER = "/tmp/agy_last_context_inject"
CONTEXT_REINJECT_INTERVAL_SECONDS = 30 * 60


def _load_agentos_context(root):
    agents_md = os.path.join(root, ".agents/AGENTS.md")
    gemini_md = os.path.join(root, ".agents/vendors/gemini.md")

    context = ""
    if os.path.exists(agents_md):
        with open(agents_md, "r", encoding="utf-8") as f:
            context += f"--- AGENTS.md ---\n{f.read()}\n\n"
    if os.path.exists(gemini_md):
        with open(gemini_md, "r", encoding="utf-8") as f:
            context += f"--- gemini.md ---\n{f.read()}\n\n"
    return context


def maybe_reinject_context(root):
    """Periodically re-injects AgentOS core context so long Gemini sessions
    don't drift away from AGENTS.md/gemini.md. Any failure here must never
    block the underlying tool call (graceful degradation)."""
    try:
        now = time.time()
        last = 0.0
        if os.path.exists(CONTEXT_REINJECT_MARKER):
            with open(CONTEXT_REINJECT_MARKER, "r", encoding="utf-8") as f:
                last = float(f.read().strip() or "0")

        if now - last < CONTEXT_REINJECT_INTERVAL_SECONDS:
            return

        context = _load_agentos_context(root)
        if context:
            print(f"AgentOS Context Reinjected:\n{context}", file=sys.stderr)

        with open(CONTEXT_REINJECT_MARKER, "w", encoding="utf-8") as f:
            f.write(str(now))
    except Exception:
        # Never let context reinjection block tool execution.
        pass


def get_workspace_root():
    """Finds the git repository root which is the workspace root."""
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL)
        return root.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return os.getcwd()

# Standard Antigravity Python Plugin Hook Interfaces
def on_session_start(session_data):
    """Bridge for Session Start - Loads Context"""
    root = get_workspace_root()
    agents_md = os.path.join(root, ".agents/AGENTS.md")
    gemini_md = os.path.join(root, ".agents/vendors/gemini.md")
    
    context = ""
    if os.path.exists(agents_md):
        with open(agents_md, "r", encoding="utf-8") as f:
            context += f"--- AGENTS.md ---\n{f.read()}\n\n"
    if os.path.exists(gemini_md):
        with open(gemini_md, "r", encoding="utf-8") as f:
            context += f"--- gemini.md ---\n{f.read()}\n\n"
    
    if context:
        # Inject the context into the agent's startup memory via Ephemeral Message or system prompt
        print(f"AgentOS Context Loaded:\n{context}", file=sys.stdout)

def pre_tool_call(tool_name, tool_args):
    """Bridge for PreToolUse"""
    root = get_workspace_root()
    maybe_reinject_context(root)

    if tool_name == "run_command":
        script_path = os.path.join(root, ".agents/hooks/scripts/check-careful.sh")
        if os.path.exists(script_path):
            result = subprocess.run(["bash", script_path], env=os.environ)
            if result.returncode != 0:
                print("AgentOS Unified Hook: Pre-tool-call rejected by check-careful.sh", file=sys.stderr)
                sys.exit(result.returncode)
                
    elif tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
        script_path = os.path.join(root, ".agents/hooks/scripts/check-alignment.py")
        if os.path.exists(script_path):
            result = subprocess.run([sys.executable, script_path], env=os.environ)
            if result.returncode != 0:
                print("AgentOS Unified Hook: File modification rejected by check-alignment.py (Missing User Alignment / Plan)", file=sys.stderr)
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
