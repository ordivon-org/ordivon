# Legacy Cleanup Risk Matrix — DGP-LGC-0

Status: **SUPPORTING_EVIDENCE** | Date: 2026-05-09 | Phase: DGP-LGC-0
Authority: supporting_evidence | Owner: Governance

## Action Classification

| Class | Action | When |
|---|---|---|
| A0 | Observe only, freeze | Unknown dependency, uncertain state |
| A1 | Mark identity/lifecycle | File exists, dependency unconfirmed |
| A2 | Move to archive, update registry path | Confirmed non-active, references updatable |
| A3 | Modify content terminology | No code behavior change |
| A4 | Delete, gitignore, or untrack | Confirmed rebuildable, zero dependencies, non-source-truth |

## Risk Assessment

| Candidate | Class | Blast Radius | Rollback | Recommended Phase |
|---|---|---|---|---|
| build/ (103 files, 165KB) | A1→A4 | None — rebuildable from source | Delete .gitignore entry | LGC-1 |
| dist/ (3 files, 382KB) | A1→A4 | None — build artifact | Same | LGC-1 |
| db/ (1 file, 10MB) | A0→A1 | UNKNOWN — may be seed/test DB | Git revert | LGC-2 after dependency scan |
| data/ (30 files, 111MB) | A0→A1 | UNKNOWN — contains SQLite | Git revert | LGC-2 after classification |
| 26 legacy dirs | A1 | None — identity only | Revert manifest | DONE (LGC-0) |
| 127 legacy-term active files | A0→A2/A3 | Low for docs, MEDIUM for scripts/tests | Git revert per batch | LGC-4 (docs), LGC-5 (scripts) |
| 82 legacy-term active files | A0→A2/A3 | Same | Same | LGC-4, LGC-5 |
| 2 archive-candidate docs | A2 | Low — documented, reference-checked | Move back | LGC-3 |

## Dependency Scan Summary

- build/: 0 code references, 0 test references — generated from CI/toolchain
- dist/: 0 code references, 0 test references — distribution artifact
- db/: referenced in scripts/ (migration tooling), alembic/ (migration config) — DO NOT DELETE
- data/: referenced in scripts/ (demo data, seed data) — needs classification

## Recommended Execution Order

```
LGC-1: build/ + dist/ quarantine (gitignore, safe)
LGC-2: db/ + data/ dependency resolution + classification
LGC-3: 2 archive doc moves (low risk)
LGC-4: Active docs terminology migration (low risk)
LGC-5: Script/test triage (medium risk, small batches)
```
