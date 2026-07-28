# M3.0 plan — cross-stack architecture correction

Status: implemented historical plan
Design: [`M30-DESIGN.md`](M30-DESIGN.md)
Tracking: Issue #24
Parent milestone: Issue #5 completed by M3

## 1. Purpose

M3.0 does not implement multi-Agent gameplay. It replaces the first M3 implementation plan with a cross-stack entry contract that reuses the proven Ordivon Host, Computing, and Runtime boundaries.

M3.0 exists because the first M3 plan would otherwise:

- preserve a single-actor time model while adding three Agents;
- duplicate Host Event, projection, lease, graph, and Context mechanisms inside Game;
- create overlapping Goal and Task dependency graphs;
- expose hidden World truth through global strategy annotations;
- use an authority ladder where an attribute-based policy is required;
- add a general conflict-graph algorithm for only three actors.

No source implementation was part of M3.0 itself. Its corrected sequence was later implemented as:

```text
PR #26  Ruleset v3 atomic Team Tick
PR #27  Host-conformant Team state, knowledge, Messages, and ABAC
PR #28  Proposal → Team Effect → Dispatch → Observation loop
PR #29  Team APIs, Web controls, and real Provider adapters
final PR  alternative plans, communication outcome, live evaluation, and receipt
```

The implementation chose the embedded TypeScript option and retained zero runtime dependencies. See [`M3-RECEIPT.md`](M3-RECEIPT.md).

## 2. Design deliverables

M3.0 is complete only when the repository contains:

1. an exact stack-ownership matrix for Computing, Host, Runtime, Game, and UI;
2. a corrected multi-Agent time model using one atomic multi-Intent TickBatch;
3. a Host integration contract using Event streams, checked projections, Task leases, revision CAS, graph-shaped Task state, and token-budget Context Blocks;
4. one Game Objective Graph rather than separate Goal and Task DAGs;
5. an Actor Knowledge boundary that prevents hidden World truth from entering private Context;
6. typed Message semantics separated from Tasks and Artifacts;
7. minimal attribute-based authority and exact single-use Grants;
8. a bounded proposal-selection rule based on exhaustive subsets for three actors;
9. one semantic Team Tick Effect mapped to one Game TickBatch Dispatch and one TickEvent Observation;
10. an explicit deployment choice between an embedded conformance-backed adapter and a local Host sidecar;
11. a revised implementation sequence and acceptance gates;
12. a record that the original M3 design and plan are superseded historical documents.

## 3. Cross-stack promotion rules

### 3.1 Use existing Host mechanisms

The implementation must consume or conform to `ordivon-host` semantics for:

- Task identity and state;
- Host Event streams;
- complete event-bound Task projections;
- stream revision compare-and-swap;
- short Task leases;
- immutable content-addressed objects;
- graph-shaped Task nodes and Ready Frontier;
- token-budget Context Blocks and manifests;
- persistent Context and Decision admission;
- external Provider invocation outside the lease.

A Game-private substitute is acceptable only as a temporary conformance-backed adapter with an explicit extraction boundary.

### 3.2 Keep Game semantics local

The following remain Game-owned:

- Room, actor health, inventory, systems, hazards, resources, and mission state;
- simulation Tick and atomic TickBatch semantics;
- specialist capabilities;
- Objective satisfaction predicates;
- local Observation policy;
- message-channel reachability;
- game conflict predicates;
- score, victory, and replay.

### 3.3 Do not promote unproven generic primitives

M3 must not promote the following into Computing merely because Game uses them once:

- Game Tick;
- specialist role;
- Station radio;
- reactor threat horizon;
- breach-control Objective;
- Game proposal rank.

A semantic object is promoted only after another real domain demonstrates the same invariant.

## 4. Deployment-choice experiment

Implementation may not begin until a small design experiment compares the following forms.

### Option A — Embedded conformance-backed Game adapter

```text
TypeScript Game process
├─ Game World Kernel
├─ Game Team Coordinator workload
└─ promoted Host protocol subset implemented in-process
```

Evidence required:

- exact JSON conformance vectors for Task Event/projection transitions;
- lease/revision behavior equivalent to Host contracts;
- token-budget Context behavior equivalent to Host contracts;
- no new generic Game-only semantics;
- operational simplicity measured against the sidecar option.

### Option B — Local Ordivon Host sidecar

```text
Python Ordivon Host process
├─ Tasks / leases / Context / cognition
└─ narrow local Game World adapter
```

Evidence required:

- process startup and recovery contract;
- local protocol identity and versioning;
- failure behavior when Host or Game restarts independently;
- latency and operational cost per Tick;
- packaging and clean-checkout usability.

### Selection rule

Choose the smallest deployment that preserves semantic ownership and the current local-product friction budget.

The default hypothesis is Option A for the first executable M3 slice. Option B wins only if the experiment demonstrates lower total complexity or a required independent-Host capability.

## 5. Corrected implementation sequence after M3.0

The first M3 seven-PR plan is superseded. The corrected sequence is six implementation PRs after the deployment-choice experiment.

## PR1 — Ruleset v3 atomic multi-Actor Tick

### Scope

- register Scenario v2 and Ruleset v3;
- add Engineer, Medic, and Security World actors;
- add specialist-exclusive primitive Commands;
- admit at most one primitive Intent per actor in one TickBatch;
- evaluate all Intent preconditions against one before-state;
- reserve shared resources across the batch;
- reject stale or conflicting batches atomically;
- combine compatible effects deterministically;
- advance environment once and mission once;
- emit one TickEvent with per-Intent receipts and verification;
- preserve Ruleset v1/v2 and all frozen receipts.

### Acceptance

- two or three non-conflicting actor Intents can succeed in one Tick;
- environment advances exactly once;
- actor-order permutation produces the same TickEvent and digest;
- conflict or insufficient shared resource rejects the complete batch without mutation;
- batch retry with the same identity is idempotent;
- old Runs replay byte-for-byte under their bound Ruleset.

## PR2 — Host-conformant Actor Tasks and Objective Graph

### Scope

- implement the selected embedded/sidecar integration form;
- create one shared Mission Goal Artifact;
- create one Host Task per specialist and one small Team Coordinator Task;
- add one Game Objective Graph with AND/OR predicates;
- represent actor work as Objective claim/attempt references, not another dependency DAG;
- use Host Event/projection/lease/revision semantics;
- derive dynamic actor availability from World State;
- preserve the single-Agent M2 facade for old Runs.

### Acceptance

- a fresh process rebuilds every Task from event-bound projection state;
- projection drift or missing referenced object fails closed;
- two writers cannot advance the same Actor Task revision;
- different Actor Tasks can prepare cognition independently;
- no new primary team-state tables bypass Host Event authority;
- Objective visibility does not reveal undiscovered World facts.

## PR3 — Actor Knowledge, Message delivery, and ABAC

### Scope

- define actor-local Observation policies;
- derive Actor Knowledge from public alarms, local observations, delivered Messages, and visible verified Facts;
- compile token-budget Context Blocks through Host semantics;
- add typed local and radio Message envelopes;
- persist delivery, wait, expiry, and evidence references as Host events;
- implement minimal ABAC using subject, action, target, environment, and player policy;
- bind single-use Grants to exact Proposal, Context, World, policy revision, and expiry;
- keep numeric message/token limits as measured scenario policy.

### Acceptance

- three actors receive materially different Contexts at one World revision;
- hidden World truth cannot enter a Context through Tasks, candidate summaries, or ranks;
- local and radio delivery differ under World reachability;
- expired or undelivered Messages are absent from current Context;
- capability and authority failures remain distinguishable;
- stale or consumed Grants cannot authorize a TickPlan;
- unrelated Actor Tasks continue while one waits for a Message or player decision.

## PR4 — Action Proposals and Team Tick Effect

### Scope

- retain exact Action Proposals outside Provider Sessions;
- invoke eligible actor Providers concurrently outside Task leases;
- allow bounded collection without a global all-provider barrier;
- compile typed Resource Claims and conflict predicates;
- enumerate at most eight subsets for three proposals;
- select one legal subset using public deterministic control criteria;
- create one semantic Team Tick Effect from the selected proposals;
- bind the Effect to one TickBatch Dispatch;
- map TickEvent per-Intent receipts back to Actor Tasks;
- preserve Effect/Dispatch/Observation/Verification identity and recovery.

### Acceptance

- one slow or failed Provider does not erase returned proposals from other actors;
- invented actor, action, target, Grant, or Message identity is rejected;
- selected subset is deterministic under proposal input permutation;
- omniscient M2.1 strategic score is not used as the team arbiter;
- one uncertain TickBatch Dispatch reconciles before any replacement batch;
- actor Tasks independently observe success, rejection, supersession, or wait.

## PR5 — Team control API and interruption recovery

### Scope

- add `GET /api/team/state`;
- add `POST /api/team/step`;
- add `POST /api/team/run`;
- add typed `POST /api/team/input`;
- expose actors, Objectives, visible Knowledge, Messages, authority requests, proposals, waits, TickPlan, TickEvent, and evidence references;
- add interruption faults across Context, Provider, Proposal, Grant, TickPlan, Dispatch, World commit, Observation, and Task advancement;
- keep execution synchronous and bounded;
- preserve existing M2 APIs for compatibility.

### Acceptance

- fresh process recovers every interruption boundary;
- no Provider call is repeated after a valid Decision is retained;
- no duplicate World Tick occurs after response loss;
- one actor can continue while another waits, fails, or is incapacitated;
- the four API operations are sufficient for engineering control;
- M4 can consume Team State without reading raw database tables.

## PR6 — Evaluation, receipt, and Issue #5 completion

### Scope

- deterministic all-Fixture Team baseline;
- Engineer-seal and Security-containment alternative victories;
- connected/disconnected communication comparison;
- permit/require-human/deny authority comparison;
- one-specialist incapacitation;
- Provider timeout/no-proposal behavior;
- all-Codex and mixed Codex/Hermes runs;
- mid-run Provider replacement;
- repeated live-run distributions rather than single anecdotes;
- exact World and Host evidence receipts;
- clean merged-main acceptance.

### Acceptance

- at least two different valid plans reach verified victory on the same seed;
- at least two compatible actor Intents execute in one Tick in the evidence trace;
- communication limits and authority policy materially change coordination or outcome;
- one specialist progresses while another waits or fails;
- World replay and Host event/projection validation succeed after every run;
- live reports include success rate, variance, latency, tokens, reported cost, waits, messages, approvals, and failure clusters;
- no hidden manager model or Fixture override changes valid live Decisions.

## 6. Design-only gates

Before merging M3.0 documentation:

- no file under `src/`, `test/`, `scripts/`, or `web/` changes;
- current 100 tests and coverage gates remain unchanged;
- `pnpm check`, current receipts, and current measurement continue to pass;
- Issue #5 remained open until the subsequent M3 implementation and evaluation merged;
- old M3 documents are retained but clearly marked superseded;
- all new stack claims bind exact inspected repository revisions;
- mature external references are primary-source documentation;
- no framework or new runtime dependency is selected.

## 7. Implementation prohibition

The following work is explicitly deferred until M3.0 design is merged and the deployment-choice experiment is reviewed:

- adding specialist actors;
- modifying Tick reducers;
- creating M3 database tables;
- introducing a Host sidecar;
- adding Team APIs;
- writing live Provider evaluation;
- changing the existing 16 KiB M2 compatibility contract;
- closing Issue #5.

## 8. M3.0 completion statement

M3.0 closes only the architecture question:

```text
How should multi-Agent Station Zero consume the Ordivon stack
without duplicating Host semantics or preserving single-Agent time?
```

It does not close the product milestone:

```text
Can three persistent specialists communicate, request authority,
act concurrently in one deterministic Tick, recover, and win?
```

That remains the responsibility of M3 implementation and Issue #5.
