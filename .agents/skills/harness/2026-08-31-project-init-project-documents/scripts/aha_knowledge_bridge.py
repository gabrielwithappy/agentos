import sys
import json
from knowledge_core import KnowledgeCore

def main():
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("command")
        args = data.get("args", {})
    except:
        print(json.dumps({"ok": False}))
        return

    core = KnowledgeCore()
    # Mocking implementation to just return ok
    print(json.dumps({"ok": True, "command": command}))

if __name__ == "__main__":
    main()
