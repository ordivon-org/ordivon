# Phase 1 responsibility survey — 2026-10-27

## Scope and evidence qualification

Exact inspected source: `75fc00bdec12268bd92ad85c6138b6f1be76bf3d` (origin/main observed 2026-10-27). This is a bounded first-layer **static survey** of all 18 entries in `tools/repo/owners.toml`, plus cross-system tooling. It does not certify installed services, complete dynamic consumer closure, or formal correctness.

The original Recursive LEGO R2.1 Skill and `references/formal-model.md` govern qualification. A source file, method, Tool, or owner partition is not automatically a LEGO. Candidate decomposition requires a goal-relative responsibility, inputs, outputs, behavioral contract, acceptance and meaningful composition/replacement boundary.

All rows have repository-entry inspection and responsibility/consumer **leads**. Semantic coverage varies; a plan's existence is not completion. Source paths below are reproducible evidence anchors, not runtime observations. All untested installation, execution and external-provider behavior remain UNKNOWN.

## All registered partitions

| Partition | Observed responsibility and consumer leads | Inspected anchors | Bounded gaps |
|---|---|---|---|
| next | Task-local binding of mature knowledge/capabilities; research/web gates invoke binding | `meta/next/README.md`; `meta/next/scripts/cross_domain_binding_r3.py`; `meta/next/scripts/research_artifact_gate_r3.py`; `meta/next/scripts/web_security_gate_r3.py` | Domain profiles, experimental episodes, authority lifecycle, terminal problem outcomes |
| composition | Stateless task-local composition; Next imports public API; compatibility and currentness separated | `packages/composition/README.md`; `packages/composition/src/ordivon_composition/interface_contract_r2.py`; `packages/composition/src/ordivon_composition/__init__.py` | Cognitive circuits, successors, obligation closure; interface compatibility is insufficient for refinement |
| control-plugin | Agent Plugin client connection configuration; consumes Gateway MCP | `extensions/ordivon-control-plane/plugin.json`; `extensions/ordivon-control-plane/mcp.json` | Installed client, authentication and live endpoint |
| runtime | Workspace/Job/Attempt, execution, replay and reconciliation; consumed by Gateway/Harness/current audit | `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/workspace.rs`; `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/admission.rs` | Runner/providers, Windows, namespace, retention, full transition/refinement coverage |
| host | Work/Social/Attention continuity; northbound tools and Gateway continuity consume it | `services/host/README.md`; `services/host/src/ordivon_host_v2/service.py`; `services/host/src/ordivon_host_v2/contracts.py` | Remaining social/work relations, complete production consumers and installation |
| harness | Caller-neutral Agent Run, Provider/Tool continuity and completion evidence; applications consume facade | `services/harness/src/ordivon_harness/api.py`; `services/harness/pyproject.toml` | Loop/recovery/completion, browser/providers, actual Runtime integration |
| gateway | Northbound actions, capability projection, routing and correlation; control-plugin consumes it | `services/gateway/README.md`; `services/gateway/src/ordivon_gateway/routes.py` | Access/authz, worker transactions, actual route/version behavior |
| skills | Agent Skills discovery/resolve/read bridge; trust, quarantine, scope precedence and stale snapshot fences | `platform/skills/README.md`; `platform/skills/src/ordivon_skills/catalog.py` | Scanner/parser, hostile packages, SEP2640 and live release currentness |
| security | Exact-subject provider evidence and policy standing; gate assembler consumes evidence | `platform/security/README.md`; `platform/security/src/ordivon_security_v2/evidence.py`; `platform/security/scripts/assemble_gate_input.py` | Provider validity, OPA, signatures, agent verifier/authz, complete threat model |
| workstation | Desired state, realization, inventory and standard integrations; shell/services consume configuration | `platform/workstation/README.md`; `platform/workstation/contracts/README.md`; `platform/workstation/workstation/nix/nix/home.nix` | Ansible/Tofu resources, provider state, backup/recovery, actual node state |
| network | Mature networking composition and workload-specific path evidence; consumer profiles include Capital | `platform/network/README.md`; `platform/network/config/sing-box/direct.json`; `platform/network/scripts/capability-report.py` | Destination fencing, provider failover, dynamic consumers, actual path/fault behavior |
| artifact | Format-specific construction/validation and exact request/profile/material commitment; receipt consumes commitment | `capabilities/artifact/artifact_core/contracts.py`; `capabilities/artifact/artifact_core/admission.py`; `capabilities/artifact/artifact_operations/receipt.py` | Format validators, trust/build/workflow, delivery and end-consumer use |
| distribution | Optional cross-provider effect-safety profile for exact occurrence/authority/readback requirements | `capabilities/distribution/README.md`; `capabilities/distribution/scripts/admission_bound.py`; `capabilities/distribution/scripts/admission.py` | Normalize/refusal/reconciliation, provider readback and actual effects; not a mandatory control plane |
| media | Optional authored expression/production/context/QC; Studio Agent routes consumers | `capabilities/media/README.md`; `capabilities/media/src/ordivon_studio/agent_surface.py` | Research validity, trial ledger, rendering/QC/rights/providers; ordinary UI does not imply Media responsibility |
| preservation | Exact local preservation/source/evidence profile; external Archivematica/Fixity retain provider semantics | `capabilities/preservation/SOURCE_BOUNDARY.json`; `capabilities/preservation/scripts/verify_source.py`; `capabilities/preservation/README.md` | Actual AIP/restore/fixity, off-site failure domains and provider operation |
| game | Read-only research/mechanism/relation/counterexample retrieval for assembly tasks; no current first-party game | `domains/game/README.md`; `domains/game/package.json`; `domains/game/scripts/external-knowledge-query.ts` | Source quality, other queries, Godot fixture, player outcomes; retrieval is not recommendation correctness |
| capital | Market/accounting composition, policy input, evidence/reconciliation; shadow and ledger consumers | `domains/capital/src/ordivon_capital/accounting/substrate.py`; `domains/capital/config/crypto_data_adapters.json`; `domains/capital/README.md` | Full trading path, authorization, PostgreSQL/TigerBeetle, economic acceptance |
| web | Browser principal/session/WebAuthn and protected mutations; human and agent request consumers | `apps/web/src/server.ts`; `apps/web/src/app.ts`; `apps/web/package.json` | Remaining routes, session/store, CSRF/Origin negatives, Agent rail and browser E2E |

## Cross-system evidence and historical plans

`tools/repo/check_architecture_docs.py` projects owner-local R1 graphs and separately interprets the other plan versions. Its graph consistency checks do not establish the truth of every descriptive contract. `tools/repo/owners.toml`, root task/configuration, Git SourceCuts, owner-native tests, Skills, Gateway and Runtime are existing discovery paths; no new registry is introduced.

The inspected 75fc00b baseline contains 11 project-lego-plan carriers, including 8 R1 carriers with 51 projected nodes / 100 declared edges. R2/R3 planning records have distinct semantics and must not be added to these counts as equivalent LEGO identities. At the inspected source the Host R1 still described retired Task/Board modules. New semantic changes in this branch must be distinguished from that source snapshot and from future main integration.

Open Runtime candidates #914–#916 overlap R07–R09; this batch changes Host, leaving Runtime candidate selection separate.

## First materialized semantic delta

Host R1 keeps O01–O04 identities while aligning Work/Social/Attention/PostgreSQL descriptions to schema 10. Four recursively qualified subresponsibilities are added:

- O09 WorkSnapshotCAS: revision/digest identity, concurrent commit and replay; parent O01.
- O10 MessageContentIntegrity: durable content identity shared by get/search/resume/duplicate-post consumers; parent O02.
- O11 TopicCursorReentry: actor/topic message-sequence navigation and bounded recovery; parent O02.
- O12 AttentionChangeHorizon: actor-scoped change-sequence projection with no-skip pagination; parent O03.

Their distinct state, consumer requirements, observable failures and replacement conditions justify decomposition without introducing runtime components. Parent-child edges denote architectural unfolding, not an established compositional proof. R3 maps retained responsibilities onto current R1 identities and records retired vocabulary.

An independent source review confirmed the strongest consumer chain: `test_social_work_fabric_postgres.py::test_r2_topic_cursor_relation_readback_reasons_and_reentry` passes Attention navigation into Topic recovery. The two cursor domains must remain distinct. Existing corruption, CAS and pagination tests are reusable implementation evidence when rerun against this candidate; none is a formal refinement proof.

## Concrete gaps and next decomposition

1. Runtime, Harness and Network still need bounded recursive decomposition beyond this first-layer survey.
2. Host Work relations, ActorRef, subscriptions, participation, intents and search need further qualification; method count must not determine LEGO count.
3. Gateway→Runtime/Host, Harness→Tool/Runtime, Media→Artifact and Capital→Network need consumer-specific contracts and failure propagation evidence.
4. Capital README describes a Nautilus OKX native-client primary path, while `crypto_data_adapters.json` declares `OKX_OFFICIAL_PUBLIC_REST_WS` primary and Nautilus `HISTORICAL_CANDIDATE_EVIDENCE_ONLY`. This is a source documentation/configuration conflict; deployed transport is UNKNOWN.
5. Runtime formal/configuration, Host schema migrations, Skills release snapshots and Network fingerprints need exact installed-consumer version bridges.

## Incremental reuse boundary

Repeat the existing Git/source projection for exact commits and compare changed owner plans and source anchors. Reuse evidence only when its property, implementation, assumptions, tool version and consumer scope remain applicable. A changed contract or environment requires reassessment of dependent evidence. Existing projections do not supply a complete dynamic impact closure; unresolved dynamic edges remain explicit gaps.

Phase 1 remains open. This survey establishes entry coverage for all registered partitions and a first concrete Host semantic update; it does not establish complete recursive semantic coverage.

## Candidate validation

Runtime Job `job-01a17bad-0d48-7fb2-85c5-c183a451998c`: dedicated temporary PostgreSQL 18.6 cluster, Alembic through schema 0010, locked dependencies, Ruff and full Host suite: **402 passed**, no skipped tests. Cluster was stopped and removed by the command's exit trap. This is isolated candidate implementation testing, not production installation or formal verification.

Initial Host verification caught an obsolete exact dependency-set assertion. The regression now retains the required O04→O01/O02 dependency subset while permitting independently evidenced semantic additions; existing graph validation checks endpoints and relation consistency.

Final identity falsification detected historical O05 ScopeBoundCursor reuse. The four additions now use previously unused O09–O12; historical Git plan identities were enumerated before reassignment. The original tombstone regression remains intact. Plan-only identity changes do not invalidate the unchanged implementation test evidence. Final architecture/graph regressions and root repo:ci were rerun: 384 targeted tests and 442 root-gate pytest cases passed, plus root native checks.

## Designed-scope frontier — 2026-10-28 addendum

Inspected main: 5e61ef7b27acbf98fce2374b65f35536ebbaaba5.
Classification candidate: 949c62de7c98d0de88c1b9f697c46fbf5360ab70.
The earlier survey's historical SourceCut and acceptance remain separately scoped.

One complete Git tree does not enumerate every responsibility Ordivon is designed
to consume. Existing exhaustive_coverage.py now exposes coverageDomain and
coverageQualification in full, recursive-cell and exact-path query results.
COMPLETE_AT_SOURCECUT applies to the source index, not to the cardinality of a
returned subset. Designed responsibilities, actual consumer closure, installed
realization and external-environment coverage remain UNKNOWN.

| Agent-facing scope | Existing evidence | Remaining coverage obligation |
| --- | --- | --- |
| Study and domain acceptance | meta/research/publication-closure-profile-r2.json | Actual Study, venue, external-standard and reserved Human decision consumers; profile presence is not scientific acceptance |
| Identity and credential realization | CURRENT_ARCHITECTURE sections 3/6; Runtime, Security and Workstation | Current principal/provider/effect binding per environment; configured routes are not authorized effects |
| Durable orchestration and recovery | Workstation Temporal/n8n; Harness Run; Runtime Job/Attempt | Actual workflow consumers, restart/replay and external-effect reconciliation |
| Browser and operational observation | CURRENT_ARCHITECTURE sections 2/7/9; Workstation observability | Active browser/session capability, trace activation and useful causal-query acceptance |
| External source and consumers | STRUCTURE_R2 source/runtime topology boundary | Independent repository identity/currentness and real consumer links; matching relative filenames do not prove equivalence |
| Live state and data lifecycle | Runtime Job/Attempt/Workspace/Artifact and Host Work/Space/Topic/Message APIs | Current instances, retained data, recovery consumers and retirement conditions; source paths do not enumerate durable records |

These are investigation scopes, not new Owners, services or a second registry.
Reject unnecessary proposals; investigate unknown existing consumers before deletion.

Actual bounded subtraction in this batch:

- Remove affected_owners.changed_paths only on the candidate where the new revision
  selector serves both CLI and CI. Its sole remaining caller was its own test.
  Preserve the cross-owner move law through the real revision selector and Git manifests.
- Remove present-tense no-trace-storage assertions from Operations/Workstation cards.
  Retain dated observations and use existing Vector/Tempo source for discovery.
- Retain Research profile R1: an Artifact test still consumes it. R2's existence
  alone does not justify deleting R1.

No directory migration or production activation is performed. Source aliases
aid navigation; real consumer and realization obligations determine later moves.

A bounded native read on 2026-10-28 independently confirmed Gateway
system.describe version 0.8.1 and 17 capability names, including Research
composition metadata beyond the four core route families. Host host.status
reported PostgreSQL schema 10; Linux runtime.describe reported its native
local target configured and available. These observations do not establish
Windows availability, effect permission, credential continuity or end-to-end
consumer success. The dated September deployment baseline must not be used as
a complete current capability inventory. Refresh the native interfaces when
a decision depends on those facts; do not copy another permanent live catalog.

A finite catalog crosscheck found eleven package cards but twelve named families
across the package index and CAPABILITY_PACKAGES_R1.md. Business Operations was
the omitted index entry. The index now links the existing section and historical
ERPNext/Frappe acceptance rather than creating another card, provider or service.
This fixes discovery documentation; no runtime dispatch failure was demonstrated.
