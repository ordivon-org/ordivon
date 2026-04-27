# DB-Backed Runtime Evidence Audit

Status: **DOCUMENTED**
Date: 2026-04-28
Wave: E2
Tags: `runtime`, `evidence`, `audit`, `db-backed`, `e2`

## Purpose

Validate that Ordivon's runtime evidence chain is structurally intact by
querying the database directly. Complements the static checker (E1) with
real data validation.

## Scope

- Read-only audit of DecisionIntake → ExecutionReceipt → Outcome → Review → Lesson → CandidateRule chain
- Operates on any SQLAlchemy Session
- Provides standalone `audit_evidence_chain(db)` function

## Non-Goals

This audit does NOT:
- Write to the database
- Modify schema or run migrations
- Connect to external services
- Execute broker/order/trade operations
- Promote CandidateRules to Policy

## Audited Object Chain

```
DecisionIntake
  → ExecutionReceipt (plan receipt, broker_execution=false)
  → FinanceManualOutcome (execution_receipt_id)
  → Review (outcome_ref_type + outcome_ref_id)
  → Lesson (source_refs → review/outcome)
  → CandidateRule (draft, lesson_ids + source_refs)
  → AuditEvent (coverage check)
```

## Checks Performed

| # | Check | What it catches |
|---|-------|----------------|
| 1 | ExecutionReceipt.request_id non-empty | Untraceable succeeded receipts |
| 2 | Plan receipt broker_execution=false | Trade execution in plan-only context |
| 3 | Outcome.execution_receipt_id valid | Broken receipt references |
| 4 | Review outcome_ref_type/id paired | Mismatched outcome references |
| 5 | Review outcome_ref resolves | Dangling outcome references |
| 6 | Lesson source_refs traceable | Lessons without review reference |
| 7 | CandidateRule draft has lesson_ids + source_refs | Drafts without source tracing |
| 8 | CandidateRule no accepted_candidate | Auto Policy promotion |
| 9 | AuditEvent coverage | Missing key event types |

## Read-Only Guarantee

The audit function:
- Does NOT call `db.add()`, `db.commit()`, `db.delete()`, `db.flush()`
- Does NOT execute raw SQL writes
- Does NOT run migrations
- Verified by `test_audit_is_read_only` (object counts unchanged post-audit)

## Test Evidence

- `tests/integration/test_runtime_evidence_db_audit.py` — 6 tests
  - valid chain audit passes
  - broken receipt reference detected
  - broken outcome_ref detected
  - CandidateRule without source_refs detected
  - audit is read-only
  - no broker/order/trade imports

## Limitations

- Requires a live database session
- Cannot verify cross-table consistency beyond foreign key checks
- Does not validate semantic correctness of payload contents
- Audit event type check only warns on missing expected types in non-empty DB

## Next Recommended Wave

E3 — Runtime Evidence Reporter: generate a machine-readable evidence report
from the audit results, suitable for CI integration and trend tracking.
