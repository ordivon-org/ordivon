# Cognitive Circuit R1 — Task-local Composition Contract

Date: 2026-09-22
Status: **R1 CANDIDATE / NOT A DEPLOYED CONTROL PLANE**

## Decision

Ordivon needs one explicit representation between a scoped Goal and the already-existing
execution/verification owners. R1 introduces the smallest residual:

```text
already-scoped objective
        +
already-selected methods
        +
already-resolved capabilities / owners
        +
owner-scoped stages and typed ports
        +
cross-owner composition obligations
        ↓
Task-local Cognitive Circuit Manifest
        ↓
mechanical compiler
        ↓
deterministic non-authoritative projection
        ↓
existing natural owners
```

This closes a representation gap. It does **not** add an Agent Service, workflow engine,
planner, scheduler, Task database, capability registry, retry controller, semantic verifier,
or domain verdict owner.

## Why the owner is Ordivon Next rather than Harness

`meta/next` already owns task-local mappings from problems to mature methods, capabilities,
providers, evidence and validators. Harness begins at one exact caller-authored
`HarnessRunContract` and deliberately does not own cross-Run strategy selection or generic
capability discovery.

Therefore:

```text
Ordivon Next R1
  owns: task-local composition description + mechanical binding checks

Harness
  owns: one bounded durable Agent Run once exact execution authority is supplied

Gateway
  owns: non-authoritative capability-to-natural-owner routing

Runtime
  owns: physical Workspace / Job / Attempt / Artifact truth

Host / Domain / External Owner
  own: their semantic continuity, domain state and verdicts
```

## R1 source language

The manifest is intentionally small:

- exact Objective reference and digest;
- exact advisory Method/Skill bindings;
- already-resolved Capability bindings and their truth boundaries;
- owner-scoped Stages;
- typed input/output Edges;
- cross-owner composition Gate requirements;
- unresolved assumptions;
- explicit non-claims.

The compiler does not choose any of these values. The caller/Agent/domain supplies them.

## Mechanical compiler

`uv run ordivon-circuit compile` validates:

1. JSON Schema shape;
2. unique node/binding identities;
3. stage dependency acyclicity;
4. exact Method/Capability references;
5. typed edge endpoint existence;
6. edge/dependency consistency;
7. cross-owner gate stage bindings.

It then emits a deterministic projection containing:

- exact manifest digest;
- deterministic topological stage order;
- selected Method and Capability binding IDs;
- required gate IDs;
- unresolved assumptions;
- an explicit non-authority boundary.

The output is disposable/rebuildable. It is not a workflow or execution record.

## Cross-owner composition gates

A Gate requirement records one bounded assume/guarantee seam:

```text
producer stage guarantee
        ↓
verifier-owned evidence
        ↓
consumer stage assumption
```

A `composition-gate-result-v1` record is owned by the named verifier and may be:

- `SATISFIED`;
- `UNSATISFIED`;
- `UNKNOWN`.

`SATISFIED` or `UNSATISFIED` requires evidence references. `UNKNOWN` may remain
evidence-empty.

The gate evaluator binds every result to the exact manifest digest and verifier owner.
Required gates close mechanically only when every required result is `SATISFIED` and the
manifest has no unresolved assumptions.

Even then:

```text
mechanicalClosure = true
domainAcceptanceEstablished = false
```

This is deliberate. Local composition evidence never upgrades itself into scientific,
business, safety, publication, product or other domain success.

## Interface Contract relation

R1 consumes existing interface contracts rather than copying them. A Capability binding
records only the resolved owner and truth boundary needed by this task-local circuit. Stable
owner contracts remain with Gateway/Runtime/Host/domain owners.

A later R2 may bind explicit producer/consumer interface-version observations when a real
contract-currentness failure needs machine handling. R1 does not create a second capability
catalog merely to cache owner surfaces.

## Cognitive Circuit Compilation relation

R1 implements only the mechanical half:

```text
semantic choice by Agent/domain
        ↓
manifest authoring
        ↓
R1 bind / validate / lower
```

It explicitly does **not** implement:

```text
Goal
  ↓
automatic method ranking
  ↓
automatic capability discovery
  ↓
automatic strategy selection
```

Those remain Agent/domain/external-owner decisions until repeated evidence justifies a
separate bounded mechanism.

## Anti-growth laws

R1 must fail architectural review if it grows any of these:

- persistent Circuit database;
- universal workflow state;
- global Task truth;
- capability registry;
- automatic permission grants;
- credential storage;
- generic retry policy;
- semantic completion authority;
- universal domain result/status vocabulary;
- hidden method/capability ranker;
- mandatory execution engine.

## R1 acceptance

R1 is accepted only when:

1. valid cross-owner circuit compiles deterministically;
2. unknown references, cycles, invalid ports and owner-collapsed gates fail closed;
3. stale gate results fail by exact manifest digest;
4. missing/UNKNOWN/UNSATISFIED gates cannot produce mechanical closure;
5. SATISFIED gates can close the composition while domain acceptance remains false;
6. repository validation stays green without adding a new runtime dependency.

The next implementation pressure should come from one real task-local consumer, not from
adding generic features by anticipation.


## Verification Obligation R1 relation

The later Verification Obligation R1 layer now lowers existing R1 Composition Gates without
changing their truth semantics:

```text
Cognitive Circuit Gate requirement
        |
        v
Verification Obligation projection
        +
exact caller-authored verifier binding
        |
        v
natural verifier owner/provider
        |
        v
existing composition-gate-result
        |
        v
R1 gate evaluator
```

The obligation compiler is one-to-one over already-authored Gates; it does not invent
properties. Binding resolution validates exact obligation/verifier identity and support scope
but does not discover, rank, install, probe, or execute verifiers.

Therefore these standings remain distinct:

```text
VERIFIER_BINDINGS_RESOLVED
    != verifier executed
    != gate SATISFIED
    != mechanicalClosure
    != domainAcceptanceEstablished
```

Owner-native R3 verifiers and the Pacti 0.3.1 timeout-contract shadow have both exercised this
thin waist. Formal/native specifications remain with their natural owners and are referenced
by exact digest; Composition does not interpret TLA+, Rego, Pacti, Lean, test, or domain
languages.
