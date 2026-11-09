# AUDIT_REPORT — Ordivon 2026-11-10 brownfield modernization

SourceCut ef17d6879d12faa61fff3bb762b0d500d73c9113. This source and command-line audit is bounded: all 5,002 Git files were inventoried, but only selected core files have been analyzed semantically. Treat uninspected internal dependencies as UNKNOWN, not PASS.

## Native baseline

- python3 tools/repo/check_owner_boundaries.py: exit 0, active_files=2320, packages=10, seams=31, references=38.
- python3 tools/repo/check_architecture_docs.py: exit 0.
- python3 tools/repo/check_composition_architecture.py: exit 0.
- Existing policy is real but partial: `tools/repo/check_owner_boundaries.py:16-31` scopes active extensions, `:89-100` ignores docs/planning/research, `:172` scans source path literals and `:219` parses Python imports. It is not a general Rust/TS runtime dependency proof.

## Ranked concrete findings and required actions

**A01 HIGH — PG reclaim second Git-status check fails to check subprocess exit.** `services/runtime/scripts/ordivon-runtime-pg-reclaim:189-199` uses returned stdout only before issuing native workspace.close; a failed Git command with empty stdout passes this operator condition. Native Runtime still separately validates close, so this is not proof of actual data loss. MODIFY only to reject returncode != 0 and preserve existing skip reason. Consumer: `services/runtime/packaging/systemd/ordivon-runtime-lifecycle.service:11`. Low diff risk, no new API.

**A02 HIGH — parallel lifecycle/operator maintenance paths.** `services/runtime/scripts/ordivon-runtime-lifecycle` 2621 lines, `ordivon-runtime-reclaim` 1176, `ordivon-runtime-cache` 874 coexist with systemd-current `ordivon-runtime-pg-reclaim` 241. Deploy/status/pressure scripts retain actual references; do not delete yet. DEFER until active CLI/Windows/packaging consumers are rechecked. Risk: duplicate owner policy, divergent recovery.

**A03 MEDIUM — explicit retired plan still advertised in current source.** `services/runtime/planning/EXECUTION_FABRIC_R1_ROADMAP.md:3` says RETIRED 2026-09-19, but `planning/lego-plan-r1.json:14` still includes it as source evidence. DELETE the retired file and remove that one reference; Git contains the history. Risk: historical link only.

**A04 MEDIUM — abandoned Windows planning artifacts.** `services/runtime/planning/WINDOWS_AUTHORITY_FACTORIZATION_EXECUTION_PLAN_R1.md:1-19` and `WINDOWS_AUTHORITY_FACTORIZATION_LEGO_R1.json:1-9` are execution plans, not native Windows implementation. No exact filename references found in tracked current source. DELETE these two historical plans, not any Windows Rust/C#/PowerShell source. Risk: outside-Git human reference unknown, recoverable.

**A05 MEDIUM — two active lifecycle extension Specs contradict user freeze.** `services/runtime/planning/WORKSPACE_CONSUMER_LIFECYCLE_R21_SPEC.md` and `WORKSPACE_CONSUMER_LIFECYCLE_R21_EXECUTION_PLAN.md` contain feature/consumer/test expansion; `services/runtime/docs/guides/runtime-legos.md:35-44` and `services/runtime/formal/README.md:384-386` link them. DELETE these two current plans, preserve the already merged TLA models, update existing links to this audit. Risk: downstream readers of historical draft PR #1998; supersede/close this unmerged draft rather than merge it.

**A06 MEDIUM — Harness has two exceptional owner-local complexity hot spots.** `services/harness/src/ordivon_harness/ordivon/run_continuity.py:129` declares an approximately 3,058-line class and `:323` and `:1548` span different work phases; `services/harness/src/ordivon_harness/ordivon/loop.py:220` begins a roughly 2,121-line _run method. PARTIAL Clean Architecture locality. Do not blindly split into another workflow engine; defer until actual call graph and native acceptance are qualified. Risk of behavior drift high.

**A07 MEDIUM — Web monolith module depth needs source-locality review.** `apps/web/src/app.ts:50` contains createWebApp and at least 15 POST and 8 GET route registrations; `apps/web/src/store.ts:37` contains WebStore with 32 SQL prepare calls. Existing store-agent-grants, store-sessions and store-schema modules are present. REFACTOR only by reusing present internal seams if verification is practical. Node SQLite here is Web-local; Linux Runtime PG-first does not imply a Web database bug.

**A08 MEDIUM — Artifact direct provider concentrates build preparation and delivery.** `capabilities/artifact/artifact_operations/providers/direct_python.py:95` class DirectPythonOperationProvider, `:190` execute_build_stage, `:356` prepare_operation, `:439` produce. Review actual consumers and duplicates in existing artifact_core and capability hooks; no new provider registry or test system.

**A09 MEDIUM — source policy is bounded, not universally language-complete.** The Owner boundary script passes for 31 exact exceptions and 38 uses, but its Python AST + literal-path search does not certify dynamic TS imports, Rust runtime bindings, or actual installed consumers. PARTIAL. Record this limitation; do not add new checker/test framework in this round. Current proper review is Owner source + existing language-native commands.

**A10 SCOPE — Linux and Windows are separate Runtime authorities.** `services/runtime/AGENTS.md:22-31` distinguishes Linux PG and historical Windows SQLite. KEEP Windows code and independent state; Linux systemd readback is not proof of Windows migration.

**A11 PRESERVE — Runtime research is frozen source provenance.** `services/runtime/research/README.md:1-35` and `research/programme/README.md` define a real archive and reopen conditions. KEEP its 132 tracked files; a text scan without a current import is not permission to destroy historical evidence.

**A12 PRESERVE — enormous existing tests are not an automatic architecture violation.** `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` 10788 lines, `services/runtime/scripts/tests/test_deploy_reclaim.py` 5155, `packages/composition/tests/test_verification_obligation_r1.py` 3388. KEEP native behavior checks; user explicitly forbids adding tests or a parallel test DSL.

## All registered Owner bounded verdicts

| Owner | Verdict | Actual anchor |
| --- | --- | --- |
| Host | PASS for declared PG/Journaling owner; other modules UNKNOWN | `services/host/README.md:1-20`; `src/ordivon_host_v2/social_space_queries.py:1-7` |
| Runtime | PARTIAL, A01 defect, A02 duplication | `services/runtime/scripts/ordivon-runtime-pg-reclaim:189-199` |
| Harness | PARTIAL locality A06 | `services/harness/src/ordivon_harness/ordivon/loop.py:220` |
| Gateway | PASS scoped thin-owner goal, code details UNKNOWN | `services/gateway/README.md`, `src/ordivon_gateway/mcp_server.py:156` |
| Security | UNKNOWN full execution policy; Owner README present | `platform/security/README.md` |
| Network | PARTIAL scoped native egress/policy separation | `platform/network/formal/egress_policy_refinement.py:1-8` |
| Workstation | PARTIAL native ingress ownership, installed outcome UNKNOWN | `platform/workstation/workstation/input_authority_ingress.py:1-10` |
| Artifact | PARTIAL provider locality A08 | `capabilities/artifact/artifact_operations/providers/direct_python.py:95` |
| Distribution | UNKNOWN implementation, owner registered | `capabilities/distribution/README.md` |
| Preservation | UNKNOWN implementation, owner registered | `capabilities/preservation/README.md` |
| Media | UNKNOWN implementation, owner registered | `capabilities/media/README.md` |
| Capital | PARTIAL domain-first source, outcome UNKNOWN | `domains/capital/src/ordivon_capital/research/pit_joint_forecast.py:1-9` |
| Game | UNKNOWN dynamic game/player result | `domains/game/README.md` |
| Composition | PASS scoped generic Owner policy; implementation still needs review | `packages/composition/README.md` |
| Data | PASS scoped read-only interoperability Owner | `packages/data/README.md` |
| Web | PARTIAL source locality A07 | `apps/web/src/app.ts:50`, `store.ts:37` |
| Chaoxing | UNKNOWN implementation | `apps/chaoxing-autosign/` |
| Authority catalog | PASS scoped non-authoritative discovery | `catalogs/authorities/README.md` |
| Capability catalog | UNKNOWN implementation | `catalogs/capabilities/` |
| ChatGPT Skills MCP | UNKNOWN implementation | `extensions/chatgpt-skills-mcp/` |
| Control plugin | UNKNOWN implementation | `extensions/ordivon-control-plane/` |

## Independent method audit

Matt Standards axis: owner-local contracts, 31 witnessed seams, present deep-module hot spots; no proof of whole-language or deployed authority. Matt Spec axis: planned edits must be deletion/clarification/defect repair, not new consumers/features/tests. ECC brownfield: RETIRED planning may leave current tree after direct links are repaired; in-use scripts and frozen research have different legitimate consumers. Superpowers verification: only actual current command results permit PASS.

Overconservative? Avoid retaining A03–A05 indefinitely because files were historically edited; but do not delete A02 while real deploy/status/pressure callers exist. Superficial? Deleting docs alone does not fix A01, so deliver an actual existing-error-path fix. Wrong problem representation? Workspace file age is not source architecture and the repository directory is not the semantic Owner. Independent peer acceptance remains UNKNOWN until actual reply; Host requests are not approval.
