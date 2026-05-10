# Document Lifecycle Governance — DGP-2

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-2
Authority: current_status | Owner: Governance

## Purpose

Bridge the existing document lifecycle model (defined in `document-lifecycle.md`, DG-1) with the Registry Control Plane's `LifecycleState` enum. This doc defines how lifecycle states interact with authority tiers, owner requirements, freshness rules, and RCP reconciler checks.

It does NOT replace `document-lifecycle.md` — it adds the RCP operationalization layer.

## Lifecycle State → RCP Integration

| Lifecycle State | Allowed Authority Tiers | current_truth_allowed | Owner Required | Review Required | New AI Readable |
|---|---|---|---|---|---|
| draft | T3_CANDIDATE_PROPOSAL, T6_OUT_OF_SCOPE | False | Recommended | No | With caution |
| candidate | T3_CANDIDATE_PROPOSAL | False | Recommended | Yes (proposal review) | With caution |
| active | T0, T1, T2 | Depends on tier | T0/T1: Required | Yes (stale_after_days) | Yes |
| stable | T0, T1, T2 | Depends on tier | T0/T1: Required | Yes (stale_after_days) | Yes |
| generated | T2_SUPPORTING_EVIDENCE | False | Optional | Auto-generated | Yes (as generated_view) |
| archived | T4_ARCHIVE_HISTORICAL | False | Optional | No | With archive warning |
| deprecated | T5_DEPRECATED_TOMBSTONED | False | Optional | No | With deprecation warning |
| tombstoned | T5_DEPRECATED_TOMBSTONED | False | Optional | No | No (requires tombstone_reason) |
| legacy_inactive | T6_OUT_OF_SCOPE | False | Optional | No | No (requires reentry condition) |
| out_of_scope | T6_OUT_OF_SCOPE | False | No | No | No |

## Hard Invariants (enforced by reconciler)

1. generated document cannot be source_of_truth.
2. archived document cannot be current_truth_allowed.
3. tombstoned document requires tombstone_reason or superseded_by.
4. superseded document requires superseded_by.
5. active T0/T1 document requires owner and review_date or last_verified.
6. out_of_scope document cannot be current_truth_allowed.
7. legacy_inactive document requires reentry_condition.

## Valid Transitions

```
draft → candidate, draft → archived, draft → legacy_inactive
candidate → active, candidate → archived
active → stable, active → deprecated, active → archived
stable → deprecated, stable → archived
generated → archived (when source data changes)
archived → tombstoned (when superseded or obsolete)
deprecated → tombstoned
tombstoned → (terminal — no outgoing)
legacy_inactive → out_of_scope (formal exclusion)
```

## Invalid Transitions (BLOCKED)

```
archived → active (must be explicitly re-registered as new doc)
tombstoned → * (terminal)
generated → active (generated views cannot become self-authorizing)
out_of_scope → active (requires reentry governance)
```

## Staleness Rules

| Authority Tier | Max Days Without Verification | Consequence |
|---|---|---|
| T0_SOURCE_OF_TRUTH | 7-30 days (configurable) | DEGRADED if stale; BLOCKED if > 2x stale |
| T1_CURRENT_STATUS | 30-90 days | DEGRADED if stale |
| T2_SUPPORTING_EVIDENCE | 90-180 days | Advisory warning |
| T3+ | N/A | No staleness enforcement |

## RCP Integration

The reconciler's `_check_owner_gaps` already enforces owner requirements per lifecycle state and authority tier. DGP-2 adds:

- `_check_lifecycle_invariants`: generated/archived/tombstoned/superseded boundary checks
- `document-lifecycle-ledger.jsonl`: machine-readable lifecycle state tracking
- Schema validation for lifecycle ledger entries

## Relationship to document-lifecycle.md (DG-1)

This doc is the RCP operationalization of the DG-1 lifecycle model. DG-1 defines the conceptual model; DGP-2 makes it machine-checkable through the Registry Control Plane. When the two conflict, DGP-2 takes precedence for RCP enforcement; DG-1 remains the conceptual reference.
