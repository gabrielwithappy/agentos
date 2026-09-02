text = open(".agents/skills/harness/writing-plans/tests/test_plan_review_scope.py").read()
text = text.replace(
'''    text = text.replace("> reviewed: true<br>", "> reviewed: true<br>\\n> **protected_change:** true<br>")''',
'''    text = text.replace("> reviewed: true<br>", "> reviewed: true<br>\\n> **protected_change:** true<br>")
    text += "\\n- declared protected paths: `manifest update`"'''
)
text = text.replace(
'''"authorized_scope": list(review.PROTECTED_REVIEW_SCOPE)''',
'''"authorized_scope": ["manifest update"]'''
)
open(".agents/skills/harness/writing-plans/tests/test_plan_review_scope.py", "w").write(text)
