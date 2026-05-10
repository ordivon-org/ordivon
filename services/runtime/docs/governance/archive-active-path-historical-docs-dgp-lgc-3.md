# Archive Active-Path Historical Docs — DGP-LGC-3

Status: **PARTIAL** | Date: 2026-05-09 | Phase: DGP-LGC-3
Authority: supporting_evidence | Owner: Governance

## Action

| Document | Old Path | New Path | Result |
|---|---|---|---|
| aegisos-quality-matrix.md | docs/product/aegisos-quality-matrix.md | docs/archive/legacy/aegisos-quality-matrix.md | ARCHIVED |
| architecture-baseline.md | docs/architecture/architecture-baseline.md | — | NOT MOVED |

## Why architecture-baseline.md was NOT moved

32 active references found, including:
- `docs/governance/current-truth-entry-map.jsonl` — registered as current truth
- `policies/constitution.md` — active policy document
- `docs/README.md` — active readme
- `docs/workflows/status-sync-workflow.md` — active workflow
- `docs/product/task-template-system.md` — active product doc
- `docs/governance/document-registry.jsonl` — registry

Moving this document would break active governance references. It requires a dedicated re-triage phase with owner approval.

## aegisos-quality-matrix.md

Only 3 references found, all in audit/inventory files (exclusions, term inventory, docs-inventory). Safe to archive. Archive warning header added. No stale references remain.

## What Was NOT Touched

- db/, data/, build/, dist/
- scripts/, tests/e2e/
- policies/constitution.md
- alembic/
- legacy taxonomy terms broadly
- legacy code directories

## Next for architecture-baseline.md

Requires LGC-5 triage: determine whether to keep as active current truth, reclassify, or archive with full reference repair.
