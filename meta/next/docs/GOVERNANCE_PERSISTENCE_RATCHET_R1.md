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
- the shared project LEGO schema cannot acquire mandatory Gate/Lens/Operator/Registry concepts.

Dynamic Task/Workspace cleanup remains owner-native and revision-fenced through Host/Runtime; this repository does not create a second lifecycle database.

## Sunset

This ratchet is successful when it can disappear.

Delete it after:
1. natural owners enforce the same retention/cleanup invariants;
2. three consecutive lifecycle audits show no material stale-carrier backlog requiring local governance;
3. removing the ratchet does not permit additive Lens/Operator/Registry/Gate state to re-enter through another maintained contract.
