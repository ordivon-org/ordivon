# AUDIT_REPORT — architecture standards versus actual source

**Subject**: Git main ef17d6879d12faa61fff3bb762b0d500d73c9113; all 5002 paths physically enumerated. Ratings below are **module-level source judgments** over sampled key files, not full running-system qualification.

## Overall finding

The repository already has a 21-owner manifest, module-aware verify commands and explicit SourceCut/evidence distinctions. It is neither an unstructured monolith nor universally equivalent to Nx/Turborepo. Its strongest debt is incomplete legacy replacement and repeated planning/evidence mechanisms. Merely migrating folders to apps/packages would not settle state authority or platform semantics.

## 21 Owner compliance assessment

| Owner | Judgment | Actual source evidence | Reason | Requested disposition | Risk |
|---|---|---|---|---|---|
| runtime | PARTIAL | services/runtime/crates/ordivon-runtime-core/src/runtime/platform/linux.rs | Linux systemd/cgroup code is partitioned, but pg_server.rs still explicitly rejects Windows context; do not confuse Linux PG with cross-platform PG. | MODIFY after Windows natural-owner migration, not in stock-only scope | High: Windows native live writer could still depend on legacy storage. |
| host | PARTIAL | services/host/src/ordivon_host_v2/service.py:148 | integrity now checks snapshot-history continuity; historical gap remediation and installed DB status are different questions. | KEEP present check; repair actual old data only via Host owner | High: invented historic revision would corrupt audit provenance. |
| harness | NONCONFORMING | services/harness/evals/fresh_agent_ab/run_live_v1.py:13; run_live_v2_currentness.py:14 | both historical live runners import removed ordivon_harness.capability_discovery. Also SQLiteHarnessStore has current script/test readers. | DELETE two invalid runner entrypoints via existing PR #2009; KEEP raw experiment evidence | Low for source-only deletion; medium if unobserved dynamic replay depends on path. |
| gateway | PARTIAL | services/gateway/src/ordivon_gateway/{routing.py,owner_protocol.py,capability_authz.py} | transport, authorization, routing have separate files; independently verify runtime client reuse rather than assume gateway high-level correctness. | KEEP; inspect real owner client lifecycle before claiming cleanup | High: permission or MCP behavioral change could affect installed gateway. |
| network | PARTIAL | platform/network/consumers/browserless/systemd/network-v2-browserless-wireguard.service | OS provider and consumer service declarations exist; static files cannot prove loaded network state. | KEEP systemd owner units; retire only after live provider release | High: broken VPN/DNS egress. |
| security | PARTIAL | platform/security/contracts/agent-request-verifier-v1/patches/oauth4webapi@3.8.8.patch | same bytes also appear under labs/agent-admission-rs/patches; separate package versions and consumers must be traced. | MAY MERGE only with package lock/patch consumers; no immediate deletion | Medium: patch mismatch in lockfiles. |
| skills | PARTIAL | extensions/chatgpt-skills-mcp/pyproject.toml | distinct package/wheel and Skill bind/read/verify surface; do not install a second Agent rule engine. | KEEP; review open stock-only PR #2011 | Medium: duplicate hook layers could obstruct agents. |
| workstation | PARTIAL | platform/workstation/systemd/service-profiles/loki.service.d/20-ordivon-observability-heavy.conf | same override bytes apply to different services; same content does not mean same runtime consumer. | KEEP service identities; evaluate only current unused drop-ins | High: loss of journaling/monitoring. |
| artifact | PARTIAL | capabilities/artifact/artifact_verification/stage.py; capabilities/artifact/scripts/artifact_verify.py | two named verification stages could encode different evidence standing, inspect call graph before merger. | MODIFY repeated verification only after native owner proves equivalent contracts | High: false artifact standing. |
| distribution | PARTIAL | capabilities/distribution/README.md | distinct destination/receipt owner, not content conversion authority. | KEEP role; inspect overlapping stock-only PR #2007 | Medium: delivered artifact receipts lost. |
| media | PARTIAL | capabilities/media/productions/live-relay-001/render/live-relay-001-master.mkv | large binary production asset retained in Git; size alone cannot prove regenerability or licensable substitution. | KEEP until material asset/source owner proves replacement | High: irreversible creative artifact loss. |
| preservation | PARTIAL | capabilities/preservation/SOURCE_BOUNDARY.json | source boundary plus METS/A3M historical evidence define preservation duty beyond cache. | KEEP real recovery facts; audit repeat publication manifests | High: backup cannot be recovered. |
| game | PARTIAL | domains/game/examples/beacon-relay; domains/game/examples/room-encounter | multiple Godot/Bevy game/exemplar surfaces not interchangeable without downstream player contract. | KEEP current native code; coordinate with Game owner stock audit | Medium: preview/controls breakage. |
| capital | PARTIAL | domains/capital/config/legacy_replay_surface_registry.json | legacy replay paths are currently referenced by tests; cannot assert dead despite legacy name. | KEEP bounded replay; retire only with explicit versioned replay decision | High: historical trading/accounting replay semantics lost. |
| data | PARTIAL | packages/data/AGENTS.md; packages/data/README.md | real Data Port owner instructions exist; peer PR #2004 removes three redundant guides but PR #1970 overlaps. | MERGE docs only after coordinating owner PRs; preserve model and source identity | Medium: unmerged source facts overwritten. |
| web | PARTIAL | apps/web/src/server.ts; apps/web/src/app.ts; apps/web/package.json | app package has deployable code, but duplicate business-state ownership must be checked against Gateway. | KEEP thin source entry; do not migrate domain state without proof | Medium: web API contract break. |
| chaoxing-autosign | PARTIAL | apps/chaoxing-autosign/README.md | small application has a standalone flow; peer PR #2017 retires synthetic MVP; no source overlap. | KEEP current real workflow; review PR #2017 | Medium: user-visible service lost. |
| composition | PARTIAL | packages/composition/src/ordivon_composition/interface_contract_r2.py | explicit interface/contract code; checking its source does not imply production realization proof. | KEEP model; prefer Lean/Z3/Pacti native rather than new calculus | Medium: incorrect theorem-to-code promotion. |
| authority-catalog | PARTIAL | catalogs/authorities/README.md | 376 tracked authority records; not all are current or garbage, must distinguish historical observation and current binding. | KEEP authoritative evidence; audit by actual referents | High: provenance destroyed. |
| capability-catalog | PARTIAL | catalogs/capabilities/providers/worktrunk.md | existing Git-native Worktrunk shadow comparison admitted reuse constraints, not an automatic rollout mandate. | KEEP provider evidence, prune only retired unreferenced old candidates | Medium: wrong external provider choice. |
| control-plugin | PARTIAL | extensions/ordivon-control-plane/plugin.json | two manifest files have native plugin and repository consumers, not empty wrapper solely by small size. | KEEP current thin manifest | Low: plugin disappears. |

## Prioritized concrete findings

| Severity | Owner | Source path(s) | Mechanism / defect | Action | Risk |
|---|---|---|---|---|---|
| P0 | Repository | docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md; open PR #2006/#2010/#2012/#2013/#2014 | multiple overlapping stock-only specification amendments; repeated parallel canon risks semantic drift | MERGE into existing current owner programme; do not add new global governance | Medium: conflicts and excess context, not verified runtime fault. |
| P0 | Runtime | services/runtime/crates/ordivon-runtime-core/src/runtime/platform/linux.rs; services/runtime/crates/ordivon-runtime-mcp/src/server/pg_server.rs | PG source path includes Linux-only systemd and rejects Windows context; cross-platform semantic core is not equivalent to Windows deployed behavior | SPLIT by natural platform owner only after native consumer readiness; current scope no functionality changes | High: accidental removal of Windows live legacy writer. |
| P1 | Harness | services/harness/evals/fresh_agent_ab/run_live_v1.py; run_live_v2_currentness.py | both import a module no longer in source; no static caller path and studies retain independent raw results | DELETE dead runners via PR #2009, do not recreate removed dependency | Low source risk, unknown external dynamic invocation. |
| P1 | Harness | services/harness/src/ordivon_harness/{sqlite_store.py,postgres_store.py} | two storage implementations still have bound tests and scripts; exact implementation-level equality and production writability not fully established | HOLD until native PG migration; reduce duplicate helper only when consumers covered | High: replay history and old test compatibility. |
| P1 | Artifact | capabilities/artifact/artifact_verification/stage.py; capabilities/artifact/scripts/artifact_verify.py | multiple verification forms require distinction between stage evidence and valid standing | REVIEW and merge only truly equivalent verification work with natural Owner | High: incorrect pass/fail semantics. |
| P1 | Repo | tools/repo/{check_architecture_docs.py,exhaustive_coverage.py,convergence_plan.py} | large repository mechanics scripts; size indicates investigation hotspot, not by itself a design failure | CHECK deep-module interfaces and native Git reusability before splitting; PR #2012 already touches coverage | Medium: duplicate governance and CI time. |
| P1 | Host | services/host/src/ordivon_host_v2/service.py | history continuity now covered by integrity but old PG snapshot gaps remain a different data problem | KEEP fixed source; natural Host owner resolves historical records without invented revisions | High: false historical authority. |
| P2 | Data | packages/data/docs/AGENT.md; HUMAN.md; LEGO_CENSUS.md | overlap with active Data source guide; PR #2004 handles exact document subtraction | DEFER to Data owner PR; do not duplicate source edit | Medium: conflicts with #1970. |
| P2 | Security | platform/security/contracts/agent-request-verifier-v1/patches/oauth4webapi@3.8.8.patch; platform/security/labs/agent-admission-rs/patches/oauth4webapi@3.8.8.patch | same SHA within separate package roots; not necessarily duplicate authority | TRACE patch lock and installed scope before dedupe | Medium: dependency installer drift. |
| P2 | Capital | domains/capital/config/legacy_replay_surface_registry.json | tests and historical replay tool paths are explicit consumers | KEEP bounded historical replay for now | High: loss of reconstruction. |
| P2 | Workstation | platform/workstation/systemd/service-profiles/{loki,netdata,vector}.service.d/20-ordivon-observability-heavy.conf | duplicate bytes have distinct service selectors | KEEP service drop-ins; no blind hash-based pruning | Medium: loss of observability. |
| P2 | Media | capabilities/media/productions/live-relay-001/render/live-relay-001-master.mkv | large tracked original/renders differ from disposable build cache | CLASSIFY via Media source/rights before any deletion | High: loss of unique media output. |

## Cross-cutting contract check (2025–2026 project patterns)

1. **Nx boundaries**: tools/repo/owners.toml and check_owner_boundaries.py already implement a repository source classification and verification seam; Nx ESLint rule covers JS/TS, not all Ordivon Python/Rust dependencies. Adding Nx as second cross-language proof system would be duplicate process.
2. **Turborepo apps/libs**: apps/web is a deployable app with package manifest; Runtime, Host and Gateway preserve different persistent state owners. Do not move all business state to packages as a purely spatial refactor.
3. **Clean/Hexagonal and Parnas**: separate physical provider/transport adapters from owner domain transition. Runtime platform/linux.rs is clear native seam; inability to conclude Windows compatibility is real, but user forbids adding that missing capability in this audit.
4. **DDD**: Host Work revision and Runtime Attempt are distinct; both may use PG without becoming one aggregate or duplicate journal.
5. **R2.1/contract**: a Lean model with A/G and proof cannot license deletion of installed services or historical records. A formal true statement on an abstraction is not a full code refinement witness.
6. **Matt/ECC/Superpowers**: file length/identical bytes are hypotheses, not failures. For high-risk replace/delete, trace precise read path; for trivial dead code use Git rollback and existing native regression rather than new tests.

## Limits and independent falsification questions

- All 5002 files have content identity but not every current dynamic caller was visited. Ratings are partial by construction; none is a blanket 100% compliance certificate.
- What actual installed process or consuming test contradicts an asserted dead path? What version/Owner has it?
- Is the proposed refactor merely moving complexity into a new shared module without reducing the interface or maintainer obligations?
- Does a claimed zero-reference file hold unique scientific results, copyrights, actual history or backup data?
- What is the exact before/after owner claim, and what command would falsify it?
- Was the candidate already modified by another Agent open PR? Then do not edit it concurrently.

## Python static cross-owner import observations

This analysis resolves only top-level local packages under Owner src/*/__init__.py; dynamic imports, Rust/Cargo dependencies, TS aliases and external runtime links remain outside this partial graph. A directed edge is not itself a forbidden dependency.

Observed 6 Python import references across 2 owner pairs; public roots 10.

| From Owner | To Owner | Import references | Source example(s) |
|---|---|---:|---|
| non-owner-source | composition | 3 | studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/r5c_backfill.py:17 ordivon_composition; studies/experimental-episodes/episode-store/src/ordivon_experimental_episode_store/r5c_projection.py:14 ordivon_composition; studies/experimental-episodes/episode-store/tests/test_data_product_contract.py:8 ordivon_composition.cross_domain_binding_r3 |
| non-owner-source | data | 3 | studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py:19 ordivon_data.catalog; studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py:20 ordivon_data.local_evidence; studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py:21 ordivon_data.odps_projection |
