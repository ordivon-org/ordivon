# Ordivon modern architecture: evidence-driven audit report

**SourceCut:** `ef17d6879d12faa61fff3bb762b0d500d73c9113`, 2026-11-10. **Outcome:** 21 Owner roots mapped, 5,002 real tracked files accounted for with the preinstalled exact-Git source tool. The strongest *confirmed* new defect is the repository boundary document's stale interpretation of its own live checker; the rest of this report separates witnessed defects from refactor hypotheses and dynamic UNKNOWN. No claim of full semantic verification of every implementation file.

## Status summary by criterion

| Criterion | Source-only status | Grounded evidence and limit |
|---|---|---|
| M01 responsibility-based directory | C within named Owner map / P overall | `tools/repo/owners.toml` has 21 disjoint Owner roots, 4,561 paths; 441 paths outside them are root meta/Skills/studies etc, **not automatically ownerless** |
| M02 enforceable module boundaries | C for bounded scope | Original `python3 tools/repo/check_owner_boundaries.py` PASS: 2,320 active files, 10 packages, 31 declared seams, 38 references. AST/literal scanning explicitly does not prove all dynamic edges |
| M03 pure domain core / inversion | U | Actual per-Owner source graph or runtime-agnostic domain imports not proved. High-LOC module ≠ violation |
| M04 authority/state/effects | P (architectural declared) | `README.md` + `AGENTS.md` distinguish Runtime, Host, Harness, Gateway and actual effect. Not every installed producer was read |
| M05 schema/contract synchronicity | P | `owners.toml` and `dependency_contracts.toml` schema_version 1; Owner protocols vary, no single domain-wide schema_version |
| M06 mature external provider | C for source selection / U for substitution | Workstation lists Ansible, Nix, OpenTofu, Quadlet, pgBackRest, Temporal; no live evidence allows mass-retiring provider wrappers |
| M07 deep modules | P | Long hot paths `services/harness/.../run_continuity.py`, `loop.py`, `packages/composition/.../verification_obligation_r1.py`; no observed consumer migration proof for splitting |
| M08 accurate check docs | **N** | `docs/architecture/OWNER_DEPENDENCY_BOUNDARY_R1.md` still quotes 2,136/19/21 vs observed 2,320/31/38 |
| M09 dependency cycles | C for 31 declared source seams / U dynamically | 17 distinct directed Owner pairs; zero multi-Owner SCC in the *declared* directed graph; not proof of arbitrary runtime calls |
| M10 trustworthy current README/ADR | P | Root `README.md` explicitly calls `CURRENT_ARCHITECTURE.md` historical and `STRUCTURE_R2.md` non-deployed target; one separate old checker-count document needs correction |
| M11 consumer-rooted code retirement | P | Source/Owner tree and native checks exist, but Git ref zero is not installed caller closure; parallel Workstation/Host/Harness subtraction PRs avoid colliding changes |
| M12 reversible scoped work | C locally | SourceCut-pinned new Runtime workspace, protected Git branch, per-Owner `mise` checks and existing CI; no production mutation |

## Owner-specific evidence and verdicts (all 21)

`C` under a specified source predicate, `P` incomplete/partial, `U` genuinely unobserved. A source checker PASS cannot be promoted to total runtime correctness.

| Owner | Architectural verdict | Actual principal file(s) and observed signal | Action, risk |
|---|---|---|---|
| authority-catalog | C on placement, P on consumers | `catalogs/authorities/scripts/authority_catalog.py` and dated `observations/` (182)/`records/` (176) | Keep exact-source observation vs authority distinction; do not drop provenance as junk |
| capability-catalog | P | `catalogs/capabilities/ele/studies.py` (688 lines), declared source projections into Artifact/Capital/etc | Check producer-origin currentness, avoid second metadata registry; upstream/dynamic consumers UNKNOWN |
| composition | P | `packages/composition/src/ordivon_composition/verification_obligation_r1.py` (770 lines); `verification_impact.py` (662) | Potential deep-module debt; do not relocate verification authority from actual consumers |
| control-plugin | C on thin carrier | `extensions/ordivon-control-plane/plugin.json` and `mcp.json`, exactly 2 files | No new control-plane implementation; no defect observed |
| runtime | P | `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` (10,788-line existing suite), `crates/` 139 files | Current PG/native Runtime boundary remains natural; massive test file is a maintainability candidate, not a reason to add tests |
| host | P | `services/host/src/ordivon_host_v2/social_space_queries.py`, `social_contracts.py`; source root 117 files | Host owns social/continuity PG, not Runtime Job; concurrent PR #2016 owns separate subtraction |
| harness | P | `services/harness/src/ordivon_harness/ordivon/run_continuity.py` (3,186), `loop.py` (2,366) | High edit locality/coupling risk; Parnas deep-module audit pending; #2015/#2009 already touch owner |
| gateway | P | `services/gateway/src/ordivon_gateway/mcp_server.py` (489) and `upstream.py` (426) | Check proxy/transport vs semantic authority; source-only checker passes; deployed RPC UNKNOWN |
| skills | P | `extensions/chatgpt-skills-mcp/src/ordivon_skills/catalog.py` (750) and `scripts/skills_mcp.py` (692) | Thin compatibility owner should not duplicate Skill source; pending #2011 handles stock cleanup |
| security | P | `platform/security/labs/agent-admission-rs/src/principal-store.ts`; `contracts/` 13 files | Explicit permission/identity boundary; do not infer lab proof is installed policy |
| workstation | P | `providers/cloudflare/scripts/ordivon_edge_release.py` (1,318), `ansible/n8n.yml` (623) | Real Cloudflare release and OS effects demand distinct acceptance; #2008/#1997 already own stock cuts |
| network | P | `platform/network/formal/egress_policy_refinement.py` and `scripts/monitoring-sourcecut-preflight.py` | Native tunnel/route state distinct from declarative tests; no live route mutation |
| artifact | P | `capabilities/artifact/scripts/artifact_oci_package.py` (637), `artifact_delivery_toolchain_doctor.py` (641) | Reconcile artifact verification and consumer acceptance, do not invent another verifier |
| distribution | P | `capabilities/distribution/adapters/`, source root 30 files | Destination receipts remain Distribution; old evidence carriers under parallel #2007 |
| media | P | `capabilities/media/scripts/creative_library.py` (613); `productions/` 213 records | Native FFmpeg/creative assets and rendered outputs have distinct consumer roles; avoid indiscriminate deletion |
| preservation | P | `capabilities/preservation/scripts/verify_source.py`; `artifacts/` 32 | Source/fixity/migration evidence must not become delivery/Host truth |
| game | P | `domains/game/research/autonomous-interest-r7/evaluator_reference.py` (601); `examples/` 333 includes upstream vendor | DDD rules and Godot/Bevy scene ownership; do not delete vendored assets by source size |
| capital | P | `domains/capital/src/ordivon_capital/research/pit_joint_forecast.py` (860); `governance/policy_decision.py` (606) | Domain finance research/governance in Capital, not repo; many tests/evidence have actual contract consumers |
| data | C for thin read-only boundary / U for deployed usage | `packages/data/src/ordivon_data/odps_projection.py` (181), `catalog.py` (177) | Read-only cross-producer projection; avoid new central data DB |
| web | P | `apps/web/src/store.ts` (810), `app.ts` (721); `apps/web/README.md` says canary | Thin app is not guaranteed by short path; current store has direct SQLite legacy count in repo SQL gate; separate owner |
| chaoxing-autosign | P with retirement candidate | `apps/chaoxing-autosign/chaoxing_mvp/{engine.py,ledger.py}`; 11 files | Concurrent PR #2017 handles admitted retirement. Do not edit or duplicate it |

## Prioritized defects and opportunities

| Severity | File(s) and exact observed problem | Corrective action and owner | Risk / qualification |
|---|---|---|---|
| **High (H1)** | `tools/repo/check_owner_boundaries.py` covers 2,320 source files and 31 explicit seams, but no source-only checker certifies dynamic/installed runtime dependency edges | No new guard. Use public Owner contracts and existing CI, request dynamic evidence only for actual risky refactors | Scope gap is documented and NOT a test failure; changing scanner risks parallel #2012 |
| **Medium (M1, confirmed)** | `docs/architecture/OWNER_DEPENDENCY_BOUNDARY_R1.md` still says 2,136 active files, 19 seams, 21 references while original verifier measured 2,320/31/38 | Repo documentation owner: update exact SourceCut, seam groups and bounded counts; no checker/API change | Low runtime risk; inaccurate Owner navigation/evidence can mislead Agents |
| **Medium (M2)** | `services/harness/src/ordivon_harness/ordivon/run_continuity.py` 3,186 lines; `loop.py` 2,366; deployment and caller roles need more locality assessment | Natural Harness Owner, existing `harness:verify`; #2015 already modifying owner | Large code is only a **refactor hypothesis**, not confirmed functionality defect |
| **Medium (M3)** | `platform/workstation/providers/cloudflare/scripts/ordivon_edge_release.py` 1,318 and Tofu handoff 865; Wranger native mechanisms already selected | Workstation Owner: compare existing native Wrangler and Ordivon unique receipt, no unproven deletion | Remote side effects/receipt identity can break if blindly replaced |
| **Medium (M4)** | `tools/repo/exhaustive_coverage.py` source-only plan projection reports 376 semantic-zone UNASSIGNED, 9 cross-plan local ID reuses | Treat as **derived candidates**, not universal missing Owners or genuine collisions; reuse existing checker and #2012 | Wrong equation (semantic zone != repo Owner) would create unnecessary global registries |
| **Low (L1)** | `domains/game/examples/` 333 tracked files, `capabilities/media/productions/` 213, and `catalogs/authorities/observations/` 182 | Classify vendored assets / outputs / historical observations by content and real consumers; no automated purge | Source size/age is not evidence of dead consumer |
| **Low (L2)** | Metadata in Owner READMEs not uniformly declared; explicit YAML-like `schema_version/lifecycle` headers seen in Runtime, Harness, Game, not others | Inspect actual owner contracts on demand; **do not standardize all README headers** absent consumer | Cosmetic uniformity would be paperwork, not architectural improvement |

## Counterfactual/false-positive protections

- A domain-first clean architecture does not require every Owner to live in `packages/`. The dated, partially deployed `STRUCTURE_R2.md` is a *migration target*; source relocation could break package installs, CI pathspecs and release scripts.
- A lack of declared SCC does not prove absence of Python dynamic imports, JS require, runtime plugin discovery or mutual RPC cycles.
- The current Native source checker actually **PASSed**; do not invent a boundary failure to justify adopting Nx Enterprise or extending tests.
- Existing historical data and lockfiles have legitimate provenance and reproducibility roles; a static zero-ref file is not necessarily junk.

## Original command evidence

At this exact SourceCut:
- `python3 tools/repo/check_owner_boundaries.py`: valid; active_files=2320, packages=10, seams=31, references=38.
- `python3 tools/repo/check_structure_r2.py`: passed.
- `python3 tools/repo/check_architecture_docs.py`: passed **before** the identified documentary update.
- `python3 tools/repo/exhaustive_coverage.py --source-cut ef17d6879d12faa61fff3bb762b0d500d73c9113 --summary`: accountedForPaths 5002, proofReuseAdmissible false.
- `... --static-python-consumers --summary`: 1,460 Python source paths; 2,359 candidate edges; 83 dynamic syntax sites; 8,988 unresolved statements (all bounded hints; not semantic failures).

The source records are anchored in the shared Workspace and Git cut; publication tests and real production deployment require later independent evidence.
