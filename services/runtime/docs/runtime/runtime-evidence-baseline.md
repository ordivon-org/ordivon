# Runtime Evidence Baseline

Status: **BASELINE**
Date: 2026-04-28
Wave: E1
Tags: `runtime`, `evidence`, `checker`, `l9`

## Purpose

Define the structural invariants that runtime evidence objects must satisfy.
These invariants are checked by `scripts/check_runtime_evidence.py`.

## Checked Invariants

| # | Invariant | Scope |
|---|-----------|-------|
| 1 | ExecutionReceipt ORM has `request_id` column | Traceability |
| 2 | FinanceManualOutcome ORM requires `execution_receipt_id` | Receipt tethering |
| 3 | Plan receipt spec documents `broker_execution=false` | Plan-only safety |
| 4 | Review ORM has paired `outcome_ref_type`/`outcome_ref_id` | H-8R compliance |
| 5 | CandidateRule model has `lesson_ids` and `source_refs` | Wave B traceability |
| 6 | CandidateRule has no promote/accept/approve methods | Policy isolation |
| 7 | Checker script has no DB write operations | Read-only guarantee |

## Related Artifacts

| Artifact | Path |
|----------|------|
| Checker script | `scripts/check_runtime_evidence.py` |
| Checker tests | `tests/unit/runtime/test_runtime_evidence_checker.py` (11 tests) |
| Plan receipt spec | `docs/architecture/execution-request-receipt-spec.md` |
| Execution records ORM | `domains/execution_records/orm.py` |
| Finance outcome ORM | `domains/finance_outcome/orm.py` |
| Review ORM | `domains/journal/orm.py` |
| CandidateRule model | `domains/candidate_rules/models.py` |

## Limitations

- Static analysis only — does not query a live database.
- Cannot verify actual DB row consistency (requires runtime connection).
- Plan receipt checks are spec-document-based, not code-path-based.
