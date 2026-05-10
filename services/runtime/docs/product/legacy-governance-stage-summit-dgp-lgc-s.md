# Legacy Governance — Stage Summit (DGP-LGC-S)

Status: **CLOSED_AS_GOVERNED_LEGACY** | Date: 2026-05-09 | Phase: DGP-LGC-S
Authority: current_status (for DGP-LGC state) | Evidence role: supporting_evidence
Owner: Governance

## Executive Status

**DGP-LGC: CLOSED_AS_GOVERNED_LEGACY**

PFIOS/AegisOS legacy material has been discovered, classified, bounded, and routed across the LGC phase chain. Legacy surfaces may still exist, but they no longer silently define Ordivon current truth, active architecture, AI onboarding, or execution boundaries. Every legacy object now has identity, lifecycle, authority boundary, and a routing decision.

This is a governed-legacy closure claim, not a removal claim. No files were deleted. No runtime behavior changed. No migration history was rewritten.

## Phase Chain: 12 CLOSED + 1 PARTIAL

| Phase | Status | Action |
|---|---|---|
| LGC-0 | CLOSED | Reality freeze: 26 dirs, 209 terms, 4 artifact classes |
| LGC-1 | CLOSED | build/dist no-op (already gitignored) |
| LGC-2 | CLOSED | data/ 30 files classified, zero deletion |
| LGC-2A | CLOSED | SQLite/DuckDB no-op (already gitignored) |
| LGC-3 | PARTIAL | 1 doc archived, architecture-baseline retained (32 active refs) |
| LGC-4 | CLOSED | 4 LGC docs cleaned, 16→0 terms |
| LGC-5 | CLOSED | 122+ files triaged, 0 execution |
| LGC-5A | CLOSED | Bridge plan: 20 active refs normalized, KEEP_ACTIVE_BRIDGE |
| LGC-5B | CLOSED | 1 rename, 2 preserved, 3 reclassified keep-legacy-qualified |
| LGC-5C | CLOSED | 18 scripts: 12 active, 6 tools, 0 quarantine |
| LGC-5D | CLOSED | 20 tests: 0 assertion risk |
| LGC-5E | CLOSED | Policy R4 + alembic R3, do-not-edit boundaries |
| LGC-5F | CLOSED | 27 source files: 25 legacy_inactive, 2 comments |

### LGC-3 PARTIAL Absorption

LGC-3 archive action for architecture-baseline.md remains unresolved because the document has active references. This unresolved action was absorbed by LGC-5A, which reclassified architecture-baseline.md as KEEP_ACTIVE_BRIDGE with explicit bridge boundaries, owner routing, and future archive conditions. The overall legacy line is closed as governed even though one archive action is intentionally PARTIAL.

### Count Normalizations

**architecture-baseline references: 34 → 20**. Initial LGC-5 scan counted 34 raw grep matches across all files. LGC-5A normalized to 20 active bridge references after excluding archive paths, duplicate lines, registry metadata entries, and audit/triage artifacts created by LGC phases.

**Safe-rename candidates: 6 → 1 renamed, 2 preserved, 3 reclassified**. LGC-5 triage initially flagged 6 files as safe_doc_rename_future. LGC-5B found: 1 file had a single safe rename (docs/README.md: "Ordivon/PFIOS"→"Ordivon"), 2 were intentionally preserved (docs/ai/README.md already says "PFIOS/AegisOS are historical", hermes-model-layer-integration.md's 16 PFIOS refs are architecture context), and 3 were reclassified as keep-legacy-qualified after content inspection.

**Tests: 186 → 184 passed**. Delta of 2 tests: removed during the deprecated reconciler check cleanup in which LEDger-schema-artifact-gap and registry-self-gap were retired from the check registry.

## What Changed

- architecture-baseline.md: BRIDGE DOCUMENT banner added, not standalone truth
- docs/README.md: one "Ordivon/PFIOS" → "Ordivon"
- 1 historical doc archived to docs/archive/legacy/
- 4 LGC audit docs terminology cleaned (16→0 legacy terms)
- 26 directories in legacy-scope-manifest: legacy_inactive, re-entry conditions defined
- data/: 30 files classified (1 keep, 2 historical, 27 quarantine — already gitignored)
- 436 document-registry entries tracking all governed objects
- 13 reconciler checks active, 0 BLOCKED, 0 DEGRADED

## What Did NOT Change

- No source code behavior changed
- No script behavior changed
- No test assertions changed
- No alembic migrations edited
- No policies/trading_limits.yaml edited
- No files deleted from repo
- No legacy directories moved
- No database migration run
- No authorization semantics changed

## PFIOS/AegisOS Terminology: GOVERNED, NOT ERASED

| Category | Count | Status |
|---|---|---|
| Deferred docs (keep-legacy-qualified) | 82 | Historical context retained |
| Legacy directories | 26 | legacy_inactive in manifest |
| Script references | 18 | Classified, not renamed |
| Test references | 20 | Classified, 0 assertion risk |
| Source references | 27 | 25 legacy_inactive, 2 comments |
| Policy/alembic | 2 | Do-not-edit boundaries |
| Active docs cleaned | 5 | 16→0 terms (LGC self-docs + README) |

## Key Boundaries

- **architecture-baseline.md**: Active bridge document. Not current truth. Archive requires successor and reference resolution.
- **policies/trading_limits.yaml**: R4. Outside DGP scope. Requires Trading Pack phase.
- **alembic/env.py**: R3. Migration record. Do not edit.
- **data/ and db/**: Stateful artifacts. Not generated. Not deletable.
- **26 legacy dirs**: Legacy_inactive. Re-entry requires explicit manifest conditions.

## Verification

```
document-governance --check: PASS (0 BLOCKED, 0 DEGRADED, 269 ROUTED)
registry-index --check: PASS
Tests: 184 passed
Doc-registry: 436 entries
```
## What NOT to Infer

- Legacy governed does NOT mean legacy removed.
- PFIOS/AegisOS still exist in the repository.
- 0 BLOCKED does NOT mean 0 future migration work.
- This summit is context compression, NOT permanent truth.
- PASS does NOT authorize merge/release/deploy.

## Non-Authorization Boundary

This stage summit is supporting_evidence. It does not authorize any change to runtime, database, policy, trading, or deployment behavior. It is a snapshot of DGP-LGC state for legacy governance audit purposes.
