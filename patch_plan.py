text = open(".agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md").read()

# Check off tasks
text = text.replace("- [ ] **Step 1: independent principle audit evidence", "- [x] **Step 1: independent principle audit evidence")
text = text.replace("- [ ] **Step 2: full harness suite and project public verifier", "- [x] **Step 2: full harness suite and project public verifier")
text = text.replace("- [ ] **Step 3: reusable change의 durable evolution record", "- [x] **Step 3: reusable change의 durable evolution record")

# Fill in sections
sections = """## 구현 결과
- 기존 HMAC 서명 코드를 모두 제거하고 순수 artifact-only 검증으로 대체했습니다.
- `protected_change: true`인 계획에 대해 `harness-architect`의 명시적 승인과 범위 일치를 런타임에 검증하도록 구현했습니다.

## 사용 방법
- 계획 문서가 변경되거나 누락된 리뷰 증거가 있을 경우: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan <plan>` 을 실행하여 누락된 서명을 확인하고 다시 요청합니다.

## 완료 증거
- `bash .agents/skills/harness/run-all-tests/tests/run_all_tests.sh` -> 143 passed, 9 skipped
- `scripts/verify-public-test-suite.sh` -> PASS

## 아카이브 결정
- 모든 구현과 테스트, 진화 가시성 갱신을 성공적으로 마쳤으므로 '완료' 상태로 전환하여 아카이브합니다."""

import re
text = re.sub(r'## 구현 결과.*## 아카이브 결정\n\(구현 후 작성\)\n?', sections, text, flags=re.DOTALL)

open(".agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md", "w").write(text)
