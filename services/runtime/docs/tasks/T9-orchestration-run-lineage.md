# Orchestration Run Lineage

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Flywheel critical
- [x] Anti-pollution critical
- [x] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: Orchestration
- Type: Observability
- Priority: P1
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [State Truth Inventory](../architecture/state-truth-inventory.md)
  - [Workflow Run Lineage Spec](../architecture/workflow-run-lineage-spec.md)
- Related Files:
  - `domains/workflow_runs/`
  - `orchestrator/runtime/engine.py`
  - `orchestrator/workflows/analyze.py`

## 2. Purpose
- Why now: intelligence runs exist, but the workflow itself still had no canonical run object for step status and failure reason.
- Problem being solved: the system could trace AI invocation but not the analyze workflow as an orchestrated run.
- If not done, what breaks or stays fake: workflow-level timing, failure step, and orchestration lineage remain implicit.
- What part of the system becomes stronger: Orchestration as a real control surface with state-backed run truth.

## 3. Scope
### In Scope
- add state-backed workflow run object
- track step status in analyze workflow
- persist success and failure run lineage
- expose `workflow_run_id` through metadata and audit

### Out of Scope
- do not add review workflow run yet
- do not build retry/fallback policy yet
- do not build workflow run query API yet

## 4. Main Object
- Primary object: Workflow Run
- Upstream dependency: analyze request and orchestrator step execution
- Downstream effect: traceability, lineage, and future retry/fallback policy
- Source of truth: State
- Whether side-effect exists: Yes

## 5. Loop Position
- Primary loop: Analyze Chain
- Step in loop: workflow execution and step-level trace
- What comes before: state transition hardening and intelligence run persistence
- What comes after: broader lineage graph and workflow retry/fallback work
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Workflow Run Record
- Secondary assets:
  - step status trace
  - failed-step persistence
  - workflow lineage spec
- Where the asset will live:
  - `domains/workflow_runs/`
  - `docs/architecture/`
- How it will be reused later: review and cross-workflow orchestration can attach to the same run model.

## 7. Design Decision
- Chosen approach: keep step status in memory during the run, then persist a completed or failed `WorkflowRun` record.
- Alternatives rejected:
  - relying only on `IntelligenceRun`
  - writing partial workflow state on every step without rollback discipline
- Why this approach is smallest viable move: it preserves workflow atomicity while still leaving a durable failure trace.
- Boundary to preserve: workflow run lineage describes orchestration, not intelligence reasoning or execution receipts.

## 8. Implementation Plan
1. add workflow run model, ORM, repository, and service
2. create a pending workflow run at orchestrator start
3. capture step completion and failure statuses
4. persist completed or failed workflow run and expose `workflow_run_id`

## 9. Verification
- Unit tests: `tests/unit/test_workflow_run_repository.py`
- Integration tests:
  - `tests/integration/test_workflow_run_lineage_api.py`
  - `tests/integration/test_analyze_transaction.py`
- Manual checks: inspect analyze response metadata and audit payload
- Failure mode checks: workflow failure persists failed step and does not commit partial analysis state
- Truthfulness checks: workflow errors leave a failed run instead of disappearing from trace

## 10. Done Criteria
- [x] analyze has a state-backed workflow run object
- [x] step statuses are persisted on success and failure
- [x] `workflow_run_id` is exposed through metadata and audit
- [x] failure path preserves run trace without preserving partial business writes

## 11. Risk Notes
- Main risk: workflow run becomes a dumping ground for unrelated lineage data
- Drift risk: future workflows may bypass the run model if it is not adopted consistently
- What this task might accidentally absorb: workflow retry/fallback design
- Rollback plan: keep the run model isolated to orchestrator and analyze workflow

## 12. Follow-up
- Immediate next task: state lineage / trace graph
- Deferred work: retry/fallback and cross-workflow coordination
- What this unlocks: workflow-level traceability and future orchestration recovery rules
