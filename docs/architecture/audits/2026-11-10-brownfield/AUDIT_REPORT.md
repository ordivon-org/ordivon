# AUDIT_REPORT — Ordivon actual source architecture, 2026-11-10

**Phase 2:** bounded current-source audit; committed evidence subject is `ef17d6879d12faa61fff3bb762b0d500d73c9113`. One file tree enumerates all 5,002 current Git files in `INVENTORY.md`; the deeper semantic assessment here covers major actual modules and selected source hot paths, **not** all 5,002 file implementations.
**Decision criteria:** `MODERN_CRITERIA.md` C01–C11. Marks are `符合 / 部分符合 / 不符合 / 待验证` and carry scoped evidence. The absence of a code check is NOT evidence that the criterion fails.
**Non-goals:** no new features, tests, consumer routes, product increments or global policy layer.

## A. 21 Owner/source module qualification matrix

| Existing natural Owner | Current source and entrypoint evidence | Current architecture judgement | Maintenance decision and risk |
|---|---|---|---|
| Runtime | `services/runtime/README.md:2-18` active/schema frontmatter; `services/runtime/crates/ordivon-runtime-core/src/runtime/engine.rs:216`, `types.rs`, `tests.rs` | **部分符合** C01/C04: physical authority clearly specified; `tests.rs` 10,788 lines and `types.rs` ~2,097 lines are change-locality risks, not boundary violations by size alone | targeted function/type submodule review, reuse Rust module/crate idioms; **HIGH regression risk** around Job/Attempt semantics |
| Host | `services/host/README.md:9` PostgreSQL; `services/host/src/ordivon_host_v2/work_store.py:34`, `work_queries.py`; `services/host/migrations/versions/` | **符合（声明的源码边界）/待验证（生产历史）** C04/C05: Work CAS vs queries are separated | KEEP native PG/CAS; never delete Work because terminal without checking Subject/Relation/Message references; **HIGH data-history risk** |
| Harness | `services/harness/src/ordivon_harness/ordivon/loop.py:77,220` and `run_continuity.py:129,323,1548`, `sqlite_store.py:154` | **部分符合** C01/C11: clear Run/Tool Owner, but `_run` spans ~2,121 lines and `EventSourcedRunContinuity` ~3,058; SQLite still consumed | bounded extraction only after native call graph and independent PR #1835 collision review; no blanket SQLite delete; **HIGH behavior/effect risk** |
| Gateway | `services/gateway/README.md:3,62` thin route-only authority; `src/ordivon_gateway/upstream.py:135` | **符合（source authority）/待验证（live RPC）** C01/C04: non-authoritative routing explicit | reuse standard MCP client, avoid replacing with second Owner RPC scheduler; live availability requires independent installed readback; **MEDIUM/HIGH** |
| Security | `platform/security/README.md:7-21`; `contracts/agent-request-verifier-v1/` and `labs/agent-admission-rs/` | **部分符合** C02/C08: bounded contracts/labs exist, some byte-identical patch/config files cross packages | check package-manager consumers and patch identity before dedup; avoid new IAM/OPA wrapper; **HIGH auth risk** |
| Network | `platform/network/README.md:62-87` and `consumers/browserless/` | **部分符合** C01/C04: transport vs consumer owners are described; mutable installed state uninspected | use existing Taskfile/systemd/providers; don't infer live VPN from source config; **MEDIUM** |
| Workstation | `platform/workstation/README.md:7-20` identifies Ansible, systemd/Podman, Temporal, n8n | **符合（technology choice/source separation）/待验证（installation）** C01/C03 | DELETE duplicated custom orchestrators if genuinely replaced, not stable upstream providers; **HIGH operational** |
| Artifact | `capabilities/artifact/README.md:3,46`; `artifact_operations/providers/direct_python.py:95,439` | **部分符合** C01/C11: evidence and verifier ownership well described; one provider class spans >500 LOC, imports many adapters | trace real stage owners and duplicate validation before *small* extract; do not compete with active Artifact PR; **HIGH evidence correctness** |
| Media | `capabilities/media/README.md:3,28`; `artifacts/creative-library/catalog-v1.json` and `productions/archive-archipelago-001/source/creative-library-catalog-v1.json` | **部分符合** C08/C11: source/render/provenance distinctions declared, large derivative data pairs differ in bytes | KEEP until actual source/production references and content semantics are traced; use FFmpeg/native producer; **MEDIUM provenance** |
| Distribution | `capabilities/distribution/README.md:37-50` documents retired control logic | **符合（scoped retirement）/待验证（external consumer）** C08: source authority intentionally thin | KEEP current actual profile consumer; do not resurrect approval service; **MEDIUM** |
| Preservation | `capabilities/preservation/README.md:6-11` Archivematica/Artefactual Fixity | **符合（native substrate）/待验证（deployed)** C01/C08 | keep native preservation provenance and scheduled fixity; **HIGH archive risk** |
| Capital | `domains/capital/README.md:1-14`; `trading/okx_demo_execution.py:399` late import; `okx_official_cli.py:17` reverse import | **部分符合** C07: a **static** two-module SCC exists; one side is a function-local import, so import-cycle failure is NOT established | record provider choice and import-time semantics; do not risk trading effects with speculative import surgery; **HIGH** |
| Game | `domains/game/README.md:20-46`, `examples/`, `planning/lego-plan-r1.json` | **部分符合** C01/C08: many examples, research and real product routes; no automatic demo→released claim | qualify old scenes/assets against actual engine packaging; no new gameplay feature; **MEDIUM/HIGH** |
| Composition | `packages/composition/README.md:3-22` bounded successor/interface contracts, explicitly not promotion authority | **符合（source responsibility）** C01/C04 | KEEP public contracts; check consumer ref before removing old profiles; **MEDIUM** |
| Data | `packages/data/README.md:10-36` ODPS/ODCS/DCAT read-only | **符合（source responsibility）** C04 | use domain-owned truth, no duplicate discovery registry; **MEDIUM** |
| Authority Catalog | `catalogs/authorities/README.md:3,20-43` separate identity/observation/discovery | **符合（authority separation by source）** C04/C06 | no conversion of currentness observations into admission; **MEDIUM** |
| Capability Catalog | `catalogs/capabilities/README.md`; `catalogs/capabilities/` provider/routing source | **待验证** C02/C04: catalog authority/installed reachability requires selected consumer inspection | source/producer-to-consumer slice before deletion; **MEDIUM** |
| Skills MCP | `extensions/chatgpt-skills-mcp/README.md:3-10` narrow filesystem-to-MCP compatibility bridge | **符合（declared scope）/待验证（installed parity）** C03/C09 | keep installed-currentness fences; no new skill registry, hooks only if native and justified; **MEDIUM** |
| Web | `apps/web/README.md:42` says SQLite canary Owner | **部分符合 / 待验证** C03/C04: explicit app/domain authority, not proof of generic PG-only cutover; app behavior/entrypoint graph requires deeper read | respect this separate current local contract; no forced storage swap from global preference; **HIGH user-data risk** |
| Chaoxing | `apps/chaoxing-autosign/` owner source/mise | **待验证** C01–C11: actual tests and source small, semantic endpoint not deeply read | KEEP; review current CLI and external effect truth before mutation; **MEDIUM** |
| Control Plugin | `extensions/ordivon-control-plane/` only 2 tracked paths, declared Owner in `owners.toml` | **待验证** C03/C08: thin source may be intentional compatibility | do not delete solely because file count is low; identify consuming client first; **LOW/MEDIUM** |

## B. Real static modularity and false-positive correction

From actual Python AST (`services/*/src` and bounded Owner library roots):
- Harness: **62 modules, 265 resolved local static edges, 0 multi-module SCC**.
- Gateway: **26 modules, 60 edges, 0 SCC**.
- Host: **36 modules, 101 edges, 0 SCC**.
- Artifact source/test-inclusive scan: **195 files, 275 edges, 0 SCC**; must not confuse test DAG with installed source graph.
- Composition: **10 modules, 16 edges, 0 SCC**.
- Capital: **65 modules, 54 edges, 1 two-module SCC**: `okx_demo_execution.py:399` imports `okx_official_cli` from inside an invocation path, while `okx_official_cli.py:17` imports the primary adapter. This is a potential maintenance/coupling issue, not a proven import-time failure; keep semantics and replay/credentials boundaries untouched until Owner justifies a change.
- Security: **14 modules, 10 edges, 0 SCC**.
- Skills MCP: **9 modules, 11 edges, 0 SCC**.

**Limitations:** local Python-import AST is not a complete call graph; dynamic imports, typed JS, Cargo workspace edges, package release consumers and execution effects remain unqualified. These counts cannot certify full module-boundary compliance.

The full source AST pass parsed **1,460/1,460** current Python files, observed **8,630** functions (at least 8 lines), **33** duplicate AST-body clusters (79 instances). A second global Git grep showed 20 plausible unreferenced private helper functions are **actually imported/consumed across files**. Do not delete by naive local call count.

## C. Prioritized findings: source path, actual issue, action, risk

| Severity / ID | Evidence / reproducible problem | Action (no new tests/features) | Risk and evidence standing |
|---|---|---|---|
| **HIGH / F01** | `tools/repo/test_exhaustive_coverage.py:110-111` asserts old `python3 verify.py`; current formal task is `tools/formal/mise.toml:17` with `python3 -I verify.py`. Exact unchanged source tests: 77 pass, 2 fail, 18 subtests pass | **REPAIR existing assertion** to current native command; proposed by PR #2012 | LOW code risk; must check actual command semantics and root CI |
| **HIGH / F02** | `tools/repo/test_exhaustive_coverage.py:630-634` assumes `sourceProblemCounts["STRUCTURE_SPLIT_REQUIRES_CONSUMER_WITNESS"]` is always present even for zero; unmodified main throws `KeyError` | **REPAIR existing test expectation**, sparse-key absence = zero; PR #2012 | LOW; ensure nonzero genuine disagreement still fails |
| **MEDIUM / F03** | `tools/repo/exhaustive_coverage.py:472,482-492` builds `cell_by_key` but then scans all `cells` for longest proper source prefix (O(N²) comparisons) | **REFACTOR** to native exact-key prefix lookups, preserve all non-directory-string prefixes and empty prefix; PR #2012 | LOW/MEDIUM; original source behaviour and duplicate-key checking unchanged |
| **HIGH / F04** | `services/harness/src/ordivon_harness/ordivon/loop.py:77,220-2340` concentrates Agent Run lifecycle in a ~2,121-line `_run` method; `run_continuity.py:129-3186` a 3,058-line class | **REFACTOR only natural state-transition seams**; first inspect PR #1835 and existing method/consumer tests, avoid blind split | HIGH semantic/temporal regressions; not a measured domain bug |
| **MEDIUM / F05** | `tools/repo/check_architecture_docs.py:1812-2157` 346-line issue census verifier; source file 2,524 LOC, plus `test_architecture_docs.py` 2,477 LOC | **REFACTOR** by current owned proof categories only if independent consumers benefit; PRs #1978/#1940 already touch checker | HIGH collision/verification-inversion risk, current code stays unchanged |
| **MEDIUM / F06** | `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` 10,788 LOC, `types.rs` 2,097 LOC, `engine.rs` 1,860 LOC | **REFACTOR narrowly** only when a real Runtime function/contract boundary can be proven; large test file not itself an architecture failure | HIGH recovery/Job effect risk |
| **MEDIUM / F07** | `capabilities/artifact/artifact_operations/providers/direct_python.py:95-606` houses provider orchestrator and `produce` at 439 | **REVIEW** whether native verification/build adapters are duplicated; do not extract general framework or overlap Artifact owner PR | HIGH proof/format correctness risk |
| **MEDIUM / F08** | `domains/capital/src/ordivon_capital/trading/okx_demo_execution.py:399` ↔ `okx_official_cli.py:17` AST cycle | **KEEP UNTIL REFUTED**; second edge is local delayed import, not proof of runtime cycle or wrong auth | HIGH real money/effect risk; no production change authorized |
| **LOW / F09** | Byte-identical copies: Security OAuth patch under `platform/security/contracts/agent-request-verifier-v1/patches/` and `labs/agent-admission-rs/patches/`; Game click WAV in two examples; two Media PNG copies under different productions | **KEEP until consumer/package provenance says reuse is safe**, then reuse native asset packaging if it actually saves cost | MEDIUM provenance/packaging risk |
| **LOW / F10** | `docs/architecture/STRUCTURE_R2.md:4,10,20` explicitly says PARTIALLY DEPLOYED and path is not ontology; `CURRENT_ARCHITECTURE.md:1-4` explicitly historical | **KEEP** clearly marked historical records; don't misreport as current docs drift | deleting historical explanation may lose accepted evidence |
| **LOW / F11** | `services/harness/src/ordivon_harness/sqlite_store.py:154` is actively imported by `scripts/harness_p0_scale_acceptance.py:18` and `scripts/run_adaptive_edit_r2_live_ab.py:29`; scripts include SQLite compatibility | **KEEP** until all real users are retired, despite PG-first runtime | removal would break existing operation; source only |
| **LOW / F12** | Readme/AGENTS direct relative-link scan across 134 source documents found **0 confirmed missing local paths** | **KEEP**; no fabricated blanket README path cleanup | regex check does not validate semantic accuracy or external links |

## D. Architecture assessment vs modern mature exemplars

- **Hexagonal / bounded contexts:** Ordivon has actual natural owner roots and public seams; don't add 21x boilerplate adapter layers simply to emulate Clean Architecture. Where Work CAS/Runtime physical effects/Harness cognition differ, explicit ports exist or should remain explicit.
- **Nx/Turborepo:** Ordivon has 21 registered Owner roots and **existing** `tools/repo/check_owner_boundaries.py`; the JS/TS-specific Nx lint and experimental Turbo boundaries must not be blanket-installed to replace existing Rust/Python verifiers. A style named `apps/packages` is not proof of modularity.
- **Single writer and event history:** Host Work and Runtime Job are different semantic state machines. Safe deletion requires a *current consumer/relation and evidence* proof, not just `terminal` status or static Git grep.
- **Management / system theory:** prioritize expensive changes and code paths (F04) but avoid code churn without demonstrable lowered coordination cost. DSM, native SCC and co-change count are lenses rather than compulsory registries.
- **Meta-risk:** writing more rules, badges and evergreen audits can become a second product. Existing present Spec and these phase artifacts are evidence for this one refactor program only, not evergreen Owner truth.

## E. Review state and falsification checklist

- Scope (what user asked): **yes**, explicitly frozen with no new features/tests/consumers.
- Theory correctness: **bounded**, R2.1 is a contract for responsibility, not proof for every file. Capital AST SCC corrected to *possible coupling*, not proven import-time error.
- Matt/ECC/Superpowers: existing source-first, two-axis Spec/Standards, small task/diff and actual verification preferred to more approval machinery.
- Over-conservatism: **falsified** for trivial stale-test and source-cell scan, directly repaired in PR #2012; no reason to block these on external installed truth.
- Superficial activity: mere 5,002-file tree is insufficient; this document records actual source/line defects and explicit high-risk untouched areas.
- Problem representation: distinguish owner identity, physical filesystem, static import, runtime effect, provenance and source vs installed/consumer, rather than collapsing all into 'modern/not modern'.
- Peer review: cross-owner Space messages `25884`, `25929` and `25941` requested falsifiable counterexamples; no new colleague endorsement has been observed for these specific audit artifacts at initial read. GitHub checks remain independent.

## F. Status

Phase 2 complete for documented **major module/source-slice** assessment; entire full-file semantic audit **INCOMPLETE**. The 5,002-file mechanical inventory is complete; unknown external consumers and uninspected deep files stay UNKNOWN. This prevents false completion.
