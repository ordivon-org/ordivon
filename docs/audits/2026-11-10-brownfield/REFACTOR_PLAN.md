# REFACTOR_PLAN — Ordivon Brownfield source-only modernization

SourceCut `ef17d6879d12faa61fff3bb762b0d500d73c9113`. Each task below is a small code/document source edit, not a new feature, test, consumer, schema, orchestration or platform. First verify actual affected Owner using existing `tools/repo/owners.toml`, `mise.toml`, `tools/repo/affected_owners.py`, then execute and verify.

## Small-batch dependency DAG

```text
B00 baseline + existing native boundary/Capital tests
    ├── B01 correct actively consumed Finance doc currentness (PG vs SQLite)
    └── B02 retire historical LEAN/TigerBeetle carrier + self-test/registry (one atomic Git slice)
              └── B03 update Finance architectural history + directory audit
    └── B04 remove truly orphaned dated demo guidance and nonexistent catalog source pointer (after public README confirm)
    └── B05 optional core-source duplication repair (after exact observed equivalence; not a release blocker)
B01–B04 -> B06 existing Owner and repo verification -> B07 final baseline/PR
```

### B00: freeze and baseline (DONE)

- Confirm origin/main and clean worktree at original SourceCut.
- Run existing `python3 tools/repo/check_owner_boundaries.py`, `check_structure_r2.py`, `check_architecture_docs.py`, `check_composition_architecture.py`: observed PASS.
- Run existing `cd domains/capital && mise run verify`: observed 870 passed, 26 skipped, 24 deselected, 209 subtests, Lean/Z3/CrossHair scoped checks PASS. Skipped PG/provider cases remain SKIP; do not claim physical PostgreSQL acceptance.
- Record raw Git source file hashes in FILE_CENSUS.tsv. No code write before baseline.

### B01: wrong current accounting information (HIGH)

Path: `domains/capital/docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md`, and narrowly relevant corresponding provenance JSON text if it states SQLite current; native consumer `catalogs/capabilities/ele/studies.py` must keep path unchanged.

- Replace present-tense 'SQLite current' with current PG source `accounting/postgres_ledger.py`, `postgres_paper_close.py`, preserve SQLite as explicitly *historical* source qualification.
- Do not rewrite real SQLite web canary (`apps/web/src/store.ts` separate Owner).
- Verify existing `test_standalone_source_retirement.py`, `test_external_owner_census.py`, capability-catalog tests and Capital native suite.
- Rollback `git restore` if uncommitted; after PR merge `git revert <commit>`.

### B02: remove self-preserving historical executable surface (HIGH)

Atomic source delta:
- Delete `domains/capital/tools/legacy_replay/` (13 files; old LEAN Wave-B runner) and `domains/capital/tools/tigerbeetle_0_17_9/` (8 files).
- Delete `domains/capital/tools/nautilus_rc4/run-m6-differential` as the discovered sole transitive caller of the deleted Wave-B precommit runner; no current active caller remains.
- Delete `domains/capital/config/legacy_replay_surface_registry.json` and `domains/capital/tests/test_legacy_replay_surface_isolation.py` (self-asserted path-presence test).
- Remove obsolete `.gitignore` rules specific to removed carrier; preserve generic build ignores.
- Keep `domains/capital/wave_b/fixtures/wave_a_target_portfolio.json` and existing PG accounting implementation. Historical source bytes are retained in immutable Git history `ef17d...`, so a future independent historic qualification can check them out at that revision, not maintain a current Python/C# runtime for them.
- Assert no remaining tracked current CLI, `mise.toml`, or public Owner source actually imports deleted carrier. A named real non-test consumer would reverse RETIRE for its specific file.
- Verify B02 using unchanged `mise run verify`, existing repo:ci/owner and Git diff; do **not** add tests for absence or new compatibility shims.
- Rollback same as B01. No live provider, database, service or external account effects.

### B03: correct one natural Owner's narrative (MED)

- Replace stale current claims in `domains/capital/docs/ARCHITECTURE.md`, `docs/FINANCE_DIRECTORY_OWNER_AUDIT_R1.md`, and `domains/capital/README.md` only where the implementation changed; preserve dates of historical R1 citations.
- Do not create a duplicate Finance SPEC. Existing docs are authority for their own scope, previous source revisions survive in Git.
- Existing doc/architecture drift check and Capital suite.

### B04: detached dated historical README (MED)

- `domains/capital/docs/OKX_DEMO_EXTERNAL_EXECUTION_R1.md`: no literal direct name path consumer under source-current Git `git grep` scan. Its current mechanics are already in `domains/capital/README.md`, `ARCHITECTURE.md` and `trading/okx_demo_execution.py`.
- Retire the outdated standalone historical doc and preserve its revision in Git; no new documentation layer needed. Confirm no source or existing tests break.
- Roll back Git as above.

### B04b: remove broken catalog source pointer (MED)

- `catalogs/capabilities/ele/studies.py` lists the nonexistent `domains/capital/docs/EXTERNAL_IMPLEMENTATION_QUALIFICATION_R1.md`. Remove only that dead list entry; do not substitute a new consumer route or relocate Finance evidence.
- Keep the currently existing `ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md` for ELE and correct its content at source.
- Verify `mise run capability-catalog:verify` and existing root repo:ci tests; Git revert restores the pointer if needed.

### B05: source responsibility duplication (MED, evidence before modification)

Candidate: `portfolio/portfolio_counterfactuals._recompute` duplicates Risk aggregate, compared to `risk/portfolio_risk.build_exposure_ledger`. This batch is **not** automatically required for B01–B04 to merge, because exact rounding/error/output equivalence has not been established. If consumer equivalence can be shown from existing cases and a direct safe reuse is possible, refactor existing function only, no new method or test. Otherwise HOLD for source-specific follow-up, not a blocker to removing the historical carrier.

### B06: verify existing acceptance rail (required for changed slices)

1. `git diff --check` and exact changed/deleted Git file list.
2. `cd domains/capital && mise run verify` with actual results and SKIPs reported.
3. `mise run repo:ci` and `python3 tools/repo/check_owner_boundaries.py`, `python3 tools/repo/check_architecture_docs.py`.
4. For any affected non-Finance Owner changes, run its already defined `mise run <owner>:verify`, not broad unrelated suites as ritual.
5. Compare source-dependent candidacy/PG claims; keep `SOURCE`, `MERGED`, `INSTALLED`, `CONSUMED` separate.

### B07: independent review, GitHub merge, final source baseline

- Matt two axes: (A) Standards vs `AGENTS.md`, Owner guide, deep module smells; (B) SPEC vs B01-B04 approved scope. Do not merge axes.
- ECC brownfield closing loop: compare current source with B00, count removed executable historical carrier bytes/paths and current false claims.
- Superpowers: verification before completion, direct smoke of existing entrypoint where justified, no new tests.
- Git commit/push PR and request existing Merge Queue; record real state. In Space, post `status|sourceCut|actual_changes|verification|remaining_UNKNOWN|next`.
- Update `BASELINE_AFTER_AUDIT.md` with after counts/check outcomes without inflating into installed/deployed truth.

## Explicit STOP criteria
Any current non-test production caller requiring a deleted carrier; source identity irreversibly lost; accepted test failure not explainable by self-test retirement; mismatch in finance contract outputs, financial effects or PG state. STOP applies only to the affected edit batch, not all unrelated cleanup.

## No-growth constraints
No net-new runtime abstraction, tests, consumer routes, Nx/Turborepo installation, additional evidence database, watcher, Agent registry, new module boundary checker or model experiment.


## R2 batch status after verification

- B00 DONE: SourceCut `ef17d...`, baseline native checks observed.
- B01 DONE: PG-current source truth in existing Finance external-owner document and census (historical SQLite remains dated evidence).
- B02 DONE: old LEAN/TigerBeetle tool islands and one transitive Nautilus M6 driver deleted with their self-preserving test and path registry.
- B03 DONE: Finance architecture and existing owner audit updated in place, historical source remains in Git.
- B04 DONE: zero direct name consumer old OKX demo document removed with Git rollback.
- B04b DONE: one path to non-existent Finance source dropped from ELE catalog's existing SOURCES array.
- B05 HOLD (not a hidden blocker): Portfolio and Risk aggregate duplication requires actual data/error/rounding equivalence before a consumer-preserving refactor; no new tests permitted.
- B06 DONE: Capital native 865 passed, 26 skipped, 24 deselected; repo:ci twice PASS (533 grouped pytest); capability-catalog native PASS.
- B07 SOURCE DONE: docs + code commit, Git branch and PR admission pending; no installed or economic-outcome claim.
