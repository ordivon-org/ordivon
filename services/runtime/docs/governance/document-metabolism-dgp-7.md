# Document Metabolism — DGP-7

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-7
Authority: current_status | Owner: Governance

## Purpose

Documents must die. They must be archived, superseded, or tombstoned with explicit reason and successor tracking. DGP-7 defines the metabolism rules that prevent document pile-up and stale truth leakage.

## Metabolism States

### archive_historical
Preserved historical record. Not current truth. Must have archive warning when referenced.
- authority: T4_ARCHIVE_HISTORICAL
- current_truth_allowed: False
- physical deletion: No

### superseded
Replaced by a newer document. Must declare successor.
- authority: T5_DEPRECATED_TOMBSTONED (by default)
- current_truth_allowed: False
- Requires: superseded_by (successor doc_id or path)

### deprecated
Still exists but actively discouraged. Gateway to tombstone.
- authority: T5_DEPRECATED_TOMBSTONED
- current_truth_allowed: False

### tombstoned
Explicitly dead. Must have reason or successor. Terminal state.
- authority: T5_DEPRECATED_TOMBSTONED
- current_truth_allowed: False
- Requires: tombstone_reason or superseded_by

### duplicate
Two or more documents claim the same current truth status.
- Finding: DEGRADED
- Resolution: supersession or dedup

### stale_current_truth
Current truth document past review_date without verification.
- Finding: DEGRADED; BLOCKED if > 2x staleness threshold

### out_of_scope
Excluded from governance. Not active, not archived, not deleted.
- authority: T6_OUT_OF_SCOPE
- current_truth_allowed: False

### reentry
A legacy_inactive or out_of_scope document returning to active governance.
- Requires: explicit reentry_condition, owner, review

## Ledgers

- `document-tombstone-ledger.jsonl`: Tractombstoned documents.
- `document-supersession-map.jsonl`: Tracts old→new successor relationships.

## Hard Invariants

1. No physical deletion without explicit tombstone record.
2. Tombstoned without reason → DEGRADED.
3. Superseded without successor → DEGRADED.
4. Archive must not be current_truth_allowed → BLOCKED (enforced by lifecycle-invariants).
5. Duplicate current truth → DEGRADED.
6. Stale current truth → DEGRADED.
7. Archive referenced by onboarding → archive warning required.
