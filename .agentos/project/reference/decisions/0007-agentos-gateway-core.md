---
status: approved
owner: project owner
approval_basis: user-request-2026-08-01-gateway-core
supersedes_scope: 0006:persistent-task-database-exclusion:gateway-run-registry-only
preserves: 0006:vendor-execution-plane,0005:direct-cli,0004:credential-boundary
---

# ADR 0007: AgentOS Gateway Core

- status: approved
- owner: project owner
- approval_basis: user-request-2026-08-01-gateway-core
- supersedes_scope: 0006:persistent-task-database-exclusion:gateway-run-registry-only
- preserves: 0006:vendor-execution-plane,0005:direct-cli,0004:credential-boundary

Gateway Core may maintain a local run registry under `AGENTOS_HOME/gateway/` to support queued runs, state, event replay, retry, cancellation, and preview-first pruning.

This is a limited exception to ADR 0006's persistent task database exclusion. The exception is only for Gateway run records and sanitized lifecycle events. It does not replace the vendor execution plane, direct CLI usage, project work contracts, Gate 2 review evidence, or credential boundaries.

Gateway workers reuse the existing AgentOS provider registry and `RuntimeRequest`/`InvocationEvent` contracts. They do not introduce a network listener, external database, queue broker, or alternate credential store.
