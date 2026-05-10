# data/ Quarantine Boundary — DGP-LGC-2A

Status: **CLOSED** | Date: 2026-05-09 | Phase: DGP-LGC-2A
Authority: supporting_evidence | Owner: Governance

## Action: NO-OP (already quarantined)

All 19 SQLite/DuckDB quarantine candidates from LGC-2 are already excluded by .gitignore:

| Pattern | .gitignore Line | Covers |
|---|---|---|
| *.db | Line ~2 | All 16 .db files in data/ |
| data/*.duckdb | Line 14 | All 3 .duckdb files in data/ |
| *.sqlite | NOT present | 0 .sqlite files found (all are .db) |

## Re-scan Confirmation

Zero references found from src/, tests/, or scripts/ for any of the 19 candidates. Files are runtime caches, local databases, and historical exports — not inputs to any active code path.

## Git Tracking Status

- 10 tracked files in data/ — ALL are JSON eval baselines/datasets (keep_stateful)
- 0 tracked .db/.duckdb files — all already gitignored
- No tracked file is a quarantine candidate

## What Was NOT Changed

- NO files deleted
- NO files moved
- NO .gitignore changes needed (already correct)
- NO git rm executed
- db/ untouched
- data/openapi_snapshot_baseline.json retained (script-referenced)
- SQLite contents untouched

## Future LGC-2B Removal Criteria

If deletion is ever desired for the 19 SQLite candidates:
1. Confirm they remain zero-reference
2. Confirm they are not required for local development
3. Use `git rm --cached` only if any become tracked
4. Rollback: restore from OS trash or re-clone
5. Must be explicitly authorized in a future phase

## Verification

```
184 tests passed
ordivon-verify document-governance --check: 0 BLOCKED, 0 DEGRADED
```
