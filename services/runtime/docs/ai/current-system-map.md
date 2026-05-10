# Current System Map — DGP-S / LGC-S

Last verified: 2026-05-09 | Owner: Governance

## Registry Control Plane

Run: `ordivon-verify registry-index --check`
Status: 1221 objects, 0 BLOCKED, 0 DEGRADED, 269 ROUTED, 13 reconciliation checks.

## Document Governance Pack

| Phase | Status | Scope |
|---|---|---|
| DGP-1 | CLOSED | Registry Control Plane Foundation |
| DGP-2 | CLOSED | Document Lifecycle Governance |
| DGP-3 | CLOSED | Current Truth / Authority Governance |
| DGP-4 | CLOSED | AI Onboarding / Context Governance |
| DGP-5 | CLOSED | Receipt / Stage Summit Governance |
| DGP-6 | CLOSED | Format / Medium Governance |
| DGP-7 | CLOSED | Archive / Tombstone / Metabolism |
| DGP-8 | CLOSED | Knowledge Map / Navigation Governance |
| DGP-9 | CLOSED | Document Governance CI / Operationalization |
| DGP-E1 | CLOSED | Active Enforcement Bridge |
| DGP-S | CLOSED | Stage Summit |

## Legacy Governance

| Phase | Status | Action |
|---|---|---|
| LGC-0 | CLOSED | Freeze: 26 dirs, 209 terms, 4 artifact classes |
| LGC-1 | CLOSED | build/dist no-op (already gitignored) |
| LGC-2 | CLOSED | data/ classified (30 files, zero deletion) |
| LGC-2A | CLOSED | SQLite/DuckDB no-op (already gitignored) |
| LGC-3 | PARTIAL | 1 doc archived, architecture-baseline retained |
| LGC-4 | CLOSED | 4 LGC docs cleaned (16→0 terms) |
| LGC-5 | CLOSED | 122+ files triaged |
| LGC-5A | CLOSED | Bridge plan: KEEP_ACTIVE_BRIDGE |
| LGC-5B | CLOSED | 1 rename, 5 preserved |
| LGC-5C | CLOSED | 18 scripts: 0 quarantine |
| LGC-5D | CLOSED | 20 tests: 0 assertion risk |
| LGC-5E | CLOSED | Policy R4 + alembic R3 boundaries |
| LGC-5F | CLOSED | 27 source files: 25 legacy_inactive |
| LGC-S | CLOSED | CLOSED_AS_GOVERNED_LEGACY |

## Current Truth Entry Points

`docs/governance/current-truth-entry-map.jsonl` — 188 entries.

## NO-GO Boundaries

`docs/ai/no-go-boundary-map.md` — Authorization, truth, evidence boundaries.

## Next Route

MR-0 — Ordivon Main Reality Freeze.

This map does not authorize merge/release/deploy.
