# Brownfield audit report | source-qualified findings

**Source:** ef17d6879d12faa61fff3bb762b0d500d73c9113; **mechanically observed:** 5002 files, 21 Owners.
**Source-only baseline checks:** tools/repo/check_owner_boundaries.py PASS (2,320 active files, 31 seams); tools/repo/check_architecture_docs.py PASS. No claim of full live/domain acceptance.

## Priority findings and exact existing action

| ID | Priority | File | Finding | Evidence-backed disposition | Main risk |
| --- | --- | --- | --- | --- | --- |
| P0-01 | HIGH | docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md (sha256:1294c1ba07df) | Superseded 220-line plan with stale #1921/#1925 status, no identified current static/dynamic internal consumer; canonical Agent contract and unique research are elsewhere. | DELETE via existing PR #2010; preserve Git history; do not create duplicate PR. | Risk: external bookmark or unobserved consumer. |
| P0-02 | HIGH | docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md (sha256:c701f6f173ad) | Claims 20 current Owners where current manifest has 21; time-bound 2026-11-06 production claims are stale. | REWRITE once, through existing conflicting PR #2006/#2010; choose one canonical carrier. | Risk: losing unique cross-Owner requirements or concurrent conflict. |
| P0-03 | HIGH | apps/chaoxing-autosign/chaoxing_mvp/cli.py (sha256:a3a6355dd575) | Demo-only fake session/discovery/submission with no proven installed product consumer; 11-file owner still navigable in root. | DELETE only via existing PR #2017 after verifying unique physical/external consumer and root owner references. | Risk: hidden running worker outside repo. |
| P1-01 | HIGH | tools/repo/affected_owners.py (sha256:6b2e4f853c8d) | Prior source selector Git CWD vs manifest root mismatch; independent PR #1999 still open and CI failed. | FIX existing source path contract on that PR; do not broaden this audit with test/consumer additions. | Risk: selecting foreign history and misrouting Owner verification. |
| P1-02 | MEDIUM | tools/repo/check_architecture_docs.py (sha256:7c6236027c88) | 2524 lines; one validation function ~346 lines. Multifunction architecture verification may be shallow, but length does not prove defect. | SIMPLIFY only when current check callers and policy source reveal duplicated real logic; existing #2012 work overlaps root. | Risk: weakening coverage or duplicating verifier. |
| P1-03 | MEDIUM | tools/repo/exhaustive_coverage.py (sha256:64d41ac7214a) | 2052 lines; candidate large functions 275 and 256 lines; used by convergence_plan and preservation test. | REVIEW deep-module/deletion test, keep actual effects and callers; not approved for wholesale relocation. | Risk: erasing real dependency/coverage evidence. |
| P1-04 | MEDIUM | apps/web/src/app.ts (sha256:ec49b263eefc) | 721-line Fastify route assembly; web server.ts already 20-line composition root and store is split into session/grant/schema files. | SIMPLIFY only demonstrably redundant logic behind existing modules; do not enforce a new packages/ split by appearance. | Risk: session/CSRF/WebAuthn behavior change. |
| P1-04B | HIGH | apps/web/src/config.ts (sha256 on frozen source) | integerEnv uses parseInt: observed ORDIVON_WEB_PORT=8080garbage silently accepted as 8080. | FIX with strict decimal-string parsing; same config error boundary; no added test files. | Risk: invalid legacy input is now deliberately rejected. |
| P1-04C | MEDIUM | apps/web/src/agent-authority.ts + identity-digests.ts + app.ts | stableEffectDigest and stableDigest compute identical SHA-256 of JSON.stringify; observed sample equality and two call sites. | DELETE duplicate function; REUSE existing digest carrier without new abstraction. | Risk: re-binding an exported name used by external consumers; repo source scan finds only app.ts. |
| P1-05 | MEDIUM | apps/web/src/store.ts (sha256:5f11322625b5) | 810-line domain-owned SQLite canary store; README explicitly says SQLite isolated canary, not live PG. | KEEP current state authority; examine duplicate SQL transaction paths before any code movement. | Risk: accidental change to replay/CAS/approval semantics. |
| P1-06 | MEDIUM | services/harness/evals/fresh_agent_ab/run_live_v1.py (sha256:c150c752aace) | Historical A/B runner under evals, existing PR #2009/#2015 addresses retirement. | DELETE via natural Harness owner only; no independent duplicate action. | Risk: unexpected research replay consumer. |
| P1-07 | MEDIUM | platform/workstation/scripts/host_historical_projection.py (sha256:7dab17dac833) | Historical Host-v1 projector with separate Workstation zero-base PR #2008. | RETIRE only after checking projection inputs/provenance and PR overlap. | Risk: losing unique archival evidence. |
| P1-08 | MEDIUM | capabilities/distribution/evidence/r8-validation-20260912.json (sha256:91d73f8dd582) | Legacy distribution evidence family, source readback differs from documentation past; PR #2007 covers them. | DELETE or KEEP by exact unique durable obligation; let Distribution owner reconcile. | Risk: false retirement of release evidence. |
| P1-09 | MEDIUM | services/host/migrations/versions/0013_unicode_substring_gin.py (sha256:bf2b189df97a) | Migrations 0001..0013 are present in Git; installed PG revision not established by this scan. | KEEP migrations; compare real DB Alembic stamp before claiming installed status. | Risk: destroying migration history and rollback compatibility. |
| P2-01 | LOW | tools/repo/ci_telemetry.py (sha256:2e925a7e8d29) | summary() AST identical to queue_telemetry.summary(); tiny copied 12-line helper does not justify new shared wrapper. | KEEP unless measured cross-consumer repeated maintenance outweighs new coupling. | Risk: high abstraction cost for cosmetic dedup. |

## Owner-by-Owner actual module census

All rows are SOURCE_INVENTORIED; details after the semicolon are targeted hypotheses/observations, not completed semantic certifications.

| Owner | Tracked files | Evidence point and actual scope | Standing |
| --- | ---: | --- | --- |
| artifact | 425 | 425 files, 195 Python/174 JSON; prior verification generations need natural Owner audit | SOURCE_INVENTORIED / REVIEW_PENDING |
| authority-catalog | 376 | records/ and observations/ dominate (365 JSON); provenance not expendable on byte dedup | SOURCE_INVENTORIED / REVIEW_PENDING |
| capability-catalog | 77 | provider cards vs installed capabilities are separate facts; 58 Markdown | SOURCE_INVENTORIED / REVIEW_PENDING |
| capital | 399 | 399 files, 185 Python/89 JSON; PIT/ledger/experiment evidence remain distinct | SOURCE_INVENTORIED / REVIEW_PENDING |
| chaoxing-autosign | 11 | 11 files, fake/demo-only MVP candidate for PR #2017 | SOURCE_INVENTORIED / REVIEW_PENDING |
| composition | 86 | formal/ and schemas/ exist; model satisfaction does not prove installed refinement | SOURCE_INVENTORIED / REVIEW_PENDING |
| control-plugin | 2 | two plugin JSON manifests, intentionally very thin; no grounds for a new wrapper | SOURCE_INVENTORIED / REVIEW_PENDING |
| data | 19 | 19 files, 3 Lean source/9 Python; native Data Owner PR #2004 handles guides | SOURCE_INVENTORIED / REVIEW_PENDING |
| distribution | 30 | 30 files, 15 evidence; PR #2007 retirement candidate | SOURCE_INVENTORIED / REVIEW_PENDING |
| game | 387 | 387 files including 333 examples; actual Godot/Bevy source vs demo artifacts distinct | SOURCE_INVENTORIED / REVIEW_PENDING |
| gateway | 107 | 107 files, auth contract supports schema v2 and v3; source gateway version 0.10.8 | SOURCE_INVENTORIED / REVIEW_PENDING |
| harness | 731 | 731 files, including 182 tests and 139 evidence; historical runners under natural Owner PR | SOURCE_INVENTORIED / REVIEW_PENDING |
| host | 117 | 90 Python files, Alembic 0001–0013 source migration; Work Journal/CAS remains Host-owned | SOURCE_INVENTORIED / REVIEW_PENDING |
| media | 553 | 553 files; 213 productions/110 research; unique work assets not low-value duplicates by hash | SOURCE_INVENTORIED / REVIEW_PENDING |
| network | 236 | 236 files including 105 consumers and 27 .service; active config/install comparison required | SOURCE_INVENTORIED / REVIEW_PENDING |
| preservation | 46 | 46 files, 32 artifacts; destruction requires actual recovery source check | SOURCE_INVENTORIED / REVIEW_PENDING |
| repository-unmapped | 441 | 441 docs/studies/.agents/tools/global files; mapping not automatically evidence of missing Owner | SOURCE_INVENTORIED / REVIEW_PENDING |
| runtime | 452 | Rust source 126 files; PG migration 0006 and separate fresh-epoch SQL; live PG state not inferred | SOURCE_INVENTORIED / REVIEW_PENDING |
| security | 162 | 162 files, Rego, TS, Python separate PDP/contracts; no root replacement | SOURCE_INVENTORIED / REVIEW_PENDING |
| skills | 45 | 45 files, includes exact-binded MCP catalog; PR #2011 overlap | SOURCE_INVENTORIED / REVIEW_PENDING |
| web | 35 | 35 files, 15 TS src modules; canary SQLite authority documented and server bootstrap thin | SOURCE_INVENTORIED / REVIEW_PENDING |
| workstation | 265 | 265 files, Ansible/Nix/systemd; Host-v1 projector PR #2008 | SOURCE_INVENTORIED / REVIEW_PENDING |

## The two most important counterexamples

1. A byte-identical LICENSE or independent Game/Media source-render image cannot be deleted by hash equivalence alone: licenses, source assets and consumer/readback roles differ.
2. A root Owner-boundary scan PASS is not proof every dynamic import, native service instance or external consumer was traversed; conversely an unchecked stale root plan is not saved by a theoretical “maybe someone reads it”.

## Current constraints / failure attribution

Open PRs #2006, #2010, #2014 share architecture documentation files; the same file must not be changed twice. PR #2010 GitHub root-verification failure was previously observed with upstream preflight/repo mechanics abandoned, so it is not evidence that the old-plan deletion is semantically invalid. #1999 root CI is blocked; not claimed complete. Native checked source only, not deployed.

## Audit strategy and remaining coverage

Concrete paths in the table were inspected beyond their directory name. The remaining files have a complete source inventory and higher-level responsibility diagnosis, but line-by-line mathematical/behavioral review remains Owner-by-Owner work. Never mark these as PASS on the strength of file enumeration.


## Frozen-source Owner-by-Owner architecture qualification (21 natural Owners)

The following bounded 21-owner source assessment is retained from source-level audit ef17d6879d12faa61fff3bb762b0d500d73c9113, originally merged via https://github.com/ordivon-org/ordivon/pull/2033. PASS only refers to the named source-level responsibility/declared interface; PARTIAL means an observed structural limit; UNKNOWN means insufficient observation. None certifies installed behavior. The original filenames and line numbers are frozen-source evidence, not live currentness. Capital source changes merged via https://github.com/ordivon-org/ordivon/pull/2040 supersede old historical housekeeping FAIL claims where actually corrected. Natural Owner/current Git governs the real status.

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

## 2026-11-10 canonical SourceCut consolidation (post-review, main e037af933)

Four separately merged source-only audit-report sets were discovered at docs/audits/2026-11-10/, docs/audits/2026-11-10-brownfield/, docs/architecture/audits/2026-11-10/ and docs/architecture/audits/2026-11-10-brownfield/. They repeat six Phase 0–5 report names and overlapping 5,002-file ledgers. The first set is retained here as the sole current report; its exact inventory was re-compared to all 5,002 distinct paths in frozen Git commit ef17d6879d12faa61fff3bb762b0d500d73c9113 with no missing/extra paths.

Unique bounded discoveries in the other reports remain in their actual natural Owner source and original merged PR history rather than being copied into a permanent second report authority:

- **Capital stock subtraction:** [PR #2040](https://github.com/ordivon-org/ordivon/pull/2040) is merged. The historical LEAN/TigerBeetle replay family, self-retaining presence checker and dead catalog reference were reviewed/retired. Current source and remaining limitations live in domains/capital/docs/FINANCE_DIRECTORY_OWNER_AUDIT_R1.md and domains/capital/; do not infer production trade execution.
- **Runtime PG reclaim guard:** [PR #2028](https://github.com/ordivon-org/ordivon/pull/2028) is the original bounded Runtime source/doc cleanup, including correcting the native Git subprocess return-code guard in services/runtime/scripts/ordivon-runtime-pg-reclaim and retiring superseded plans. The detailed formal model limitations stay in services/runtime/formal/README.md; a source merge does not prove installed Runtime effects.
- **Repository index and native test drift:** [PR #2012](https://github.com/ordivon-org/ordivon/pull/2012) is merged; tools/repo/exhaustive_coverage.py and existing verification/test call sites, not an audit narrative, carry its final semantics.
- **Cross-Owner static graph observations:** [PR #2033](https://github.com/ordivon-org/ordivon/pull/2033) captured current entrypoints and a Capital delayed-import SCC that also imports successfully in the observed bounded check. File size or a syntactic SCC is not itself a behavioral defect.

The original alternate reports remain recoverable by Git history of [#2040](https://github.com/ordivon-org/ordivon/pull/2040), [#2028](https://github.com/ordivon-org/ordivon/pull/2028), and [#2033](https://github.com/ordivon-org/ordivon/pull/2033). Removing duplicated current documentation does not undo their verified source changes, revoke native Owner receipts, or claim production acceptance. Existing Runtime and Capital source-document links are simply repointed to this current report set, not reconnected to any new product consumer.
