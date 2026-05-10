# data/ Stateful Classification — DGP-LGC-2

Status: **CLOSED** | Date: 2026-05-09 | Phase: DGP-LGC-2
Authority: supporting_evidence | Owner: Governance

## Action: CLASSIFIED (no files deleted or moved)

## Inventory Summary

| Bucket | Count | Size | Action |
|---|---|---|---|
| sqlite_database (runtime cache) | 19 | 111MB | quarantine_candidate (.gitignore) |
| seed_or_cache (JSON) | 8 | 11KB | quarantine_candidate (.gitignore) |
| seed_data (referenced) | 1 | 162B | keep_stateful |
| eval_result (referenced historical) | 2 | 8KB | keep_historical |

## Reference Scan Results

Only 3 of 30 files are referenced by active code/scripts/tests:
- `data/openapi_snapshot_baseline.json` → `scripts/check_openapi_snapshot.py` — ACTIVE reference. Keep.
- `data/evals/runs/2026-04-17_run_011944.json` — historical eval result. No active reference found in src/tests/scripts.
- `data/evals/runs/2026-04-17_run_012001.json` — historical eval result. Same.

The remaining 27 files (19 SQLite DBs + 8 JSON caches, 111.4MB) have ZERO references from src/, tests/, or scripts/. They are runtime caches, local databases, and historical exports.

## Classification Decisions

| data/openapi_snapshot_baseline.json | KEEP — active reference from check script |
| data/evals/runs/*.json | KEEP — historical eval evidence (2 files, 8KB) |
| data/*.db (19 SQLite files) | QUARANTINE CANDIDATE — 0 references, 111MB, runtime cache |
| data/*.json (8 cache files) | QUARANTINE CANDIDATE — 0 references, 11KB |

## What Was NOT Done

- NO files deleted
- NO files moved
- NO SQLite modified
- db/ untouched (separate scope)
- alembic/ untouched
- policies/ untouched
- legacy taxonomy terms unchanged

## Recommended Next Action (LGC-2A)

Add `data/*.db`, `data/*.sqlite`, and unreferenced cache JSON to .gitignore. Keep `data/openapi_snapshot_baseline.json` and `data/evals/` in tracking. This reduces tracked state from 111MB to ~8KB.

## Verification

```
184 tests passed
ordivon-verify document-governance --check: 0 BLOCKED, 0 DEGRADED
```

## Known Debts

- db/ classification (separate phase)
- legacy-term active terminology (LGC-4, LGC-5)
