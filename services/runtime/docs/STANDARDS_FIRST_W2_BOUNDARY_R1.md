# Standards-First W2 Runtime Boundary R1

Date: 2026-09-19
Status: ACCEPTED_BOUNDARY; NO_WORKFLOW_CUTOVER

## Decision

Runtime remains the local physical execution/effect-commit authority. It is not a replacement for Temporal, BPMN/DMN, a business scheduler, or a generic controller platform.

This boundary is intentionally narrow:

- Temporal owns long-lived durable application/business process orchestration when required.
- controller/operator patterns own desired/current reconciliation semantics in the domain that owns that state.
- Saga/compensating transactions own cross-service compensation semantics.
- HTTP/provider contracts own retry/idempotency semantics for external effects.
- Runtime owns exact local admission, Job/Attempt identity, physical dispatch, process-tree ownership, bounded execution evidence, cancellation, and reconciliation against physical executor reality.

## Keep

- stable request identity and exact replay;
- durable Job and Attempt identity;
- at-most-once physical dispatch per Attempt;
- source/executable/input commitment;
- process-tree ownership;
- terminal evidence;
- explicit lost/orphaned/unknown states;
- exact reconciliation of Registry, runner result, systemd/cgroup and Windows Job Object evidence;
- structured effect contracts only when Runtime actually implements and verifies their deduplication/read-back semantics.

## Do not add

- durable business workflow semantics;
- hidden queues or scheduler policy;
- generic timers/signals;
- cross-domain TaskFlow;
- generic compensation engine;
- automatic retry of opaque external effects;
- caller-asserted idempotency/effect classes for arbitrary execution.

## Important distinction

```text
Runtime reconciliation
= reconcile Runtime-owned durable intent/evidence with physical executor reality

Temporal workflow recovery
= resume durable application process state

Saga compensation
= issue new compensating domain effects

domain controller
= drive current domain state toward desired domain state
```

These are related patterns but not interchangeable authorities.

## Retry rule

A repeated client request with the same stable Runtime request identity may resolve to the original committed Job.

A second physical dispatch is a new Attempt.

A second external-world effect is never justified merely because process execution was retried. External effect safety must come from the effect owner through idempotency, deduplication identity, read-back/reconciliation, or explicit compensation.

## W3 handoff

The remaining high-value Runtime work is formal verification, not workflow expansion. Prefer TLA+ models for:
- admission vs dispatch;
- cancellation/reconciliation/late-result races;
- lease/generation fencing;
- unknown Registry commit state;
- recovery publication safety.
