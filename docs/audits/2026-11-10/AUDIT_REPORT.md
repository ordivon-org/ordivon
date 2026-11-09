# Ordivon — AUDIT_REPORT (source-bound modernity review)

SourceCut `ef17d6879d12faa61fff3bb762b0d500d73c9113` (current main at initial observation); parent `AUDIT_SCOPE.md` and `MODERN_CRITERIA.md`. Source inspected as actual bytes and AST/manifest, not a reconstructed directory. The `INVENTORY.md` ledger contains all 5002 tracked paths (~123,199,041 bytes). Detailed code semantics were reviewed at selected critical seams; the rest are classified mechanically and remain explicitly unproven.

## Phase 2: decisive observations

**Architecture question:** Do real responsibility boundaries, state owners, contract consumers and change localization agree? A feature-first tree or Nx-looking layout alone cannot answer. The existing repo owner manifest has 21 owner roots, with read-only root source policy checks and a small set of explicit cross-owner seams. Code is already arranged by bounded owner, often using Python/Rust/TS and native Postgres/uv/pnpm/Cargo. The architecture therefore **is not a blank slate requiring an Nx/Turborepo migration**.

**Existing boundary rule actually runs:** `tools/repo/check_owner_boundaries.py:16-26,50-78,85-100,120-170,219-258`; native invocation on this exact working source: `active_files=2320, packages=10, seams=31, references=38`, exit 0. `tools/repo/test_owner_boundaries.py:65-118,180-242` contains native negative examples. Nevertheless the checker explicitly skips `docs/evidence/planning/research` via `IGNORED_COMPONENTS`; C02 is PARTIAL, not omniscient import enforcement. Adding a second Nx conformance engine is not justified.

**Owner registry and lifecycle:** `tools/repo/owners.toml:1-130` has schema_version=1 and 21 owner roots; root `AGENTS.md:1-72` explicitly prohibits cross-owner internal imports. It is not a runtime source of identity/goal truth. Host source migration head is `services/host/migrations/versions/0013_unicode_substring_gin.py` (source only). Runtime/Harness README contain `schema_version:1` YAML documentation frontmatter; these do not establish installed database schema.

## Phase 2.1: 21 natural owners × 12 criteria (evidence-calibrated)

Legend: `P` PASS source and active check; `M` PARTIAL, useful structure but incomplete proof; `F` FAIL with a reproduced concrete counterexample; `U` UNKNOWN/untested in this bounded audit. These grades are **current-source-only**. They are intentionally not averaged: a formal theorem, a directory, or an OWNER README is not proof of installed consumer correctness.

| Owner | Source pointer | C01 | C02 | C03 | C04 | C05 | C06 | C07 | C08 | C09 | C10 | C11 | C12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| runtime | services/runtime/README.md:1-35; crates/ordivon-runtime-core/src/pg_admission.rs:1-45 | M | M | M | M | M | M | U | M | M | M | M | U |
| host | services/host/README.md; src/ordivon_host_v2/work_store.py:34; migrations/versions/0013_unicode_substring_gin.py | M | M | M | M | M | M | U | M | M | M | M | U |
| harness | services/harness/README.md:1-36; src/ordivon_harness/ordivon/loop.py:172-220; run_continuity.py:129 | M | M | M | M | M | M | U | M | M | M | M | U |
| gateway | services/gateway/src/ordivon_gateway/mcp_server.py:12-40,156-170 | M | M | M | M | U | M | U | U | M | M | M | U |
| security | platform/security/README.md; contracts/agent-request-verifier-v1/src/index.ts | M | M | M | M | M | M | M | U | M | M | M | U |
| network | platform/network/AGENTS.md; README.md; planning/lego-plan-r1.json | M | M | U | M | U | M | U | M | M | M | M | U |
| workstation | platform/workstation/README.md; systemd/; postgresql/ | M | M | U | M | U | M | U | M | M | M | U | U |
| artifact | capabilities/artifact/README.md:1-24; artifact_verification/stage.py:1-38 | M | M | M | M | M | M | U | M | M | M | M | U |
| distribution | capabilities/distribution/README.md; packaging scripts | M | M | U | M | U | U | U | U | M | M | U | U |
| media | capabilities/media/AGENTS.md; README.md; apps/, packages/, processing/ | M | M | M | M | U | M | U | M | M | M | M | U |
| preservation | capabilities/preservation/README.md; planning/lego-plan-r1.json | M | M | U | M | M | M | U | U | M | M | U | U |
| capital | domains/capital/README.md; src/ordivon_capital/research/pit_joint_forecast.py | M | M | M | M | M | M | U | M | M | M | M | U |
| game | domains/game/AGENTS.md; README.md; Godot/Bevy source | M | M | M | M | U | U | U | M | M | M | M | U |
| composition | packages/composition/README.md; src/ordivon_composition/verification_obligation_r1.py | M | M | M | M | M | M | U | M | M | M | M | U |
| data | packages/data/AGENTS.md:1-18; README.md:1-55 | M | M | M | M | M | M | U | M | M | M | M | U |
| web | apps/web/src/config.ts:15-22; src/store.ts:37-45; README.md:40-53 | M | M | M | M | M | F | U | M | M | M | U | U |
| skills | extensions/chatgpt-skills-mcp/README.md; pyproject.toml; src/ | M | M | M | M | U | M | U | M | M | M | U | U |
| authority-catalog | catalogs/authorities/README.md; evidence/records/ | M | M | U | M | U | M | U | U | M | M | U | U |
| capability-catalog | catalogs/capabilities/README.md; schemas/ | M | M | U | M | U | M | U | U | M | M | U | U |
| control-plugin | extensions/ordivon-control-plane/mcp.json; plugin.json | M | U | M | U | U | M | U | U | U | M | U | U |
| chaoxing-autosign | apps/chaoxing-autosign/README.md; manifest paths | M | M | U | M | U | M | U | U | M | M | U | U |

## Phase 2.2: ranked source-grounded findings (ECC four axes)

| ID / severity | ECC axis | Concrete source evidence and diagnosis | Existing contract and maturity judgment | Action (stock only) | Risk / rollback |
| --- | --- | --- | --- | --- | --- |
| **F01 / P1** | Coding practice | `apps/web/src/config.ts:15-22` uses `Number.parseInt(raw,10)` for all positive-integer envs; on installed Node `parseInt("42garbage",10)` returns `42`, so malformed input crosses config seam as valid. | The error states "must be a positive integer" yet parsing is partial; C06 **FAIL**. A real correctness defect, not a demand for a new platform. | **REPAIR** the existing parser to require a full decimal integer string, preserve positive/safe-integer constraints; run existing `web:verify`, do not add tests or features. | Low–medium: rejects historically tolerated malformed env strings (intended). `git revert` single-file change. |
| **F02 / P1** | Coding practice / design | `services/harness/src/ordivon_harness/ordivon/loop.py:220-2342` `_run` spans ~2120 lines, and `run_continuity.py:129-2955` mixes transaction/event/caller ingress/replay flows. | Matt deep-module/locality review hotspot; large size alone does not prove a bug. PRs `#2015/#2009/#2005` already change Harness, so avoid overlapping changes. | **OWNER HANDOFF**: trace actual public seam and change reasons before any split; reuse current PG store and lifecycle methods, not a new Run kernel. | High churn/semantic continuity; no mutation this PR. |
| **F03 / P1** | Thinking / technology | `services/runtime/crates/ordivon-runtime-core/src/pg_admission.rs:1-3` says opt-in, not production authority; root current docs describe PG-backed Runtime. `services/runtime/README.md:1-35` and Runtime tool state are separate source vs installed qualifiers. | Comment/document currentness discrepancy is **candidate**, not verified installed defect; Runtime remains natural Owner. | **CLARIFY** comment only after exact installed Runtime source/feature flag and owner-native confirmation, not by guessing. | Mislabeled production evidence or unsafe rollback if changed blindly; no cross-owner edit. |
| **F04 / P2** | Coding practice | `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` 10,788 lines; `pg_admission.rs` 3,026 lines. `services/runtime/scripts/tests/test_deploy_reclaim.py` 5,155 lines. | Test architecture and coupling hotspot, not automatically dead code. Keep real regression oracles. | **ANALYZE/SPLIT IF WARRANTED** via existing Runtime Owner; no new tests, avoid today’s overlapping PRs. | Removing tests wholesale would lose fault evidence; medium–high. |
| **F05 / P2** | Thinking / code | `apps/web/src/store.ts:37-46` exposes `readonly db: DatabaseSync`. Actual direct reads occur only from existing tests (`apps/web/test/store-schema.test.ts:36-45`, `test/agent-authority.test.ts:179,329`, `test/browser-e2e.ts:463`), not established production callers. | Interface leakage to test surface, **PARTIAL** C03, not proof of multi-owner DB write. Native SQLite is explicitly a canary choice in `apps/web/README.md:40-53`; do NOT generalize PG-only requirement to this scoped canary. | **KEEP** now. Refactor only if real API consumers need a stable seam and no new test infrastructure. | Changing DB visibility would break current tests; low actual benefit. |
| **F06 / P2** | Thinking / architecture | `capabilities/artifact/artifact_verification/stage.py:1-38` exposes `VerificationStageHooks` with eleven callable fields; neighboring `artifact_verifiers/`, `artifact_operations/`, `artifact_core/` exist. | Potential shallow indirection vs deep module. This audit has not established duplicate execution or call replacement. | **REVIEW** binding callsites and native current packaging before deleting hooks; do not create third verifier. Artifact Owner PR `#1974/#1994` active. | High if erased stage has a real profile/consumer. |
| **F07 / P2** | Lifecycle / governance | Existing `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md` has overlapping open PRs `#2006/#2010/#2013`; code/PR navigation competes to establish current strategy. | Parallel mutable spec can cause conflicting state; merge discipline, not a new governance system. | **DON’T EDIT OVERLAP**. Owner of root architecture should adjudicate and retire superseded content through ordinary Git PR. | Risk of lost peer changes; high if auto-overwritten. |
| **F08 / P2** | Technology | `services/harness/src/ordivon_harness/sqlite_store.py` 1,065 lines coexists with `postgres_store.py` 758 lines; code may still exercise compatibility and transition consumers. | Cannot infer dead from SQLite in filename. Repo already has PG-only target and prior Owner branches. | **TRACE CONSUMERS** then retire only if no current callers/replay commitments. No blind delete. | Could erase required replay path; high. |
| **F09 / P2** | Source contract | `tools/repo/exhaustive_coverage.py:1-100` (2,052-line project-wide source/semantic classifier) already exists, and PR `#2012` is modifying that exact file. | Existing source index is not a new platform. Avoid parallel AST/inventory engine. | **REUSE** current native owner; this user's 5002-file Markdown ledger is a snapshot, not a new verification runtime. | Duplication and cross-PR conflict if new scanner shipped; avoided. |
| **F10 / P3** | Lifecycle / evidence | `extensions/ordivon-control-plane/` contains only `mcp.json` and `plugin.json`; unlike conventional service projects it has no `src/` files. | Appropriate thin carrier if its consumer is external plugin host; absence of source is not a violation. | **KEEP** manifests; compare actual published plugin/Tool consumer before any removal. | Deleting without dynamic provider lookup risks disappearance. |
| **F11 / P3** | Thinking | Full Git inventory has **23 exact-byte duplicate groups** but no known per-group ownership equivalence or effect-free replacement. | Exact hash equality only proves bytes equality, not semantic identity or removable lineage. | **REVIEW** per real consumer; skip blind dedupe and generated assets. | Unwarranted source deletion can erase license/evidence/test fixtures. |
| **F12 / P3** | Planning | `docs/architecture/CURRENT_ARCHITECTURE.md` is explicitly designated a dated snapshot by root `README.md:20-30`; `STRUCTURE_R2.md` is a target, not the deployed layout. | This distinction is good, do not rewrite all file paths to fit an unshipped architecture. | **KEEP** historical vs target tagging and keep `owners.toml` as current source routing. | Premature move breaks published owner paths; high. |

**F01 reproduction:** actual Node executable `/usr/bin/node`: `JSON.stringify({input:"42garbage", parsed:Number.parseInt("42garbage",10), safe:Number.isSafeInteger(Number.parseInt("42garbage",10))})` produced `{input:"42garbage",parsed:42,safe:true}`, exit 0. This was observed *before* modifying the parser. It is deterministic and its interface contract contradicts accepted junk suffixes.

## Mature patterns: suitability vs fashion

- **Clean/Hexagonal/DDD**: Host/Runtime/Harness natural owners and typed external SDK boundaries largely fit intent. Do not introduce ports/adapters for single static internal implementations. Native PG transaction, MCP SDK transport and systemd are already real infrastructure.
- **Modular monolith**: one Git repository co-locates autonomous Owner releases/locks, so it is a *modular monorepo*, not one shared transaction monolith; forcing one DB or one package manager violates existing invariants.
- **Nx/Turborepo**: enforcement insight applies; project uses `tools/repo/check_owner_boundaries.py` + source manifest, not Nx. No performance or dependency evidence justifies converting the whole Rust/Python/TS tree.
- **Matt**: deepest immediate improvement is not deleting small facets but correcting low-level seams and reducing stale parallel decision records. Run deletion test at real importer, not file size.
- **ECC**: four gap axes used above; the missing-features axis is deliberately **out of scope** this wave, and does not authorize tasks. No extra hooks to enforce a report.
- **Superpowers**: isolated worktree, observed negative case, exact bounded plan, native verification; no `TDD` extension because user expressly prohibits new tests.

## Evidence and limitations

All file paths are exact source paths at SourceCut. 5002-file ledger is mechanically complete; the qualitative assessment is **not** a human line-by-line semantic proof of all 5002 files. Each `M`/`U` in the owner matrix remains a review standing. No installed service/source, database currentness, web production release or external user effect is inferred from Git. A source defect verified by reproduction (F01) differs from a structural hotspot (F02/F04) and from a cross-owner planning collision (F07).

## References

- Matt native codebase design: https://github.com/mattpocock/skills/blob/main/docs/engineering/codebase-design.md
- Nx boundary constraints: https://nx.dev/docs/features/enforce-module-boundaries
- ECC: https://github.com/affaan-m/everything-claude-code
- Superpowers writing/execution: https://github.com/obra/superpowers/tree/main/skills
- Parnas: https://doi.org/10.1145/361598.361623
