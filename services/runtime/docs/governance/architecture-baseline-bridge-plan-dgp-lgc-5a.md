# Architecture Baseline Bridge Plan — DGP-LGC-5A

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-LGC-5A
Authority: supporting_evidence | Owner: Governance

## Decision: KEEP_ACTIVE_BRIDGE

`docs/architecture/architecture-baseline.md` is retained as an active bridge document. It serves as a historical-to-current architecture reference node with 20 unique referring files. It is NOT current truth by default.

## Reference Graph: 20 files

| Risk | Type | Files | Action |
|---|---|---|---|
| R2 | policy_dependency | 1 (constitution.md) | Manual review required — Trading phase |
| R1 | current_navigation | 1 (docs/README.md) | Keep reference |
| R1 | current_truth_registry | 1 (current-truth-entry-map) | Review when successor exists |
| R0 | architecture_dependency | 8 | Keep reference |
| R0 | historic/audit/workflow | 7 | Keep reference |
| R0 | product/registry | 2 | Keep reference |

## Bridge Status

- authority_tier: T2_SUPPORTING_EVIDENCE (not source_of_truth)
- current_truth_allowed: False
- lifecycle: active (bridge document)
- role: Historical architecture reference node for current system navigation

## What NOT to Infer

- This document is not standalone current Ordivon architecture truth.
- It contains legacy PFIOS/AegisOS context that may not describe current system state.
- For current architecture, see current truth entry map and current system map.
- Bridge docs cannot be archived until all navigation/dependency references are resolved.

## Successor Strategy

1. Future phase should create a current-architecture doc that supersedes the historical content.
2. Update docs/README.md and current-truth-entry-map to point to successor.
3. Then archive this document with supersession reason.

## Archive Conditions (NOT YET MET)

- All architecture_dependency refs resolved by successor (8 files)
- docs/README.md updated to point to successor
- current-truth-entry-map.jsonl updated
- policies/constitution.md reviewed (R2 — Trading phase required)

## Warning Banner Added

Warning banner added to top of architecture-baseline.md:
"**BRIDGE DOCUMENT** | DGP-LGC-5A | Not standalone current truth. For historical architecture context. See current-system-map and current truth entry map for active architecture docs."
