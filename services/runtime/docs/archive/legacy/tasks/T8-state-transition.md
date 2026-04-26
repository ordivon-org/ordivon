# State Transition

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Anti-pollution critical
- [x] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: State
- Type: Boundary
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [State Truth Inventory](../architecture/state-truth-inventory.md)
  - [State Transition Spec](../architecture/state-transition-spec.md)
- Related Files:
  - `domains/strategy/state_machine.py`
  - `domains/journal/state_machine.py`
  - `domains/intelligence_runs/state_machine.py`

## 2. Purpose
- Why now: recommendation had a state machine, but review and intelligence run still changed status through service-local mutation.
- Problem being solved: core state objects did not consistently enforce transition rules.
- If not done, what breaks or stays fake: state truth would continue to permit silent invalid transitions.
- What part of the system becomes stronger: State as a controlled source of truth instead of a passive storage layer.

## 3. Scope
### In Scope
- add explicit transition rules for review
- add explicit transition rules for intelligence run
- enforce transition validation in services
- document the currently covered state objects

### Out of Scope
- do not introduce workflow run state yet
- do not redesign outcome lifecycle
- do not build a generic meta state-machine framework

## 4. Main Object
- Primary object: State Machine
- Upstream dependency: existing persisted recommendation, review, and intelligence run rows
- Downstream effect: safer lifecycle writes and clearer lineage semantics
- Source of truth: State
- Whether side-effect exists: Yes

## 5. Loop Position
- Primary loop: Analyze Chain
- Step in loop: runtime and review lifecycle transition
- What comes before: object creation and state truth inventory
- What comes after: workflow run and lineage modeling
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: State Machine
- Secondary assets:
  - transition spec
  - failure-path validation
- Where the asset will live:
  - `domains/`
  - `docs/architecture/`
- How it will be reused later: workflow run, outcome backfill, and review lifecycle work can extend the same transition discipline.

## 7. Design Decision
- Chosen approach: add object-specific state machines where state already exists in live code paths.
- Alternatives rejected:
  - leaving transition rules implicit in services
  - forcing a generic framework before object semantics are stable
- Why this approach is smallest viable move: it hardens current fact objects without broad architectural churn.
- Boundary to preserve: state transitions describe truth mutation, not governance decisions or execution receipts.

## 8. Implementation Plan
1. add review state machine
2. add intelligence run state machine
3. enforce transitions in services
4. validate success and invalid-transition paths

## 9. Verification
- Unit tests:
  - `tests/unit/test_review_state_machine.py`
  - `tests/unit/test_intelligence_run_state_machine.py`
- Integration tests:
  - `tests/unit/test_review_service.py`
  - `tests/unit/test_intelligence_run_repository.py`
  - `tests/integration/test_audit_events.py`
- Manual checks: compare persisted statuses with audit and service output
- Failure mode checks: invalid terminal transitions and missing intelligence run ids
- Truthfulness checks: state writes now fail honestly on invalid transition instead of silently mutating

## 10. Done Criteria
- [x] review transitions are explicit
- [x] intelligence run transitions are explicit
- [x] services enforce transition validation
- [x] failure path is covered by tests

## 11. Risk Notes
- Main risk: current transition rules may still be narrower than future product semantics
- Drift risk: new services may bypass state machines if the pattern is not kept in review
- What this task might accidentally absorb: full workflow run state design
- Rollback plan: object-local state machines keep rollback scope small

## 12. Follow-up
- Immediate next task: workflow run record and run lineage
- Deferred work: outcome lifecycle state machine
- What this unlocks: trace and run-state work can rely on explicit transition rules
