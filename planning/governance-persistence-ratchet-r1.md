# Governance Persistence Ratchet R1

Date: 2026-09-19
Status: ACTIVE MIGRATION RATCHET — explicitly disposable

## Purpose

This is not a new Ordivon architecture layer. It is a temporary anti-layer: a migration ratchet that prevents Task + Workspace + Evidence + Gate + Lens + Operator + Registry from turning into seven durable control planes.

Design target: conditional continuity + ephemeral execution carrier + owner-native evidence/provenance + stateless decision predicates + versioned analytical methods + stateless reasoning transformations + rebuildable discovery indexes.

The ratchet MUST be deleted when natural owners enforce the same boundaries and repeated lifecycle audits show that the local guard no longer changes decisions.

## External-standard mapping

| Local word | Mature owner/pattern | Consequence |
| --- | --- | --- |
| Task | OMG CMMN for adaptive case semantics; Temporal only when durable executable workflow is actually required | Host Task stays a narrow continuity claim, not a universal workflow/domain object |
| Workspace | Git worktree + Kubernetes finished-Job TTL, owner/dependent GC and finalizers | Workspaces are disposable carriers; retention needs a live claimant/finalizer-equivalent reason |
| Evidence | W3C PROV + in-toto/SLSA + OpenLineage | persist references, digests, provenance and claims; do not copy owner-native raw truth by default |
| Gate | OPA decision/enforcement split | gate should be a pure decision or external policy evaluation, not a stateful coordinator/store |
| Registry | MCP Registry / OCI distribution patterns | discovery/index points to natural packages/content; it is not global semantic truth |

Canonical references:
- https://www.omg.org/spec/CMMN/
- https://docs.temporal.io/
- https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/
- https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
- https://git-scm.com/docs/git-worktree
- https://www.w3.org/TR/prov-primer/
- https://in-toto.io/docs/specs/
- https://slsa.dev/spec/v1.2/build-provenance
- https://openlineage.io/docs/spec/
- https://www.openpolicyagent.org/docs
- https://modelcontextprotocol.io/specification/2026-07-28
- https://github.com/modelcontextprotocol/registry
- https://github.com/opencontainers/distribution-spec/blob/main/spec.md

## Negative-lifecycle laws

### Task

A Host Task exists only to preserve cross-session semantic continuity.

Candidate terminalization law:

(progress in {LOCALLY_COMPLETE, SATURATED})
AND valueNow == NO_POSITIVE_VALUE_NOW
AND wake.conditions == []
=> semantic continuity should normally become terminal

This is a review rule, not an automatic destructive rule: the exact current Task revision must be resumed before mutation.

### Workspace

Workspace deletion follows a finalizer-like checklist:

active_jobs == 0
AND output_commit_or_artifact_preserved
AND (clean OR explicit_dirty_handoff)
AND no_current_semantic_claimant_requires_workspace
=> close

The commit/artifact is the retained product; the mutable worktree is not the archive.

### Evidence

Prefer subject/claim + producer identity + source/run identity + digest + provenance relation + verifier/version + verdict over copied raw bytes. Raw evidence remains with Runtime, Git, benchmark, browser, API or other natural owner whenever replay remains possible.

### Gate

A gate is behavior: decision = f(input, policy).

It must not own a second persistence plane merely because the decision matters. Persist a decision receipt only when a real replay/audit consumer exists.

### Analytical methods

Analytical methods are not a durable Ordivon object class. The natural owner is the mature external discipline or the domain itself. Invoke the method directly and retain only decision-relevant derived evidence when needed.

The former local Lens Registry, Router, Compiler, Portfolio, reserve pool, and operator ceilings are retired. Reintroducing a local method-selection ontology requires an irreducibility argument showing why direct external/domain method selection is insufficient.

### Registry

A local registry is acceptable only when it is the natural standard-defined authority or a rebuildable discovery projection.

A fixed dispatch map wrapped in a Registry class is not a registry and should collapse to direct dispatch or a pure function.

## Retired planning and question meta-layer

The local project LEGO plan schema, validator, rollout carrier, and Question Compiler are retired. They are not replaced by a second Ordivon planning ontology.

Use the natural owner directly:

- software implementation plans: obra-superpowers/writing-plans;
- implementation execution: obra-superpowers/subagent-driven-development and test-driven-development when applicable;
- codebase architecture discovery: codex-user/acquire-codebase-knowledge plus the project source/tests;
- scientific question formation: codex-user/hypothesis-generation;
- experiment design: codex-user/experimental-design;
- security analysis: codex-user/security-threat-model;
- other domains: the domain-native method or mature external standard.

Derived plans/questions remain working artifacts. Project truth stays in project-native source, tests, specifications, domain records, and owner-native evidence.

## Baseline

Live 2026-09-19 audit:
- Host open Tasks: 270
- NO_POSITIVE_VALUE_NOW: 97
- LOCALLY_COMPLETE: 51
- SATURATED: 23
- Runtime open Workspaces: 150
- dirty: 39
- with active Jobs: 3
- ordivon-next: 90
- core-zero/core-elimination named: 51

These counts diagnose retention pressure. They do not independently authorize deletion.

## Executable enforcement

scripts/check_governance_persistence_r1.py checks repository-static rules:
- the retained governance roles have explicit persistence classes;
- Gate is stateless;
- Registry is rebuildable by default;
- retired local method-routing infrastructure remains absent;
- retired local planning/question schemas, validators, and skills remain absent.

Dynamic Task/Workspace cleanup remains owner-native and revision-fenced through Host/Runtime; this repository does not create a second lifecycle database.

## Sunset

This ratchet is successful when it can disappear.

Delete it after:
1. natural owners enforce the same retention/cleanup invariants;
2. three consecutive lifecycle audits show no material stale-carrier backlog requiring local governance;
3. removing the ratchet does not permit additive Lens/Operator/Registry/Gate state to re-enter through another maintained contract.

## Lifecycle audit — 2026-09-20

Standing: **SUNSET_NOT_MET / STALE_CARRIER_PRESSURE_REMAINS**.

This audit used the Host and Runtime owner-native inventory surfaces directly. Counts are point-in-time observations; they are not deletion authority and may move while concurrent agents create or close carriers.

| Measure | 2026-09-19 baseline | 2026-09-20 observation |
| --- | ---: | ---: |
| Host open Tasks | 270 | 269 |
| `NO_POSITIVE_VALUE_NOW` | 97 | 97 |
| `LOCALLY_COMPLETE` | 51 | 50 |
| `SATURATED` | 23 | 23 |
| Runtime open Workspaces | 150 | 283 |
| Runtime dirty Workspaces | 39 | 46 |
| Runtime Ordivon Next Workspaces | 90 | 140 |
| `core-zero` / `core-elimination` named Workspaces | 51 | 38 |

The static ratchet remains healthy (`scripts/check_governance_persistence_r1.py` passes), but the dynamic sunset criterion does not. Host continuity pressure is essentially unchanged and Runtime carrier pressure remains material.

### Owner-native cleanup performed

For Ordivon Next workspaces, a bounded cleanup required all of the following before closure:

- no current non-terminal Host Task checkpoint referenced the Workspace;
- Runtime reported the Workspace clean;
- no active Runtime Job was attached;
- the Workspace HEAD was already reachable from current `main`, proving the Git output was preserved;
- the Workspace predated the current-day parallel work, reducing interference with active agents;
- `workspace.close` used the exact current `sourceStateDigest` with `force=false`.

Nine historical Workspaces satisfied those conditions and were removed:

- `ws-commercial-marketing-integration-r2-20260919`
- `ws-agent-service-standards-wave3-integrate-r1-20260919`
- `ws-r40-reconcile-latest-b2eab-20260919`
- `ws-commercial-integration-r5-20260919`
- `ws-commercial-integration-r3-20260919`
- `ws-agent-service-main-integration-r1-20260919`
- `ws-standards-wave2-next-20260919`
- `ws-agentservice-standards-wave2-r1-20260919`
- `ws-toolchain-authority-census-r3-20260919`

A separate bounded census found 112 clean, Host-unclaimed Ordivon Next Workspaces whose HEADs were **not** reachable from current `main`. They were deliberately retained: a clean worktree is not proof that its unique commit has been integrated, archived, rejected, or handed off. Deleting those carriers without resolving that preservation question would violate this ratchet's own finalizer-like law.

### Sunset consequence

This observation does **not** count as one of the three consecutive clean lifecycle audits required for deletion. The ratchet still changes real decisions: it caused safe closure of preserved carriers while preventing deletion of unpreserved unique commits.

Do not add a second lifecycle database or custom garbage collector to solve this. Continue using Host claimant navigation, Runtime Workspace state, Git reachability, and exact close fences. The next audit should reassess whether natural-owner lifecycle behavior has made this local review rule redundant.
