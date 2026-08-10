import re

with open("agentos/observability/plan_parser.py", "r") as f:
    text = f.read()

# 1. Update parse_exec_plan
old_parse_exec_plan = """def parse_exec_plan(text: str) -> ExecPlanSummary:
    return ExecPlanSummary(
        title=_find_h1(text),
        status=_find_meta_line(text, "상태"),
        reviewed=_find_meta_field(text, "reviewed"),
        active_agent=_find_meta_field(text, "active_agent"),
        active_session=_find_meta_field(text, "active_session"),
        dashboard_item_id=_find_meta_field(text, "dashboard_item_id"),
        git_branch=_find_meta_field(text, "git_branch") or _find_meta_field(text, "branch"),
        goal=_find_section(text, "목표"),
        user_result_summary=_find_h2_section(text, "사용자 결과 요약"),
        progress_snapshot=_find_h2_section(text, "진행 스냅샷"),
        worktree_info=_find_h2_section(text, "Worktree 정보"),
        last_review_entry=_find_last_review_entry(text),
        user_request=_find_meta_field(text, "user_request"),
        implementation_started_at=_find_meta_field(text, "implementation_started_at"),
        implementation_completed_at=_find_meta_field(text, "implementation_completed_at"),
        implementation_duration=_find_meta_field(text, "implementation_duration"),
    )"""

new_parse_exec_plan = """def parse_exec_plan(text: str) -> ExecPlanSummary:
    fm_match = re.search(r"^---\\s*\\n(.*?)\\n---\\s*(?:\\n|$)", text, re.DOTALL | re.MULTILINE)
    fm_data = {}
    if fm_match:
        for line in fm_match.group(1).split("\\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                fm_data[key.strip()] = val.strip()

    def get_meta(key: str, old_label: str = None) -> str:
        if fm_match and key in fm_data:
            return fm_data[key]
        if old_label:
            return _find_meta_line(text, old_label)
        return _find_meta_field(text, key)

    return ExecPlanSummary(
        title=_find_h1(text),
        status=get_meta("status", "상태"),
        reviewed=get_meta("reviewed"),
        active_agent=get_meta("active_agent"),
        active_session=get_meta("active_session"),
        dashboard_item_id=get_meta("dashboard_item_id"),
        git_branch=get_meta("git_branch") or get_meta("branch"),
        goal=_find_section(text, "목표"),
        user_result_summary=_find_h2_section(text, "사용자 결과 요약"),
        progress_snapshot=_find_h2_section(text, "진행 스냅샷"),
        worktree_info=_find_h2_section(text, "Worktree 정보"),
        last_review_entry=_find_last_review_entry(text),
        user_request=get_meta("user_request"),
        implementation_started_at=get_meta("implementation_started_at"),
        implementation_completed_at=get_meta("implementation_completed_at"),
        implementation_duration=get_meta("implementation_duration"),
    )"""

text = text.replace(old_parse_exec_plan, new_parse_exec_plan)

# 2. Update upsert_meta_field
old_upsert = """def upsert_meta_field(text: str, key: str, value: str) -> str:
    \"\"\"Set a `> key: value<br>` metadata line in an exec-plan's header block.

    Updates the line in place if `key` already exists (blank or filled);
    otherwise inserts a new line directly after the `active_session:` line,
    the fixed anchor point every exec-plan header already has. Used to write
    the GitHub dashboard card's identity back onto the plan document after a
    sync, so a reader can confirm which card a plan is linked to (and vice
    versa) without re-running a title-based lookup.
    \"\"\"
    field_re = re.compile(rf"^>\\s*{re.escape(key)}:\\s*.*$", re.MULTILINE)
    new_line = f"> {key}: {value}<br>"
    if field_re.search(text):
        return field_re.sub(new_line, text, count=1)

    anchor_re = re.compile(r"^>\\s*active_session:\\s*.*$", re.MULTILINE)
    match = anchor_re.search(text)
    if not match:
        return text
    insert_at = match.end()
    return text[:insert_at] + "\\n" + new_line + text[insert_at:]"""

new_upsert = """def upsert_meta_field(text: str, key: str, value: str) -> str:
    \"\"\"Set a metadata field in an exec-plan's header block (Frontmatter or old blockquote).\"\"\"
    # 1. Try YAML frontmatter
    fm_match = re.search(r"^---\\s*\\n(.*?)\\n---\\s*(?:\\n|$)", text, re.DOTALL | re.MULTILINE)
    if fm_match:
        fm_block = fm_match.group(1)
        field_re = re.compile(rf"^{re.escape(key)}:\\s*.*$", re.MULTILINE)
        new_line = f"{key}: {value}"
        
        if field_re.search(fm_block):
            new_block = field_re.sub(new_line, fm_block, count=1)
        else:
            anchor_re = re.compile(r"^active_session:\\s*.*$", re.MULTILINE)
            amatch = anchor_re.search(fm_block)
            if amatch:
                insert_at = amatch.end()
                new_block = fm_block[:insert_at] + "\\n" + new_line + fm_block[insert_at:]
            else:
                new_block = fm_block + "\\n" + new_line
        
        return text[:fm_match.start(1)] + new_block + text[fm_match.end(1):]

    # 2. Fallback to old blockquote format
    field_re = re.compile(rf"^>\\s*{re.escape(key)}:\\s*.*$", re.MULTILINE)
    new_line = f"> {key}: {value}<br>"
    if field_re.search(text):
        return field_re.sub(new_line, text, count=1)

    anchor_re = re.compile(r"^>\\s*active_session:\\s*.*$", re.MULTILINE)
    match = anchor_re.search(text)
    if not match:
        return text
    insert_at = match.end()
    return text[:insert_at] + "\\n" + new_line + text[insert_at:]"""

text = text.replace(old_upsert, new_upsert)

with open("agentos/observability/plan_parser.py", "w") as f:
    f.write(text)

print("done")
