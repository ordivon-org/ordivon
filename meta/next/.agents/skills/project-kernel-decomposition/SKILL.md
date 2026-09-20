---
name: project-kernel-decomposition
description: Decompose a mature software project, framework, platform, protocol, or repository until its transferable architectural kernel can be rebuilt from scratch. Use when asked to deeply study a project, explain what it really does in one sentence, separate product shell from core mechanisms, map modules and flows, compare with mature substitutes, or produce a minimal working clone/prototype specification. Prefer authoritative/current sources and source code over marketing summaries; preserve evidence and mark hypotheses explicitly.
compatibility: Works for public projects studied from source/docs and local repositories studied through filesystem/git/runtime tools. Web access materially improves current product/platform studies.
license: MIT
---

# Project Kernel Decomposition

The goal is not to summarize a project. The goal is to reduce it to a set of mechanisms and contracts that are sufficient to reconstruct the smallest faithful kernel without copying the product shell.

## Output invariant

A completed decomposition must let another engineer answer all of these without reopening the original project:

1. What does the project do, in one sentence?
2. What is its real kernel rather than its product/UI/integration shell?
3. Which modules own which responsibilities?
4. What are the key state objects, identities, protocols, and transitions?
5. What is the control flow and data/effect flow?
6. What failure/durability/security boundaries matter?
7. Which pieces are mature external substrates rather than project-native inventions?
8. What should be retained, substituted, or rejected locally?
9. What is the smallest clone that proves the kernel?
10. What observable tests prove that clone is semantically faithful?

If the decomposition cannot specify a minimal clone and its acceptance tests, it is not finished.

## Evidence hierarchy

Prefer evidence in this order when available:

```text
current source code / executable behavior
    > current official specification or documentation
    > release notes / maintainer design docs
    > official examples and tests
    > independent technical analysis
    > marketing copy / community summaries
```

Record retrieval/version/date for fast-moving platforms. Separate verified mechanism facts from architectural interpretation and hypotheses. Never promote an inference into a source-backed fact merely because it is plausible.

## Phase 0 — Freeze the subject

Record:

- exact project/product name;
- upstream repository and commit/tag when source is available;
- official docs/spec version and retrieval date for services;
- study scope and excluded surfaces;
- whether the target is open-source code, managed service, protocol, or mixed product.

For managed services, treat the documented public contracts as the observable implementation boundary; do not pretend private internals are known.

## Phase 1 — One-sentence model

Write exactly one sentence that states the durable architectural value, not the feature list.

Good form:

> `PROJECT is a <core abstraction> that <central mechanism> so <system-level outcome>.`

Then add a falsification sentence:

> `It is not primarily <common misleading framing>.`

If this cannot be written clearly, continue investigation before decomposing modules.

## Phase 2 — Shell vs kernel vs substrate

Partition the system into three classes:

```text
PRODUCT SHELL
UI, onboarding, billing, hosted convenience, branding, marketplace, adapters

TRANSFERABLE KERNEL
state machines, registries, schedulers, reconciliation, protocol contracts,
identity boundaries, persistence semantics, execution loops, routing rules

MATURE SUBSTRATES
Kubernetes, Postgres, Redis, OAuth/IAM, OTel, MCP, A2A, queues,
object stores, policy engines, workflow engines, etc.
```

Do not reimplement a mature substrate merely because the target product bundles it.

## Phase 3 — Responsibility decomposition

Create a responsibility table. Every meaningful module must have one primary owner and explicit inputs/outputs.

Minimum columns:

```text
module | responsibility | owns durable truth? | inputs | outputs | dependencies | replaceability
```

Look for hidden mixed authorities: a component that simultaneously decides policy, executes effects, stores truth, and judges semantic completion is usually several modules disguised as one.

### Phase 3A — LEGO / puzzle node graph

Convert the responsibility map into a typed architecture graph. Borrow the composability of n8n nodes and connections, but do **not** assume every architectural node is an executable workflow step. Borrow the provider/service-seam discipline of plugin architectures such as DeepSeek Harness: consumers depend on a stable contract while the implementation behind a seam may be replaced.

Use `references/node-graph-contract.md` for the canonical node and edge vocabulary.

Every candidate node must declare at least:

```text
id
kind
one-sentence responsibility
authority / truth ownership
input ports
output ports
state or effect boundary
dependencies / substrates
replacement contract
failure modes
acceptance test
```

Recursively split a node until it passes the Atomicity Gate:

1. one primary responsibility;
2. one primary authority or effect boundary;
3. explicit typed ports;
4. independently replaceable behind a contract, or explicitly intrinsic;
5. independently testable through observable behavior;
6. no hidden child that owns materially different durable truth, policy, execution, or semantic verification.

If a node fails any item, it remains `COMPOSITE` and must be decomposed again. A leaf may be marked `ATOMIC` only when further splitting would describe implementation detail rather than a distinct architectural responsibility.

The target form is:

```text
PROJECT
  -> SUBSYSTEMS
      -> COMPOSITE NODES
          -> ATOMIC KERNEL NODES
              -> typed edges
```

A completed graph should be sufficient to reassemble the system from the leaf nodes plus their contracts.

## Phase 4 — State and identity algebra

List the smallest persistent/logical objects needed to explain the system.

For each object specify:

```text
identity
lifecycle states
creator/owner
mutable fields
persistence boundary
version/revision semantics
relationships to other objects
```

Typical examples include AgentDefinition, Deployment, Revision, Session, Run, Task, Thread, Checkpoint, RegistryRecord, ToolBinding, Identity, Policy, Artifact, Event.

Do not use one identifier as a universal identity if the source system distinguishes scopes.

## Phase 5 — Control flow and effect flow

Draw at least one end-to-end path from request to observable effect.

Distinguish:

```text
desired/control state
execution state
external effect
observed/read-back state
semantic/domain completion
```

For distributed systems, explicitly identify queues, workers, reconcilers, checkpoints, retries, cancellation, streaming, and ambiguous-effect handling.

## Phase 6 — Protocol and boundary extraction

Extract the smallest stable interfaces between modules. Prefer protocol-neutral contracts before provider-specific APIs.

For each boundary define:

```text
request shape
response/event shape
identity/auth context
idempotency/replay semantics
failure modes
versioning
observability hooks
```

Map standard protocols such as HTTP, MCP, A2A, OAuth, OTel, OCI, or Kubernetes APIs rather than inventing local equivalents.

## Phase 7 — Failure, security, and durability model

For each important path ask:

- What can fail before acceptance, after acceptance, during execution, and after an external effect?
- What is persisted before retry?
- What can be replayed safely?
- Which credentials/identity does code run as?
- Where is policy decided and where is it enforced?
- What is isolated per user/session/agent/run?
- What evidence distinguishes `requested`, `accepted`, `executed`, and `verified`?

Never treat `durable`, `secure`, or `isolated` as binary labels without naming the actual boundary.

## Phase 8 — Reconstruct the minimal kernel

Reduce the project until removing any remaining component breaks a core invariant.

Write:

```text
Minimal Kernel
├── object/data model
├── interfaces
├── control loop(s)
├── persistence
├── execution adapter
└── verification/observability
```

Then provide a build order. A good build order yields a runnable vertical slice early and adds mechanisms one at a time.

## Phase 9 — Minimal clone acceptance

A clone is accepted only through behavior, not diagram similarity.

Specify tests such as:

- create/register an object and resolve it deterministically;
- submit work and observe lifecycle transitions;
- crash/restart and recover committed state;
- cancel/retry without corrupting identity;
- enforce one denied and one allowed capability;
- route one standard-protocol request end-to-end;
- show trace/evidence linking request -> execution -> result;
- replace one adapter without rewriting the kernel.

Use the smallest test set that proves the extracted mechanisms.

## Phase 10 — Local adoption decision

Classify each extracted mechanism:

```text
ADOPT        use the upstream/provider directly
ADAPT        keep a thin local binding/adapter
EXTRACT      implement the small transferable kernel locally
ON_DEMAND    retain only when a workload needs it
REJECT       attractive but overlapping/wrong-authority machinery
```

End with both:

- **What the local system should retain**
- **What it should not copy**

Do not end with a vague recommendation to "use best practices."

## Required final structure

Use `references/decomposition-contract.md` as the default report skeleton. The final acceptance section must include:

```text
ONE-SENTENCE TEST: PASS|FAIL
MODULE-COMPLETENESS TEST: PASS|FAIL
MINIMAL-CLONE SPEC TEST: PASS|FAIL
BEHAVIORAL-ACCEPTANCE TEST: PASS|FAIL
```

`PASS` means the decomposition is sufficient to begin implementing the minimal kernel without reopening broad project discovery. It does not mean the production product has been cloned.
