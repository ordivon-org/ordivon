# AUDIT_SCOPE — Ordivon brownfield modernization

Date: 2026-11-10. Git SHA: `ef17d6879d12faa61fff3bb762b0d500d73c9113`, checked via GitHub main and local Git. Primary source repo: `/root/projects/ordivon`; audit in isolated PG Runtime worktree.

## Allowed

Observation -> evidence-backed judgment -> executable plan -> small reversible behavior-preserving cleanup, rename, consolidation and evident defect repair -> native verification. 21 real Owners, 5,002 Git tracked files.

## Forbidden

New product features, tests, consumers or interfaces, parallel control planes, duplicated global registries, new approval hooks, relabeling all current roots as packages, treating Git checkout as production. Do not delete active Workspaces, PG rows or Windows native state in this repo audit.

## Principles

Real implementation and installation authority are lower natural Owner facts. `docs/architecture/STRUCTURE_R2.md` is partially deployed target grammar, not current source truth. Root only handles repository mechanics. Keep Linux PG and Windows native differences explicit.

## Evidence grading

File ledger is exact for tracked Git files, not human line-by-line interpretation. Verdict about a file requires at least its actual code path, consumer/ref, source SHA and rollback. Source tests do not certify installed node or product acceptance. UNKNOWN does not mean FALSE.

## Phase boundaries

Phase 0: source baseline and criteria; Phase 1: per-owner tree/file inventory; Phase 2: major module code/architecture review; Phase 3: ranked rollback plan; Phase 4: scoped existing-code edits + existing verification; Phase 5: current Git baseline + Host Space handoff.

## Artifacts

`AUDIT_SCOPE.md`, `MODERN_CRITERIA.md`, `INVENTORY.md`, `INVENTORY_FILES.tsv`, `AUDIT_REPORT.md`, `REFACTOR_PLAN.md`, `BASELINE_AFTER_AUDIT.md` all live together; no second tracking registry.
