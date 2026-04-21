# Intelligence Run

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Flywheel critical
- [x] Anti-pollution critical
- [x] Reliability critical
- [x] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: Intelligence
- Type: Observability
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Layer Module Inventory](../architecture/layer-module-inventory.md)
- Related Files:
  - `domains/intelligence_runs/`
  - `orchestrator/workflows/analyze.py`
  - `intelligence/providers/hermes_agent_provider.py`

## 2. Purpose
- Why now: a real runtime path still needs a state-backed run record or failures and traces remain too easy to lose.
- Problem being solved: `AgentAction` captures AI output, but not the bounded runtime invocation lifecycle itself.
- If not done, what breaks or stays fake: Hermes can run, but there is no first-class record of pending/completed/failed runtime execution.
- What part of the system becomes stronger: Intelligence run observability and trace discipline.

## 3. Scope
### In Scope
- add a state-backed `IntelligenceRun` object
- persist success and failure run status for Hermes analyze
- expose run lineage in analyze metadata and audit payloads

### Out of Scope
- do not add list/query APIs yet
- do not add dashboard visualization yet
- do not add multi-task catalog support

## 4. Main Object
- Primary object: Intelligence Run
- Upstream dependency: intelligence task request
- Downstream effect: state trace, audit trace, future metrics
- Source of truth: State
- Whether side-effect exists: Yes
  The task persists runtime run records and error outcomes.

## 5. Loop Position
- Primary loop: Analyze Chain
- Step in loop: runtime invocation and trace persistence
- What comes before: context assembly and task contract build
- What comes after: analysis persistence, audit, report
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: State Record
- Secondary assets:
  - Audit Trail
  - Diagnostic Signal
- Where the asset will live:
  - `domains/intelligence_runs/`
  - analyze workflow metadata
- How it will be reused later: recommendation/review/report tasks can attach to the same run model.

## 7. Design Decision
- Chosen approach: store a minimal state-backed `IntelligenceRun` around the bounded Hermes task request.
- Alternatives rejected:
  - reusing `AgentAction` as the only runtime record
  - logging run lifecycle only in audit text
- Why this approach is smallest viable move: it captures the runtime lifecycle without forcing a broader workflow-run refactor.
- Boundary to preserve: Intelligence owns runtime execution trace, State owns persisted run truth.

## 8. Implementation Plan
1. add `IntelligenceRun` model, ORM, repository, and service
2. create pending run record before Hermes analyze execution
3. mark run completed or failed based on runtime outcome
4. surface `intelligence_run_id` in analyze metadata and audit payloads

## 9. Verification
- Unit tests: run repository create/update and DB bootstrap
- Integration tests: analyze success and Hermes unavailable failure both persist run status
- Manual checks: inspect analyze response metadata
- Failure mode checks: failed Hermes call leaves a persisted failed run
- Truthfulness checks: runtime errors do not disappear without a trace

## 10. Done Criteria
- [x] Hermes analyze creates a pending/completed run record
- [x] Hermes failure path persists a failed run record
- [x] analyze response metadata includes `intelligence_run_id`
- [x] at least one integration path proves run persistence on both success and failure

## 11. Risk Notes
- Main risk: conflating workflow runs with intelligence runs too early
- Drift risk: `IntelligenceRun` becoming a second `AgentAction`
- What this task might accidentally absorb: dashboard and query surface work
- Rollback plan: keep the run table isolated and remove only workflow hookups if needed

## 12. Follow-up
- Immediate next task: [T3 Core State Truth Inventory](./T3-core-state-truth-inventory.md)
- Deferred work: intelligence run query APIs and dashboard surfaces
- What this unlocks: real AI task run metrics and traceability
