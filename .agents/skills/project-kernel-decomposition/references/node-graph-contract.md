# Project Kernel Decomposition — LEGO Node Graph Contract

This contract turns a project decomposition into a graph that can be reassembled from atomic architectural nodes.

## 1. Node model

A node is an architectural responsibility with an explicit contract. It is not necessarily one process, package, class, or workflow step.

Required fields:

```text
NodeId
Label
Kind
DecompositionState = COMPOSITE | ATOMIC
ResponsibilitySentence
Authority
OwnsDurableTruth = yes | no | delegated
OwnsExternalEffect = yes | no | delegated
Inputs[]
Outputs[]
StateObjects[]
Dependencies[]
Substrates[]
ReplacementContract
FailureModes[]
Invariants[]
Evidence[]
AcceptanceTests[]
```

### Node kinds

Use the smallest useful vocabulary:

- `SOURCE_TRIGGER` — introduces work/events into the graph.
- `TRANSFORM` — pure or mostly pure data/state transformation.
- `DECISION_ROUTER` — selects path/target without performing the final effect.
- `STATE_AUTHORITY` — owns durable/logical truth.
- `EFFECT_EXECUTOR` — performs physical or external effects.
- `RECONCILER` — compares desired and observed state and drives convergence.
- `ADAPTER_GATEWAY` — translates or governs a protocol/provider boundary.
- `VERIFIER_OBSERVER` — observes evidence or decides semantic acceptance.
- `PROJECTION_SINK` — derives disposable/read-oriented views or terminal outputs.

A node may have secondary traits, but exactly one primary `Kind` should explain its architectural role.

## 2. Port model

Every port should state what crosses it and what does not.

```text
Port {
  name
  direction = IN | OUT
  payload_or_contract
  identity_context
  ordering
  replay_semantics
  trust_boundary
}
```

Ports are preferable to vague arrows because they make replacement and testing possible.

## 3. Edge model

Use typed edges. Do not collapse every relationship into `calls`.

- `DATA` — payload/value movement.
- `CONTROL` — scheduling, activation, cancellation, or lifecycle intent.
- `EFFECT` — request/result around an external or physical effect.
- `IDENTITY` — principal, ownership, tenancy, revision, or correlation binding.
- `POLICY` — authorization/governance decision path.
- `OBSERVATION` — read-back of actual state.
- `EVIDENCE` — artifact/receipt/trace used to support a later claim.
- `DEPENDENCY` — required substrate/service availability.

Each edge should identify source port, target port, and whether loss/duplication/reordering matters.

## 4. Atomicity Gate

A node is `ATOMIC` only if all are true:

1. It has one primary responsibility.
2. Its authority boundary is singular and explicit.
3. Its ports are explicit enough for an alternate implementation.
4. Durable truth, external effects, policy, and semantic verification are not accidentally mixed.
5. It can be tested independently through observable behavior.
6. Replacing it does not require rewriting unrelated neighboring nodes.
7. Any remaining internal pieces are implementation details, not independently meaningful architecture.

Otherwise keep it `COMPOSITE` and split again.

### Common forced splits

Split when one component does two or more of:

```text
stores authoritative state
chooses policy
executes external effects
reconciles desired/observed state
judges semantic success
projects UI/read models
```

This usually indicates multiple architectural nodes hidden in one module.

## 5. Composition patterns

These patterns are reusable LEGO assemblies:

### Pipeline
`A -> B -> C`

Use for ordered transforms or effect stages.

### Fan-out / fan-in
`A -> {B,C,D} -> E`

Use for parallel independent work with explicit aggregation semantics.

### Policy gate
`request -> policy -> allow/deny -> effect`

Policy is not the effect executor.

### Registry resolve
`consumer -> registry -> immutable revision/target -> adapter`

Discovery is not authorization.

### Desired/observed reconciliation
`desired authority -> reconciler -> executor -> observation -> reconciler`

Do not report desired state as observed success.

### Durable work + ephemeral wake-up
`durable record -> notifier/queue -> worker -> durable update`

The notification transport is not the source of truth.

### Verification spine
`effect evidence -> verifier -> semantic state authority`

Process exit or provider response is evidence, not automatically domain success.

### Projection
`authoritative events/state -> projector -> board/index/UI`

Projection must be rebuildable.

## 6. n8n lesson retained

n8n demonstrates that complex systems become tractable when a workflow is represented as explicit nodes plus connections, with node-local configuration, retry/error handling, and extensible custom/community nodes.

Transfer the composability, not the assumption that every node is an executable action.

## 7. DeepSeek Harness lesson retained

DeepSeek Harness demonstrates a complementary architecture: plugins provide typed services on a shared context, consumers declare dependencies, and providers can be swapped while the consumer-facing contract remains stable. Optional workflow orchestration lives behind a service seam rather than becoming privileged core machinery.

Transfer the seam/provider discipline into `ReplacementContract` and `DEPENDENCY` edges.

## 8. Graph completion criteria

A graph is complete only when:

- every kernel responsibility is represented by one owning node;
- every node is either `ATOMIC` or has documented children;
- every cross-node interaction is a typed edge;
- every durable truth has exactly one authoritative owner;
- every external effect has an executor and an evidence/observation path;
- every replaceable dependency has a contract boundary;
- a topological/build-order view can be generated for the minimal clone;
- the leaf set plus edge contracts is sufficient to implement a clean-room vertical slice.

## 9. Recommended table

| node | kind | atomic? | responsibility | authority | in ports | out ports | replaceable by | acceptance |
|---|---|---|---|---|---|---|---|---|

## 10. Acceptance markers

Add these to a decomposition report when node mode is used:

```text
NODE-GRAPH COVERAGE: PASS|FAIL
ATOMICITY GATE: PASS|FAIL
EDGE-TYPING: PASS|FAIL
REASSEMBLY SUFFICIENCY: PASS|FAIL
```
