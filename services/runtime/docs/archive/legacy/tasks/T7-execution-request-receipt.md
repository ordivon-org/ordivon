# Execution Request / Receipt

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
- Layer: Execution
- Type: Enablement
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Execution Action Catalog](../architecture/execution-action-catalog.md)
  - [Execution Request / Receipt Spec](../architecture/execution-request-receipt-spec.md)
- Related Files:
  - `domains/execution_records/`
  - `orchestrator/workflows/analyze.py`
  - `capabilities/workflow/analyze.py`

## 2. Purpose
- Why now: execution actions were named, but there was still no first-class request / receipt object to show what actually happened when a consequential action ran.
- Problem being solved: report writing remained a consequential side-effect without an execution request and receipt trail.
- If not done, what breaks or stays fake: execution would remain hidden in workflow steps and state would still have no receipt-backed truth object.
- What part of the system becomes stronger: Execution, State, and audit traceability across a real action family.

## 3. Scope
### In Scope
- introduce execution request and receipt models
- persist request / receipt for `analysis_report_write`
- expose request / receipt ids through metadata and audit

### Out of Scope
- do not objectify every execution family
- do not build a full adapter platform
- do not introduce external integrations

## 4. Main Object
- Primary object: Execution Receipt
- Upstream dependency: side-effect boundary approval and workflow action context
- Downstream effect: state traceability and future receipt-backed execution hooks
- Source of truth: State
- Whether side-effect exists: Yes

## 5. Loop Position
- Primary loop: Execution Loop
- Step in loop: request -> side-effect -> receipt
- What comes before: action classification and governance boundary
- What comes after: broader receipt rollout and state-backed execution hooks
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Execution Receipt
- Secondary assets:
  - Execution Request
  - request / receipt spec
  - analyze-path execution trace
- Where the asset will live:
  - `domains/execution_records/`
  - `docs/architecture/`
- How it will be reused later: the same pattern can be extended to recommendation, review, validation, and intelligence-related execution families.

## 7. Design Decision
- Chosen approach: start with the most concrete artifact write family, `analysis_report_write`.
- Alternatives rejected:
  - waiting until all execution families are ready
  - modeling receipt only in audit payload
- Why this approach is smallest viable move: it proves the pattern on a real main-chain side-effect without rewriting the whole execution layer.
- Boundary to preserve: execution request / receipt records describe action execution, not governance decisions or intelligence reasoning.

## 8. Implementation Plan
1. add request / receipt models, ORM, repository, and service
2. wire `analysis_report_write` through request / receipt persistence
3. propagate ids into analysis metadata, audit payload, and capability response metadata
4. validate success and failure paths

## 9. Verification
- Unit tests: `tests/unit/test_execution_record_service.py`
- Integration tests:
  - `tests/integration/test_execution_request_receipt_api.py`
  - `tests/integration/test_analyze_transaction.py`
- Manual checks: compare analyze response metadata with DB rows and audit payload
- Failure mode checks: metadata update failure produces failed receipt and compensation
- Truthfulness checks: no execution success is reported without a persisted request / receipt pair

## 10. Done Criteria
- [x] one real execution family has request / receipt objects
- [x] request / receipt rows persist in state
- [x] success and failure paths are both covered
- [x] audit and metadata can reference request / receipt ids

## 11. Risk Notes
- Main risk: treating receipt as a universal abstraction before other families are understood
- Drift risk: mixing intelligence persistence and external execution under one receipt policy too early
- What this task might accidentally absorb: full execution adapter rollout
- Rollback plan: keep scope limited to the report-write family

## 12. Follow-up
- Immediate next task: extend request / receipt to `recommendation_generate` or `analysis_metadata_update`
- Deferred work: execution adapter consolidation
- What this unlocks: state-backed receipt records and future execution state hooks
