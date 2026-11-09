# Ordivon physical source architecture audit — scope

**SourceCut:** `ef17d6879d12faa61fff3bb762b0d500d73c9113`, current origin/main at 2026-11-10 02:30 +08. **Workspace:** `ws-gpt6-wholerepo-modernization-spec-20261110-r1`, isolated branch `refactor/repo-modernization-physical-owner-audit-20261110`. Physical primary checkout: `/root/projects/ordivon` (read-only for this task).

## Purpose and non-goals

Re-evaluate actual Ordivon owner source directories, primary code files and real consumers, against 2025–2026 maintainable modular-monorepo engineering. Reduce stale currentness claims, wrong ownership, dead source and needless abstraction. **No new features, no new tests or test frameworks, no new consumers, no production installation or service effects.** Do not mass-move directories merely to mimic Nx, Turborepo or a future structure spec.

## Natural ownership

- `tools/repo/owners.toml` is the repository *mechanical* map, `schema_version=1`, with **21 owner roots**, each retaining its own verification, provider identity, DB and release. Individual Owner schema/lifecycle is not centralised; inspect its own published contract and actual instance.
- Root source grammar consists of `services/`, `platform/`, `capabilities/`, `domains/`, `packages/`, `apps/`, `catalogs/`, `extensions/`, `profiles/`, `studies/`, `docs/`, `tools/`, `.agents/` and `.github/`. These are physical folders, not autonomous semantic Owners.
- `docs/architecture/STRUCTURE_R2.md` is a **partially deployed target**, `CURRENT_ARCHITECTURE.md` a dated historical snapshot. No automatic source relocation.
- Runtime owns Job/Attempt/execution evidence, Host owns Work/Space/Topic/Message/continuity, Harness owns Agent/tool/trace context, Gateway routes, Security authenticates/authorizes, Workstation converges OS/node dependencies; domains own their own product meaning. Source co-location does not transfer this authority.

## Phase contract

| Phase | Action | Named output |
|---|---|---|
| 0 | Inspect actual Git SourceCut/owners/current PRs; freeze checkable criteria | `AUDIT_SCOPE.md`, `MODERN_CRITERIA.md` |
| 1 | Enumerate all 5,002 tracked paths; categorize real top-level directories and 21 Owner modules, identify code/contract entrypoints | `INVENTORY.md` |
| 2 | Evaluate evidence under each criterion. C/P/N/U = conform/partial/breach/unknown. Record path, native consumer, concrete risk. | `AUDIT_REPORT.md` |
| 3 | Retain only source-bound actionable task DAG. Avoid changing another Agent's open PR-owned files. | `REFACTOR_PLAN.md` |
| 4 | Make minimal **stock-only** changes; execute only original Owner/Repo verifiers, no new test system | source Git diff + native check receipts |
| 5 | Recheck exact SourceCut vs commit, evidence, original checks, Merge/Install/Consumer standing and Space handoff | `BASELINE_AFTER_AUDIT.md` |

## Concurrency / conflict

Open PRs discovered at SourceCut: #2012 owns `tools/repo/exhaustive_coverage.py` and its tests; #2013/#2010 modify `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`; #2014 modifies Agent contract spec; #2016 Host, #2015 Harness, #2008 Workstation, #2017 Chaoxing and others perform their own stock cleanups. This branch **does not edit their paths**.

This specific scope has one observed source-currentness defect in a distinct path: `docs/architecture/OWNER_DEPENDENCY_BOUNDARY_R1.md` quotes 2,136 active files, 19 seam declarations and 21 references as the standing architecture description; the actual existing `tools/repo/check_owner_boundaries.py` at this SourceCut returns 2,320 active files, 31 seams and 38 references. The remedy is a scoped documentary update, not a new source checker.

## Evidence qualifications

Tracked files + static imports + bounded policy edges do **not** establish installed/dynamic consumer closure. The repository checker is source-level only; actual platform effect needs native readback. Same-file-content duplicates can be intentional when OS unit identity differs. Do not invent Owner `schema_version` or lifecycle where none is declared, do not count every file as a LEGO and do not call an audit a semantic proof.

Coordination: existing Host Space `space:ordivon-capability-task-forum-r1:20261101` / Topic `topic:ordivon-capability-task-forum-r1:03-refinement:20261101`; request sequence 25956. Handoff fields: state, SourceCut, completed, pending, evidence pointers, independent counterexamples. Space is a collaboration record, not merge authority.
