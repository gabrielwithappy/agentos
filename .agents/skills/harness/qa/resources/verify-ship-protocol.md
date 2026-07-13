# VERIFY/SHIP Protocol

Harness execution guide for VERIFY (Alignment/Security/Regression) and SHIP (Quality/UX/Deploy) phases.

---

## VERIFY Phase

### Alignment Review

**Review Question**: "Did we build what was requested?"

- [ ] Plan vs implementation 1:1 comparison
- [ ] Misalignments documented
- [ ] No missing features

---

### Security/Bug Review

**Review Question**: "Is there anything dangerous?"

**Automated Tools:**
- `npm audit` (Node.js)
- `bandit` (Python)
- `lighthouse` (web performance)

**OWASP Top 10 Check:**
- [ ] No injection vulnerabilities
- [ ] No authentication flaws
- [ ] No sensitive data exposure
- [ ] No XXE vulnerabilities
- [ ] No access control flaws

**Finding Format:**
- File:line
- Description
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- Fix suggestion

---

### Improvement Review

**Review Question**: "Did improvements break anything?"

- [ ] All existing tests pass
- [ ] Existing features work normally
- [ ] New code matches existing patterns

---

### VERIFY_GATE Checklist

- [ ] Implementation = Requirements
- [ ] CRITICAL issues: 0
- [ ] HIGH issues: 0
- [ ] No regressions

**Gate failure → Return to implementation fix**

---

## SHIP Phase

### Code Quality Review

**Review Question**: "Does it meet quality standards?"

- [ ] lint passes
- [ ] type check passes
- [ ] test coverage >= 80%

---

### UX Flow Verification

- [ ] End-to-end user journey test
- [ ] Error states verified
- [ ] Loading states verified
- [ ] Accessibility compliance (WCAG 2.1 AA)

---

### Related Issues Review

**Review Question**: "Did we break anything elsewhere?"

- [ ] Issues discovered during review checked
- [ ] Related areas not broken
- [ ] Deferred items documented (next sprint)

---

### Deployment Readiness Review

**Review Question**: "Is this ready to deploy?"

- [ ] No hardcoded secrets
- [ ] Environment variables documented
- [ ] Migrations safe
- [ ] Rollback possible
- [ ] Monitoring ready

---

### SHIP_GATE Checklist

- [ ] All quality checks pass
- [ ] UX verified
- [ ] Related issues resolved
- [ ] Deployment checklist complete
- [ ] **User final approval**

**Gate failure → Return to appropriate phase based on failure type**
