# Ordivon Convergence & Publication Fabric R2

Status: **IMPLEMENTATION CONTRACT / PARTIALLY REALIZED**
Date: 2026-09-28
Spec ID: `ORDIVON-CONVERGENCE-PUBLICATION-R2`

## 1. Purpose

R2 governs the transition from many parallel Agent Workspaces into one canonical published source history. It replaces "merge bot" thinking with explicit source, impact, verification, publication, evidence, and currentness contracts.

The retained kernel is:

```text
Candidate
+ Currentness
+ Ownership
+ Impact
+ Verification
+ Publication
+ Evidence
```

Provider mechanisms remain replaceable. Authority boundaries do not.

## 2. Constitutional invariants

1. **One canonical publication authority.** GitHub protected `main` is the current provider publication authority. A local ref MUST NOT independently claim the same role.
2. **Total path classification.** Every publication-relevant tracked path MUST resolve to an owner source or one explicit non-owner class. Unknown paths fail closed.
3. **Immutable verification subject.** Verification evidence binds an exact revision/tree or provider synthetic future tree.
4. **Projection is not authority.** Owner/impact plans are repository projections, not domain or provider truth.
5. **Evidence is not authority.** CI receipts, Episodes, and telemetry cannot authorize publication by themselves.
6. **Effect intent is not effect occurrence.** Provider writes require readback/reconciliation.
7. **Optimize only after soundness.** R1 conservative dependency closure remains the fallback until typed directed propagation proves a smaller sound graph.
8. **Provider owns provider mechanics.** Ordivon does not build a shadow Merge Queue or queue database while GitHub supplies the required mechanism.
9. **Pressure before control.** Adaptive scheduling, batching, speculative-window control, and predictive scheduling remain evidence-gated.
10. **Historical evidence survives replacement.** R1 acceptance and telemetry remain evidence, not current architecture authority.

## 3. Source planes

R2 distinguishes three states that MUST NOT be collapsed into one field named `main`:

```text
Workspace State
    isolated Agent physical source

Integration Frontier
    local high-throughput composition state
    NOT publication truth

Publication State
    provider protected main
    canonical source truth
```

The target topology is:

```text
Agent Workspaces
      -> immutable Candidate Envelopes
      -> local Integration Frontier
      -> provider-current Impact Plan
      -> Verification DAG
      -> GitHub PR
      -> GitHub Merge Queue / merge_group
      -> exact future-tree qualification
      -> GitHub main
      -> readback evidence
```

## 4. R2 LEGO

| ID | LEGO | Natural authority | R2 standing |
|---|---|---|---|
| C01 | Canonical Source Authority | GitHub/source provider | required |
| C02 | Local Integration Frontier | Git mechanics | required |
| C03 | Candidate Envelope | Runtime + Git | required |
| C04 | Publication Adapter | provider adapter | required |
| C05 | Provider Governance Contract | GitHub + repo policy | required |
| C06 | Ownership Resolver | repository mechanics | implementing |
| C07 | Typed Dependency Graph | repository contracts | planned |
| C08 | Change Classifier | repository mechanics | planned |
| C09 | Impact Compiler | repository mechanics | planned |
| C10 | Verification Plan DAG | repository mechanics | planned |
| C11 | Verification Executor | CI / Runtime | planned |
| C12 | Verification Result Cache | evidence substrate | deferred until identity proof |
| C13 | Failure Classifier | verification/evidence layer | planned |
| C14 | Structured Evidence Fabric | CI / Runtime / provider observations | planned |
| C15 | Queue Pressure Controller | provider/future controller | NOT ADMITTED by default |

## 5. C06 ownership contract

Current R2 foundation uses two disjoint mechanisms:

- `tools/repo/owners.toml`: paths that have a first-class mechanical verification owner.
- `tools/repo/path_classes.toml`: paths intentionally outside an owner root, classified as repository mechanics, documentation, generated evidence, or archived source.

Resolution is total over tracked current source. `UNKNOWN` is an error, not `owners=[]`.

A path-class result with no owner does **not** claim semantic irrelevance. It states only why the path is not an owner source. Cross-cutting publication impact remains separately controlled by convergence policy.

## 6. Verification migration

R1 verification remains the safety oracle while R2 evolves:

```text
R1: changed paths -> direct owner -> conservative undirected seam closure
```

R2 will shadow it with:

```text
changed paths
 -> total ownership
 -> change class
 -> typed directed seams
 -> interface fingerprints
 -> minimum sound affected graph
 -> Verification DAG
```

R2 MUST fall back to the R1 conservative graph for unknown change/edge semantics.

## 7. Verification levels

Future profiles are:

- `L0`: Workspace feedback.
- `L1`: publication admission.
- `L2`: exact `merge_group` future-tree landing qualification.
- `L3`: post-publication readback/observation.

L2 is the canonical mechanical landing gate. L3 SHOULD NOT blindly duplicate L2 when exact-tree evidence remains valid.

## 8. Publication effect contract

Provider mutation follows:

```text
intent
 -> provider-current precondition snapshot
 -> effect attempt
 -> committed / not-committed / ambiguous
 -> provider readback
 -> receipt
```

Transport loss is not failure evidence. Reconciliation precedes replay.

## 9. Migration order

1. R2.0 fresh source/provider census and durable spec.
2. R2.1 reconcile local/provider canonical split; establish local Integration Frontier; make local `main` provider mirror.
3. R2.2 make path ownership/classification total and fail closed.
4. R2.3 typed directed dependency graph + interface fingerprints.
5. R2.4 Impact Compiler shadowing R1.
6. R2.5 Verification DAG + bounded parallel executor.
7. R2.6 L0/L1/L2/L3 split.
8. R2.7 failure classification + bounded retry.
9. R2.8 safe content-addressed evidence reuse.
10. R2.9 provider governance hardening and publication robot identity.
11. R2.10 queue optimization only if pressure remains proven.

## 10. Completion gates

R2 is not complete until:

- provider `main` is the sole publication line;
- local `main` is a mirror rather than an independent production frontier;
- local concurrent integration has a separately named frontier;
- owner/path resolution is total;
- typed dependency propagation is live with conservative fallback;
- Verification is represented as a DAG;
- structured receipts and failure classes are available;
- provider governance is live-read against a desired contract;
- provider effects reconcile response loss;
- Agent UX exposes Candidate, Provider Base, Provider Current, Impact, Verification, Queue, and Next admissible transition without collapsing those identities.

## 11. Non-goals until evidence changes

R2 does not authorize a private merge queue, custom queue DB, ML scheduler, retry-until-green loop, arbitrary CI-result reuse, or semantic-acceptance collapse into GitHub checks.
