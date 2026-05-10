# Pending Registration Triage — RG-7

**Phase:** RG-7 — Pending Registration Triage
**Status:** CLASSIFIED (closure deferred to per-bucket execution)
**Date:** 2026-05-09
**Authority:** proposal

## Problem

RG-0 identified 137 documents in `document-registry-exclusions.json` classified as `pending_registration` with no concrete plan for resolution.

## Classification

The 137 pending documents fall into 5 natural buckets:

| Bucket | Path | Count | Strategy |
|---|---|---|---|
| architecture-legacy | docs/architecture/ | 48 | Archive or register selectively |
| runtime-receipts | docs/runtime/ | 38 | Bulk-register as receipts (L2, supporting_evidence) |
| product-proposals | docs/product/ | 31 | Register as proposals (L4, proposal authority) |
| paper-trades | docs/runtime/paper-trades/ | 11 | Bulk-register as runtime receipts |
| governance-ops | docs/governance/ | 7 | Register individually (mixed authority levels) |
| tooling | scripts/ | 2 | Out of scope (not docs/) |

## Bucket Strategy

### architecture-legacy (48)
Mix of legacy AegisOS design docs and Ordivon-era architecture files. Risk: many may be superseded. Approach: classify each as `archive_historical` or register with `authority = current_status` depending on active reference count.

### runtime-receipts (38)
PV-*/ADP-*/HAP-*/OGAP-* closure receipts. All are `supporting_evidence`, `L2_EVIDENCE`. Safe to bulk-register.

### product-proposals (31)
Product docs, stage notes, roadmap. Authority = `proposal`, layer = `L4_PRODUCT`. Safe to register.

### paper-trades (11)
PT-001 through PT-011. All `supporting_evidence`, `L2_EVIDENCE`. Safe to bulk-register.

### governance-ops (7)
Mixed — staleness audit, debt policy, wiki index, scope drift doc. Needs individual assessment.

### tooling (2)
`scripts/audit_ordivon_verify_public_wedge.py` and `scripts/dryrun_ordivon_verify_public_repo.py` — these are scripts, not docs. Remove from exclusion list or register in artifact-registry only.

## Execution Plan

```
RG-7A: Bulk-register runtime-receipts (38) + paper-trades (11) — 49 docs
RG-7B: Register product-proposals (31)
RG-7C: Triage architecture-legacy (48) — classify each
RG-7D: Register governance-ops (7) individually
RG-7E: Remove tooling scripts (2) from doc exclusions list
```

## Status

RG-7 is a **triage phase** — it classifies the backlog and defines per-bucket strategies. Actual registration will be executed in RG-7A through RG-7E sub-phases as time and priority allow. None of these 137 docs are BLOCKED — they are DEGRADED (unregistered but known).

## Validation

```
Doc-registry checker: continues to flag unregistered docs — expected behavior.
No current-truth impact.
```
