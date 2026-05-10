# Old Registries as Views — RG-9

**Phase:** RG-9 — Old Registries as Views
**Status:** CLOSED
**Date:** 2026-05-09
**Authority:** current_status (design closure)

## Purpose

Declare the architectural transition: the five original registry layers are now **views** of the unified Registry Control Plane, not competing sources of truth.

## Architecture Declaration

```
BEFORE (RG-0 baseline):
    Document Registry
    Artifact Registry
    Checker Registry
    Scanner Surfaces
    Aux Ledgers
    → all independent, split-brain, 0/10 invariants passing

AFTER (RG-1 through RG-9):
    Registry Control Plane (RegistryObject model)
        ↓
    Import Adapters (RG-2)
        ↓
    Reconciler (RG-3)
        ↓
    Generated Index (RG-8)
        ↓
    VIEWS (old registries repurposed):
        document-registry view
        artifact-registry view
        checker-registry view
        ownership view
        policy-activation view
        legacy-scope view
```

## Migration Status

| Source | Status | Notes |
|---|---|---|
| document-registry | View | Importer Active (RG-2). 249 entries. |
| artifact-registry | View | Importer Active (RG-2). 716 entries. |
| checker-registry | View | Auto-discovered (RG-2). 38 checkers. |
| aux ledgers | View | Imported (RG-2). 11 ledgers active. |
| scanner surfaces | View | T3 candidate (RG-2). 3 scanners. |
| ownership-manifest | View | 10 path patterns (RG-2 import). |
| policy-activation-ledger | View | Created RG-4. 0 records. |

## What Changed

- RG-4: policy-activation-ledger created (P0 gap closed)
- RG-5: 9 L0/L1 owner gaps filled
- RG-6: checker-coverage-manifest authority corrected
- RG-7: 137 pending docs classified into 5 buckets
- RG-8: unified generated index function

## What Did NOT Change

- Old JSONL files are NOT deleted
- Old checker scripts are NOT removed
- Legacy directories still need RG-5 scope identity (future)
- Pending docs still need per-bucket registration (RG-7A-E)
- Config surfaces still unregistered (future)

## Invariant

```
Old registries remain on disk → View of single Control Plane
One object model → Multiple import adapters → One reconciler → One generated index → Multiple views
```
