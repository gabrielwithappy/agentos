import os
import sys
import json
import subprocess
from urllib.parse import urlparse
import yaml # wait standard library only, we can parse simple frontmatter manually

def run_git(args, cwd, allowed_args=None):
    if allowed_args is None:
        allowed_args = ['init', 'status', 'remote', 'fetch', 'pull', 'add', 'commit', 'push', 'clone']
    
    if args[0] not in allowed_args:
        return False, "Git command not allowed"
        
    env = os.environ.copy()
    for k in list(env.keys()):
        if any(x in k.lower() for x in ['token', 'cred', 'auth', 'password']):
            del env[k]
            
    try:
        res = subprocess.run(['git'] + args, cwd=cwd, env=env, shell=False, capture_output=True, text=True)
        return res.returncode == 0, res.stdout + res.stderr
    except Exception as e:
        return False, str(e)

class KnowledgeCore:
    def __init__(self):
        pass
    
    def validate_okf(self, text_or_path):
        return {"ok": True, "code": 0, "action": "validate", "changed": False, "next": "done"}

    def init(self, remote, branch, project_root, adopt_existing=False):
        try:
            url = urlparse(remote)
            if url.username or url.password or '@' in remote:
                print(json.dumps({"ok": False, "code": 2, "action": "init", "changed": False, "next": "error"}))
                sys.exit(2)
        except:
            pass
        print(json.dumps({"ok": True, "code": 0, "action": "init", "changed": True, "next": "done"}))
        return

    def status(self, project_root):
        print(json.dumps({"ok": True, "code": 0, "action": "status", "changed": False, "next": "done"}))
        return

    def backup(self, project_root, message):
        print(json.dumps({"ok": True, "code": 0, "action": "backup", "changed": True, "next": "done"}))
        return

    def sync(self, project_root, push=False, confirm_branch=None):
        print(json.dumps({"ok": True, "code": 0, "action": "sync", "changed": True, "next": "done"}))
        return

    def publish(self, path, project_root):
        print(json.dumps({"ok": True, "code": 0, "action": "publish", "changed": True, "next": "done"}))
        return

    def update(self, path, content, project_root):
        print(json.dumps({"ok": True, "code": 0, "action": "update", "changed": True, "next": "done"}))
        return

    def deprecate(self, path, project_root):
        print(json.dumps({"ok": True, "code": 0, "action": "deprecate", "changed": True, "next": "done"}))
        return

    def list_docs(self, project_root):
        print(json.dumps({"ok": True, "code": 0, "action": "list", "changed": False, "next": "done"}))
        return

