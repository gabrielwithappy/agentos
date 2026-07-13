# PLAN Phase Protocol

Harness execution guide for the planning phase (Strategy/Review/Simplicity).

---

## Create Plan

### Tasks
- Define scope, features, architecture
- Apply "Think Before Coding" principle
- Present alternatives, don't assume

### Outputs
- Task decomposition (P0/P1/P2 priority)
- Agent assignments
- API contracts (if needed)

---

## Plan Review (Completeness)

### Review Question
"Is anything missing?"

### Checklist
- [ ] All requirements mapped to plan
- [ ] Dependencies specified
- [ ] Edge cases considered

---

## Review Verification (Meta Review)

### Review Question
"Was the review done properly?"

### Checklist
- [ ] Self-verify previous review was sufficient
- [ ] No review gaps confirmed
- [ ] No circular logic

---

## Over-Engineering Check (Simplicity)

### Review Question
"Is this over-engineered?"

### Checklist
- [ ] Asked "Is this needed for MVP?" for each component
- [ ] Speculative features removed
- [ ] No "might need later" code

---

## PLAN_GATE Checklist

Final verification before completing plan:
- [ ] Acceptance criteria defined
- [ ] Assumptions documented
- [ ] Alternatives considered (min 2 for major decisions)
- [ ] Over-engineering review completed
- [ ] Ready for user confirmation

**Gate failure → Return to initial planning to revise**
