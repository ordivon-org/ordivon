# Ordivon Repository Brownfield Modernization — Source-First Execution Spec R1

Date: 2026-11-10 (Asia/Shanghai)
Standing: active, source-qualified maintenance plan; not a new architecture authority or semantic LEGO registry.
Exact audit SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113 (origin/main at audit admission).
Natural owners: the existing 21 entries in `tools/repo/owners.toml`; all effects remain with the relevant Owner.
Existing governance: `docs/architecture/STRUCTURE_R2.md`, `docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md`, `AGENTS.md`, GitHub Merge Queue and owner-native `mise` tasks.
Collaboration: existing Host Space `space:ordivon-whole-system-optimization-r1:20261002`, existing repository-operating-model topic, message sequence 25884. Space is not Git, test or domain truth.

## 1. Goal and freeze rule

Re-examine every actually tracked repository file as part of the CURRENT Git source, identify architectural misrepresentations and maintainability costs, then remove, reuse, consolidate or refactor existing implementation while preserving the current externally observable behavior and existing Owner responsibility.

This is a BROWNFIELD maintenance program, not new product development. **Do not add functionality, new tests, new consumer paths, new interfaces, services, registries, task trackers, monitoring planes or abstract LEGO wrappers.** Existing failed tests may be repaired when their *expectations* demonstrably drifted from an already-effective native contract; that is not an authorization to weaken a valid invariant. Use existing tests and negative evidence to qualify refactors. Do not delete unique historical proofs, external assets or untracked/private user data merely because lexical references are absent.

No automatic global rewrite and no wholesale migration to Rust. Select the smallest natural implementation and prefer proven upstream packages where replacing truly duplicative custom behavior is source-, interface- and lifecycle-equivalent.

## 2. Full file inventory and evidence discipline

The read-only per-file enumeration using exact `git ls-files -z` (not a recalled directory tree) covered 5,002/5,002 tracked source paths; 4,575 identifiable textual files; aggregate repository file bytes 123.2 MB. All 1,460 Python sources parsed as AST. An AST pass observed 8,630 functions of at least eight lines and 33 identical-body clusters (79 instances); a byte-level SHA-256 pass found 14 duplicate clusters (31 files). None of these counts is a proof of dead code, duplicate responsibility or removable consumer.

Present tracked top-level inventory:
- services 1,407 (harness 731, runtime 452, host 117, gateway 107)
- capabilities 1,054 (media 553, artifact 425, preservation 46, distribution 30)
- domains 786 (capital 399, game 387)
- platform 663 (workstation 265, network 236, security 162)
- catalogs 532 (authorities 376, capabilities 77, knowledge 74, data-products 5)
- packages 105 (composition 86, data 19)
- docs 104, studies 89, tools 65, .agents 63, extensions 47, apps 46, profiles 17, .github 13, root 9, tests 2.

Important source hotspots (not automatic defect labels):
- `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` 10,788 lines; `runtime/types.rs` 2,097; `runtime/engine.rs` 1,860.
- `services/harness/src/ordivon_harness/ordivon/run_continuity.py` 3,186 lines, `loop.py` 2,366 and `sqlite_store.py` still actively consumed by some scripts/tests.
- `tools/repo/check_architecture_docs.py` 2,524 lines; `tools/repo/exhaustive_coverage.py` 2,052; `tools/repo/test_architecture_docs.py` 2,477.
- `capabilities/artifact/artifact_operations/providers/direct_python.py` 606 lines.
- `capabilities/media/artifacts/creative-library/catalog-v1.json` and `capabilities/media/productions/archive-archipelago-001/source/creative-library-catalog-v1.json` are large but not byte-identical.
- Exact duplicate packaged images, audio, Security patch/config and historic evidence may have distinct independent consumers. Do NOT deduplicate as a naked byte-count exercise.

Audit each Git file by: (i) source identity/path, (ii) true natural owner/source region, (iii) parser/type and concrete responsibility, (iv) actual imports/config/runtime/product consumers including dynamic discovery, (v) mature upstream/native replacement, (vi) change coupling/churn and cost, (vii) preservation/effect/knowledge value, (viii) disposition REMOVE / REUSE / COMPOSE / REFACTOR / KEEP with source-backed rationale, (ix) existing verification and publication status. Use a derived, rebuildable scan and evidence tied to the Git commit; **no new persistent per-file state database or mandatory per-file 11-tuple**. Files without dynamic/remote-consumer closure must remain UNKNOWN rather than proven unconsumed.

Detailed semantic review is incremental by Owner and high-impact path. The full machine inventory is complete; the semantic/source consumer review of all 5,002 files is NOT complete and must never be presented as such.

## 3. Mature methodological providers (not delegated authority)

Matt Pocock Skills @ 4ae2317ddb22b046e264: `to-spec` synthesizes established context without new interviews, `to-tickets` creates independently reviewable slices and only real blocking edges, `code-review` separates standards defects from spec defects. Adapt to existing Host Work/GitHub issue only when task continuity requires it.

ECC @ d2ef2680594f9a17526a: `brownfield-retrospective` begins with observable code, reconstructs current behavior/history, derives a four-axis gap register (thinking, coding practice, missing capabilities, technology selection), and closes with actual regression verification. **Suppress the missing-features axis for this maintenance-only phase**; do not fabricate new product backlog. `search-first` and change-impact drive reusing mature providers. Do not create docs/retro subtrees for every directory or import ECC's hook/tracker architecture.

Obra Superpowers @ 22f0b463e7a5e579904d: isolated Git worktree, `writing-plans` with exact paths/commands, `verification-before-completion` with observed results and existing-test behavior preservation. New RED tests are forbidden by this task, so use existing focused/Owner tests, old-vs-new deterministic comparisons and exact source diffs instead. Do not reproduce their own subagent scheduler inside Ordivon.

Additional mature and mathematically grounded references: Martin Fowler *Refactoring* (small behavior-preserving transformations); Bazel/Cargo native modular dependency boundaries rather than new home-grown cross-owner graphs; Pacti A/G contracts, Liskov–Wing behavioral subtyping, Hoare/weakest precondition and TLA+ when a real current interface warrants proof; DSM dependency clustering for candidate review; NASA verification-versus-validation; Stafford Beer VSM for coordination diagnostic (not literal five new services); Toyota Poka-Yoke/Jidoka for actual-boundary correction; Theory of Constraints for prioritizing real bottlenecks and avoiding unbounded speculative WIP.

## 4. Formal, semantic and architecture constraints

Use canonical R2.1 only for an independently contractable responsibility, `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`. A file, a test or an incidental import is not automatically a LEGO. Existing implementation and its natural Owner continue to own the contract.

Let P denote an implementation, E a stated environment, c an existing named observer, Obs_c the observer's projection of input/output, failures, temporal effects and ordering. A behavior-preserving refactor should discharge the scoped obligation:

    Obs_c(Traces(P_after | E)) = Obs_c(Traces(P_before | E))

This is a **proof obligation**, not a statement that running the test suite establishes full equivalence. For a pure deterministic helper, equivalence can follow from the same predicate/selection law. For effects, concurrency, binary artifacts or unknown dynamic consumers, require natural Owner comparison and retain residual UNKNOWN. Do not alter safety/liveness/authority guarantees to simplify a file.

Owner boundaries and verified external technology are prior constraints, not accidental source paths. Cross-Owner import or data-provider substitution needs explicit natural-owner compatibility; change approval belongs to existing GitHub publication authority, not an Agent's narrative. No new generic evaluator to judge whether a model is conservative.

Graph view: typed edge classes Git import, syntax call, config, build, deployment, evidence-read, effect and domain-consumer. Lexical path hits are hints, not runtime observations. DSM/reverse-dependency focus and Git churn select review candidates; a duplicate hash or >1000 LOC is only a candidate defect.

Optimization: first meet the exact current behavior/authority constraints; then reduce code/mental-state volume, duplication, dependency coupling, expensive re-evaluation and WIP. Prefer REMOVE unused mechanisms, REUSE mature native provider, COMPOSE existing interfaces, then a small justified REFACTOR. Avoid metrics (LOC, number of deleted tests) as substitutes for value.

## 5. Owner-local audit frontier; avoid other Agents' active PRs

These are entry points for targeted review, not a claim that their adjacent files have been semantically cleared:

| Source responsibility | Entry files / suspected debt | Authority/modern practice |
| --- | --- | --- |
| Repo/architecture mechanics | `tools/repo/exhaustive_coverage.py` expensive cell hierarchy scan; existing stale assertions in `test_exhaustive_coverage.py`; `check_architecture_docs.py` is under competing PRs | Git tree, Python stdlib/AST, isolated read-only projections and repo:ci |
| Runtime | `services/runtime/crates/ordivon-runtime-core/src/runtime/{engine.rs,types.rs,tests.rs}` | Rust module decomposition, native PG Job/Attempt; preserve lifecycle/effect semantics |
| Harness | `services/harness/src/ordivon_harness/ordivon/{loop.py,run_continuity.py}` and legacy SQLite adapters | Existing Harness Run contract, native PG, no new Agent Runner |
| Gateway | `services/gateway/src/ordivon_gateway/upstream.py` and upstream identity | Native MCP client pooling/HTTPX, Gateway is non-authoritative |
| Host | `services/host/src`, historical Work snapshots | PostgreSQL/FK and actual Space/Message relations; terminal Work with consumers is not garbage |
| Security | `platform/security/contracts` vs `labs` duplicate patch/config | AuthZEN/OPA/Rego native contracts, preserve provenance |
| Network | `platform/network/substrates/shared-egress` | Provider-native VPN/Podman, no new proxy control plane |
| Workstation | `platform/workstation` Ansible/systemd/Temporal/n8n | Reuse upstream providers, native deployment readback |
| Artifact | `capabilities/artifact/artifact_operations/providers/direct_python.py`, existing verification adapters | Existing Artifact claim/evidence and upstream format verifiers; avoid overlap with live Artifact PR |
| Media | `capabilities/media` production artifacts and creative-library catalogs | FFmpeg/native media operators, distinguish source from rendered publication |
| Distribution/Preservation | `capabilities/{distribution,preservation}` | Native provider publication and Archivematica/BagIt; retain genuine external receipts |
| Capital/Game | `domains/{capital,game}`, legacy replay / engine examples | Native PG/trading simulation and Godot/Bevy; no new strategy or gameplay feature |
| Composition/Data | `packages/{composition,data}` | Typed source interfaces, read-only composition, established validators |
| Catalogs | `catalogs/{authorities,capabilities,knowledge,data-products}` | Discovery != admission; no duplicate registry |
| Skills/Control plugin/Web/Chaoxing | `.agents/skills`, `extensions`, `apps` | Agent Skills/MCP/native frontend, preserve actual client contracts |
| Studies/Docs/Profiles | `studies`, `docs`, `profiles` | Research provenance, Diátaxis/ADR currentness, retain only genuine current entrypoints |

Full coverage requires continuing each Owner's evidence-backed per-file review, not producing a 5,002-line unverifiable prose list. Work is divided by natural Owner; do not modify peer branches or ship multi-Owner speculative rewrites.

## 6. Complete execution DAG with independent acceptance

B0 — EXACT SOURCE BASELINE (complete for this cut). Read remote main SHA, root/owner README and AGENTS, `owners.toml`, existing CI and currently active PR file sets. Observe the main's existing verification state BEFORE changing source. This audit found two existing `test_exhaustive_coverage.py` failures (77 passed, 2 failed, 18 subtests) on unmodified main: obsolete `python3 verify.py` assertion after isolated `python3 -I verify.py` cutover, and false assumption that a sparse zero Structure-split counter exists. These failures may be repaired without adding test coverage.

B1 — PER-FILE SOURCEMAP (depends B0; machine inventory done). Reconstruct by Owner and actual producer/consumer including source imports, CI jobs, launch/deploy scripts and external users. For every removal candidate, establish true no-consumer or already-equivalent replacement; otherwise KEEP/UNKNOWN. Aggregate source inventory remains derived from Git, not permanently registered.

B2 — DEEP CODE/ARCHITECTURE REVIEW (starts with B1 selected file sets). Check behavior, contract assumptions, duplicate implementations, monolithic responsibilities, invalid historical authority, technology choice, coupling graph and Git co-change. Compare to appropriate upstream mature module designs; do not force a single framework on every Owner. Record actionable path:line evidence and actual caller before a proposed edit.

B3 — SMALL MAINTENANCE PATCHES (requires one B2 proven defect). Own one narrow slice/Owner; permit correction of stale baseline expectations; use existing validations and immutable before/after output comparison. No new feature, test, consumer, schema, registry or framework. Refactor is admissible only when observable behavior/metadata is preserved under the scoped assumptions.

B4 — CROSS-OWNER CONSOLIDATION (B2 and native Owner readbacks, independent). When two modules actually implement one responsibility, prefer a mature incumbent. Remove the redundant implementation only after the surviving consumer remains valid; preserve history and independent archival receipts. Avoid ongoing PR code and do not add adapter layers to rationalize duplicate code.

B5 — DOC/STUDY/ASSET DELETION (B1,B2 evidence). Classify historical snapshots and packages against real static/dynamic consumers and retention/provenance requirements. Retire obsolete current references and dead research wrappers via Git deletion rather than a parallel archive database. Exact-content duplication is not proof that independent runs/asset packages are interchangeable.

B6 — TWO-AXIS AND SIX-QUESTION CROSS-REVIEW (each patch before integration; existing Host Space). Standards vs Spec (Matt), plus: theory applied with correct assumptions? mature method native rather than ritual? over-conservative or under-scoped? surface-only cleanup? correct problem representation/Owner? baseline and current consumer unchanged? Independent Agent findings need concrete source lines and counterexamples; Space acknowledgement is not a publication approval gate.

B7 — NATIVE INTEGRATION (B3–B6). Existing focused tests, native Owner verify/mise, Structure/owner/GitHub checks, exact diff from pinned main, GitHub PR and Merge Queue; track SOURCE, MERGED, INSTALLED and DOMAIN_CONSUMED separately. A code-only refactor can be qualified as SOURCE/MERGED without claiming installed or domain improvements not observed.

B8 — ITERATE BY ACTUAL BOTTLENECK (after B7). Continue next high-value owner slice only if evidence justifies it; no mandatory daily report, no endless review, no 'done' claim for uninspected file sets. The program is complete only when every file has an evidence-qualified disposition or explicit UNKNOWN and material changes have native consumer standing.

## 7. First executable source slice — repo read-only inventory

Existing code: `tools/repo/exhaustive_coverage.py::derived_problem_legos`. It already constructs a unique `cell_by_key[(sourceZone, physicalPrefix)]` map for duplicate detection, then computes each parent by scanning every other cell and selecting the longest proper prefix. This is a proven avoidable quadratic scan for source cell count N.

Optimization is purely internal: for each cell search its own physicalPrefix proper prefixes from longest to shortest in the already validated map. Include the empty prefix to retain old semantics, and preserve same-zone and strict-length tests. No new external entrypoint or serialized field.

Mathematical identity: for fixed key map, the first matching descending strict prefix is exactly the maximum-length candidate of the old exhaustive comprehension. Candidate complexity goes from O(N^2) pairwise prefix checks toward O(sum(length(prefix))) hash lookups; because Python slices copy characters, a conservative character-work bound is O(sum(length(prefix)^2)). There is no assumption of directory separator alignment; all proper string prefixes are considered so existing behavior is not narrowed.

Before the code patch, fix ONLY two stale existing native test expectations: `python3 verify.py` -> `python3 -I verify.py` matching current `tools/formal/mise.toml` and missing sparse counter key -> `dict.get(key, 0)` matching zero counts. These corrections do not add tests or change producer behavior. Run exactly the current `tools/repo/test_exhaustive_coverage.py` and compare existing tests before/after (77/79 passing baseline, then all passing). Run `python3 tools/repo/check_architecture_docs.py`, `python3 tools/repo/check_structure_r2.py`, `python3 tools/repo/check_owner_boundaries.py`, `git diff --check` and `mise run repo:ci` when available. Record any environment limitations honestly.

Files modified in B3 first slice: `tools/repo/exhaustive_coverage.py` and `tools/repo/test_exhaustive_coverage.py` only. This Spec is the single temporary maintenance contract and should be removed or consolidated into existing Owner documentation once its actionable responsibilities are consumed. No new standing Code Owner/Agent authority.

## 8. Stop and downgrade rules

- If an apparently dead private function is imported by a peer file, do not delete it. This happened in the source audit: all 20 locally unreferenced private-helper suspects had evidence of cross-file usage on closer inspection.
- If a big file is a generated, versioned or third-party resource with intentional immutable provenance, do not split it simply to meet a LOC threshold.
- If existing contract requires SQLite/read compatibility in a certain tool while PG is current production authority, do not delete that adapter merely because 'PG-first' is the desired deployment.
- If a peer PR already implements a correct remedy, cancel this slice rather than produce a competing PR. Check GitHub remote main/active PRs again at integration.
- If native checks fail at baseline, separate unrelated existing failures from introduced regressions and repair only substantiated stale assertions.
- If only a new diagram, duplicate Spec, arbitrary score or added policy remains after the proposed change, DELETE the proposal.
- Unknown external consumers or effects never become 'safe to delete' solely through no static textual references.

## 9. Handoff

Each bounded slice requires exact initial commit, changed file paths, a short observed-source problem statement, current behavior and existing verification commands, preserved behavior/contract, peer disagreement with concrete evidence, and final PR/merge/consumer standing. Preserve one implementation branch per non-overlapping slice, not a permanent global reform worktree or new issue database. Existing Git/Host/Runtime remain authoritative for their own facts.
