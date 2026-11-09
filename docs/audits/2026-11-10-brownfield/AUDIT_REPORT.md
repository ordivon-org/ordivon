# AUDIT_REPORT — Ordivon 2026-11-10 source architecture review

**SourceCut:** `ef17d6879d12faa61fff3bb762b0d500d73c9113`. Source-aware audit, not installed-production audit. Evidence: `FILE_CENSUS.tsv` contains all 5,002 Git-tracked files; `INVENTORY.md` groups natural Owners. The 21-Owner mapping and scripts are real, but semantic source audits remain prioritized **bounded samples**, not a claim to have dynamically proved every file.

## 1. Current architectural outcome (principles applied, not style judgment)

The fundamental Ordivon modular monolith is **legitimate**. There are 21 named natural Owners in `tools/repo/owners.toml:4-111`; `mise.toml` delegates verification to native Owner tasks. Installed `tools/repo/check_owner_boundaries.py` already enforces exact active-source literal links and Python AST imports against `dependency_contracts.toml`. At this SourceCut the command passed: **2,320 active files / 10 Python packages / 31 declared seams / 38 declared references**; `check_structure_r2.py`, `check_architecture_docs.py`, `check_composition_architecture.py` passed too.

**Do not install Nx/Turborepo as duplicate policy engines.** Their mature ideas—tags/constraints, graph-aware affected tasks, DAG selection—already have comparable native mechanisms; Nx ESLint works on JS/TS only while language-agnostic Conformance is separate. Passing an active-source scan does **not** show dynamic imports, deployed components, environment authority or 5,002-file semantic correctness.

The actual failure pattern is **historical evidence and qualification retaining executable surface through self-referential tests/config, plus stale text claiming old state is current**. Correctness of each historic runner is not an economic consumer. Phase 4 must first shrink that surface.

## 2. Criterion assessment

| Criterion | Standing | Grounded evidence and implication |
| --- | --- | --- |
| C01 Domain/feature Owner-first | PASS for declared layout | `tools/repo/owners.toml`, roots `services/{host,runtime,harness,gateway}`, `platform/security`, `domains/capital`. No physical Computing root found; this is not automatically a missing service. |
| C02 Enforced module boundaries | PASS for active static scope; dynamic UNKNOWN | `tools/repo/check_owner_boundaries.py:85-109,225-310`, `tools/repo/dependency_contracts.toml`; native command PASSED, explicitly scans active subsets. |
| C03 Small interface/deep module | PARTIAL | Huge source/coordination files such as `services/harness/src/ordivon_harness/ordivon/run_continuity.py` (3,186 lines), `services/harness/.../loop.py` (2,366), and `capabilities/artifact/artifact_operations/providers/direct_python.py` (606) are candidates for interface-locality audit; size alone is not proof of a violation. |
| C04 Durable ownership / single writer | PARTIAL / installed UNKNOWN | `services/host/README.md` says Host PG/Alembic; `services/runtime/README.md` owns Job/Attempt; `apps/web/README.md` documents an intentional separate SQLite **web canary**. Do NOT globally force a DB replacement because Finance chose PG. Installed state was not inspected. |
| C05 Current schema/docs consistent | FAIL, evidenced Finance historical doc | `domains/capital/docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md:15-35,47,70` still claims SQLite current, whereas `domains/capital/src/ordivon_capital/accounting/postgres_ledger.py`, `domains/capital/README.md` and `domains/capital/docs/ARCHITECTURE.md` say PG-current source. |
| C06 External owner selection | PARTIAL | `domains/capital/config/{external_owner_census,candidate_tool_surface_registry,legacy_replay_surface_registry}.json` retains historical candidates; meaningful current source imports are distinct from provenance. |
| C07 Effect/admission separation | PASS for explicit source boundary, live UNKNOWN | `services/gateway/README.md` explicitly non-authoritative; `services/harness/README.md` Run≠Task; `domains/capital/src/ordivon_capital/trading/execution_reconciliation.py` distinguishes intent/effect; neither doc nor a test proves live financial provider truth. |
| C08 Cohesion / no duplication | PARTIAL | Finance `portfolio/portfolio_counterfactuals.py` recomputes Risk-style exposure separately from `risk/portfolio_risk.py` (function overlap). More semantic comparison required before changing output. |
| C09 Dead code / self-retaining loops | FAIL, evidenced | `domains/capital/tools/legacy_replay/` (13 files), `tools/tigerbeetle_0_17_9/` (8), `config/legacy_replay_surface_registry.json`, `tests/test_legacy_replay_surface_isolation.py:7-83`. The latter asserts historical files exist even though current scripts must not call them. A later exact source scan found `tools/nautilus_rc4/run-m6-differential:9` calling the old LEAN replay; it was retired with the carrier. |
| C10 Graph-aware native tasks | PASS for observed static implementation | `mise.toml` root Owner delegations and `tools/repo/{affected_owners,ci_owner_shards,convergence_plan}.py`; `repo:ci` runs existing boundaries, checks and GitHub policy. |
| C11 Discoverability / current truth | PARTIAL | `AGENTS.md:1-100` has explicit source/permission/UNKNOWN guidance; Finance historical docs contradict current Accounting and multiple 2026-09 runner narratives are only history. |
| C12 Proof/consumer separation | PASS as stated; actual refinement UNKNOWN | `domains/capital/formal/README.md` and `services/gateway/README.md` explicitly bound model evidence; `packages/composition/README.md` mechanical completion ≠ domain acceptance. Not an end-to-end installed proof. |

## 3. 21-owner evidence matrix

Standing is source-architecture correspondence, NOT owner verification result or a numerical ranking. One line is not a claim every file was semantically read.

| Owner | Standing | Concrete anchor / intervention | Risk of premature action |
| --- | --- | --- | --- |
| host | PARTIAL | `services/host/src/ordivon_host_v2/social_space_queries.py`, `social_contracts.py`, `README.md`: PG/Alembic factual owner, verify real Journal/CAS boundaries before moving persistence | breaking durable Work/Space meaning |
| runtime | PARTIAL | `services/runtime/crates/ordivon-runtime-core/src/runtime`, `services/runtime/README.md`; Job/Attempt/Workspace owner; large Rust test source not reason to split state | loss of recovery and exactly-once claims |
| harness | PARTIAL | `run_continuity.py` and `loop.py` large; search for duplicate coordination/weak seams in existing functions | losing bounded Tool/Provider continuity |
| gateway | PASS for declared boundary | `services/gateway/src/ordivon_gateway/{mcp_server,upstream,research_routes}.py`; thin routing only | leaking downstream authority into proxy |
| security | PARTIAL | `platform/security/README.md`, `policies/agent_admission.rego`; current proof must remain with natural Security owner | permission drift |
| network | PARTIAL | `platform/network/README.md` and `formal/egress_policy_refinement.py`; explicit egress/Network authority separate from Gateway | breaking live VPN/ingress |
| workstation | PARTIAL | `platform/workstation/providers/cloudflare/scripts/ordivon_edge_release.py` (1,318 lines), real Tofu and local setup | broken physical machine release |
| artifact | PARTIAL | `capabilities/artifact/artifact_operations/providers/direct_python.py` and `scripts/artifact_oci_package.py`; inspect dual validation, avoid replacing Artifact bytes with task conclusions | loss of reproducibility/packaging |
| distribution | UNKNOWN for internals | `capabilities/distribution/` manifest/README; no scoped deep execution in this pass | installer/release regressions |
| media | PARTIAL | `capabilities/media/productions/live-relay-001/render/live-relay-001-master.mkv` (41.5 MB) and source MP4 (16.5 MB) are Git tracked; determine real downstream media evidence before pruning binaries | deleting required authored assets |
| preservation | PARTIAL | `capabilities/preservation/scripts/verify_source.py`; must retain artifact fixity independent of media production | false archival claims |
| game | PARTIAL | `domains/game/examples/room-encounter/addons/dialogue_manager/dialogue_manager.gd` (2,009 lines); third-party addon must not be treated automatically as first-party duplication | broken game content |
| capital | FAIL in historical housekeeping; domain boundary PARTIAL | `domains/capital/docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md` false PG-current state; isolated legacy replay self-test loop; seven active source Owners largely coherent | finance contract regression |
| composition | PASS for stated bounded scope | `packages/composition/src/ordivon_composition/verification_obligation_r1.py` (770 lines); keep gate mechanistic, not domain approval | false completion authority |
| data | PARTIAL | `packages/data/src/ordivon_data/{catalog,odps_projection}.py`; no independent current global data store | duplicate data custody |
| control-plugin | PASS for thin packaging | `extensions/ordivon-control-plane/plugin.json` and `mcp.json` | wrong public transport |
| skills | PARTIAL | `extensions/chatgpt-skills-mcp/src/ordivon_skills/catalog.py` (750 lines); Skill selection cannot authorize effect | silent privilege transfer |
| web | PARTIAL | `apps/web/src/{store,app}.ts` SQLite canary + opaque session, separate scope from Capital PG | deleting valid web canary state |
| chaoxing-autosign | PARTIAL | `apps/chaoxing-autosign/chaoxing_mvp/{engine,ledger}.py`, local bounded app | breaking app utility |
| authority-catalog | PASS for declared scope | `catalogs/authorities/scripts/authority_catalog.py` (280 lines), catalog not live policy | mistaken standards certification |
| capability-catalog | PARTIAL | `catalogs/capabilities/ele/studies.py:55-58` actually consumes outdated Finance doc; fix producer's current truth without inventing new router | broken research browse link |

## 4. Prioritized concrete findings (no speculative additions)

| ID | Severity | Paths and observed fact | Action | Risk and proof |
| --- | --- | --- | --- | --- |
| F01 | HIGH | `domains/capital/docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md:15-35,47,70` declares SQLite current; `catalogs/capabilities/ele/studies.py:56` consumes it. | Clarify in place: PostgreSQL owner now, SQLite qualification strictly historical. | Must preserve current study path and older archived provenance; check Capital and catalog native tasks. |
| F02 | HIGH | 21 files `domains/capital/tools/{legacy_replay,tigerbeetle_0_17_9}` plus the transitive `tools/nautilus_rc4/run-m6-differential` caller, self-test `tests/test_legacy_replay_surface_isolation.py` and path-presence registry. Active `src/` and default `mise.toml` do not directly run them. | RETIRE this self-referential historical executable carrier, self-test and registry in one reversible batch; retain frozen `wave_b/fixtures/wave_a_target_portfolio.json`. | Dynamic consumer closure UNKNOWN; versioned Git restore remains available. Run existing Capital verify, repo owner/architecture checks after change. |
| F03 | MED | `domains/capital/docs/ARCHITECTURE.md:108,172` advertises executable historical runners as preserved while PG/SDL current. | Rewrite to explicitly historical Git lineage, no current executable branch for retired families. | Do not remove current Nautilus qualification branches in the same batch. |
| F04 | MED | `domains/capital/docs/OKX_DEMO_EXTERNAL_EXECUTION_R1.md` has no matching direct tracked-file path references, dated standalone account. | RETIRE document (Git history retains it) after checking current canonical demo interfaces still documented elsewhere. | Human external bookmarks UNKNOWN, reversible Git deletion. |
| F05 | MED | `domains/capital/src/ordivon_capital/portfolio/portfolio_counterfactuals.py` duplicates Risk aggregate vs `risk/portfolio_risk.py`. | Retain current public shape; refactor existing implementation to consume one Risk arithmetic owner only after checking type/result equivalence. | Precision/rounding and input failure behavior may change; no new tests in this program. |
| F06 | MED | `capabilities/media/productions/live-relay-001/render/` contains 58 MB of tracked MP4/MKV. | HOLD asset pruning until current product/provenance consumer is checked; consider Git LFS in a future permitted delivery scope, not as an automatic cleanup. | High risk deleting authored creative output; do not equate file size with dead code. |
| F07 | MED | `services/harness/src/ordivon_harness/ordivon/{run_continuity,loop}.py` together exceed 5k lines. | Future bounded codebase-design review on call paths, not mechanical file split. | Large cohesive state machine can be intentionally deep. |
| F08 | LOW | Existing cross-Owner verifier `tools/repo/check_owner_boundaries.py` passes, but its supported active set is smaller than 5,002 tracked files. | Record exact coverage; avoid installing new Nx. Strengthen declared constraints only when current violation found. | False claim of all-file runtime enforcement. |

| F09 | MED | `catalogs/capabilities/ele/studies.py:50-58` still registered `domains/capital/docs/EXTERNAL_IMPLEMENTATION_QUALIFICATION_R1.md`, absent from source at current SourceCut. | Delete only its already-dead source-list entry; keep the existing live Finance census projection unchanged. | No new catalog source or consumer. Verify capability-catalog's existing tests and repo:ci. |

## 5. Audit approach and collaboration truth

- Repo static source and current native boundary checks are OBSERVED, not deployed/loaded currentness.
- Agent reviewers were requested in Host Space `space:ordivon-capability-task-forum-r1:20261101` and `space:ordivon-task-portfolio-and-proof-gates-r1:20261101` with concrete source SHA and evidence contract. Social post is NOT approval.
- Automated read-only Codex sibling reviews failed at invocation due access/usage limit. No peer conclusion from those jobs is credited as proof. Continue with existing source checks and real Space replies if observed.
- No weak-model trials, no new test apparatus, no consumer routes.

## 6. Decision criteria for Phase 4

Use unchanged native Owner tests as a **regression witness**. If a test fails because it asserts a deleted unused implementation file must exist, retire that self-referential test with the implementation only when source-current consumer closure is established; never fake PASS or add tests. Keep source/public interface work distinct from cleanup, and keep Finance market/broker/PG effects outside this audit.
