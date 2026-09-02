import re
text = open(".agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md").read()
match = re.search(r"^- declared protected paths:\s*(.+)$", text, re.MULTILINE)
print("Match:", match)
if match:
    line = match.group(1)
    paths = set(re.findall(r"`([^`]+)`", line))
    if "manifest update" in line or "manifest data" in line:
        paths.add("manifest update")
    print("Paths:", paths)
