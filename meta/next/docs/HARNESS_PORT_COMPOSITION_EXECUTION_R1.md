# Harness Port Composition Execution R1

Date: 2026-09-14  
Status: **REGISTERED / EXECUTION PLAN**

## Decision

Ordivon retains **Host, Harness and Runtime** as the three semantic cores. Harness is not replaced by one external agent framework. It becomes a small durable semantic core surrounded by replaceable capability/provider implementations.

The operating pattern is learned from n8n without cloning n8n:

```text
stable execution/authority semantics
        +
replaceable provider descriptions/adapters
        +
composition-time registration
        +
exact per-execution authority snapshot
```

For Harness this means:

```text
Harness Core
  Run identity / Journal / cognition / authority / effect continuity / recovery / completion
        |
        +-- stable ports
        |
        +-- provider implementations selected per composition
```

No OMP/Codex/OpenHands/Claude implementation becomes a new semantic owner.

## The n8n lesson translated precisely

n8n succeeds because a node implementation can change while the engine keeps stable notions of node description, credential binding, workflow execution and execution result. Harness needs the same separation:

| n8n concept | Harness translation |
| --- | --- |
| node description | capability/action descriptor |
| node implementation | provider adapter |
| credential | owner/provider authority binding |
| workflow | bounded ToolProgram / external orchestrator composition |
| workflow execution | Harness Run |
| node result | Tool/Provider observation |
| execution history | Harness Journal |
| subworkflow | Child Harness Run |
| binary/resource object | ResourceRef / Artifact reference |
| external target truth | Runtime / provider / World truth |

The translation stops here. Harness does **not** become a workflow engine, credential database, integration marketplace, scheduler or global event platform.

## Non-negotiable laws

The refactor must preserve:

```text
History != Cognition
Observation != Retention
Installed capability != Run authority != Turn authority
Tool intent != Physical effect
Physical effect != Semantic success
Exact replay != Redispatch
Run terminality != Host/Domain completion
```

No provider port may weaken these inequalities.

## Important negative constraint: no resurrected global Capability Service

Current Harness correctly retired generic capability discovery/ranking/catalog ontologies after they had no independent authority/consumer.

Therefore R1 uses:

```text
composition-time provider registry (ephemeral)
        -> exact selected descriptors/grants
        -> frozen Run authority
        -> exact turn surface
```

The registry is not durable semantic truth, does not rank relevance, and does not decide authority.

Dynamic provider discovery such as MCP updates **availability** only. A new capability becomes turn-visible only when existing Run authority already permits it or a caller-authorized successor Run/binding explicitly admits it.

# Current Harness seams to retain

Current source already has useful boundaries:

- `HarnessRunContract` — immutable Run authority;
- `AgentTurnAdapter` / `AgentTurnRequest` / `AgentTurnResult` — Provider seam;
- `DomainToolBridge` — current Tool execution seam;
- `HarnessRuntimeClient` + `HarnessExecutionBinding` — Runtime seam;
- `WorkingViewProjector` — cognition projection seam;
- `HarnessToolProgram` — bounded deterministic programmatic composition;
- Journal/CAS + Provider/Tool lifecycle — continuity core.

R1 should regularize these seams instead of creating parallel abstractions.

# Target ports

These are logical ports, not a demand to create eight empty framework classes on day one.

## P1 Provider Port

Current donor: `AgentTurnAdapter`.

Stable responsibility:

```text
exact AgentTurnRequest
  -> Provider/model physical interaction
  -> normalized AgentTurnResult / typed failure
```

Must not own Tool authority, WorkingSet selection, Runtime effects or semantic completion.

First implementation remains DeepSeek; later Codex/OpenAI/Claude/etc. prove portability.

## P2 Action / Capability Provider Port

Stable responsibility:

```text
action descriptor + exact request
  -> provider-specific mechanism
  -> structured observation/proposal
```

Used for Edit, LSP, DAP, Browser, Eval, MCP-backed Tools, n8n-backed deterministic automation and similar capabilities.

Do not persist a universal Harness capability database. Provider descriptors are composition inputs.

## P3 Resource Resolver Port

Stable responsibility:

```text
ResourceRef -> bounded content/metadata projection
```

Candidate schemes:

- `workspace://`
- `artifact://`
- `agent://`
- `history://`

Possessing a reference never grants an action.

## P4 Cognition Projection Port

Current donor: `WorkingViewProjector` and turn projection.

Stable responsibility:

```text
canonical history + selected durable cognition + interaction cognition + attempt cognition + control
  -> exact model-visible turn projection
```

OMP compaction, fresh-context handoff or other strategies may be implementations. History/cognition ownership remains Harness.

## P5 Effect Executor Port

Current donors: `DomainToolBridge`, Runtime bridge.

Stable responsibility:

```text
admitted Harness action/effect intent
  -> exact provider/Runtime dispatch
  -> receipt/observation/UNKNOWN/reconciliation
```

Provider transport success never becomes domain success.

## P6 Child Run Port

Stable responsibility:

```text
ChildRunRequest
  -> independently identified Harness Run
  -> ChildYield / evidence refs
```

OMP `task` / Agent Hub are implementation donors. Child work that mutates code may bind a Runtime Workspace.

## P7 Programmatic Composition Port

Current donor: `HarnessToolProgram`.

Keep two complementary bounded forms:

- declarative short Tool dataflow: `HarnessToolProgram`;
- imperative computation/tool composition: Persistent Eval.

Do not add cron, webhooks, distributed workflow state or business process semantics. Route those to n8n/Temporal/Host as appropriate.

## P8 Interceptor Port

Experimental only. Candidate hooks:

- before turn;
- before Provider call;
- Provider stream observation;
- after Provider result;
- before action admission;
- after observation;
- before completion proposal.

TTSR and Advisor are candidate implementations. Interceptors receive no hidden authority.

# Execution sequence

## R0 — Freeze semantic baseline

Goal: prove the refactor starts from a healthy exact current Harness.

Actions:

1. run current portable deterministic suite;
2. record current public API and durable schema inventory;
3. record existing cross-repository consumers of `AgentTurnAdapter`, `DomainToolBridge`, `HarnessRuntimeClient`, `WorkingViewProjector`, `HarnessToolProgram`;
4. classify each public type as semantic core, current port, provider implementation or migration residue;
5. add characterization tests only where a real current seam lacks one.

Exit:

- no production behavior change;
- exact baseline test/evidence recorded;
- migration map names every current seam owner.

## R1 — Formalize existing ports without new capability behavior

Do the smallest extraction possible:

1. retain `AgentTurnAdapter` as Provider Port rather than renaming merely for aesthetics;
2. retain `WorkingViewProjector` as Cognition Projection Port;
3. define one common provider/action descriptor shape only where first external capability needs it;
4. define ResourceRef/resolver only when the first large deferred resource path is wired;
5. keep `HarnessRuntimeClient` as the Runtime-specific Effect Executor adapter;
6. add conformance tests that implementations cannot add turn authority absent from the exact `AgentTurnRequest`/grant.

Exit:

- existing DeepSeek/no-Tool/Runtime behavior byte- or semantically-equivalent where compatibility requires;
- no new global registry or persisted state;
- first stable-port tests pass.

## R2 — First real donor: Adaptive Edit Gateway

Use the OMP-derived Edit ABI as the first proof that the architecture is genuinely replaceable.

Implement:

```text
EditCodec
  anchored/hashline-like
  exact replacement
  conventional patch where useful
        |
        v
CanonicalEditPlan
        |
        v
Runtime workspace.patch / patch.get
```

Why first:

- historical Harness P2/P3 independently exposed malformed unified-diff failures;
- current Runtime already has strong exact Patch/reconciliation semantics;
- OMP supplies mature ACI lessons;
- it tests a provider mechanism without changing Harness Run laws.

Exit:

- same semantic edits benchmarked across at least replacement + anchored + patch;
- stale source and lost-response falsifiers pass;
- no edit codec writes files outside Runtime Patch authority.

## R3 — Programmatic composition upgrade

Keep existing `HarnessToolProgram` as declarative bounded dataflow.

Add Persistent Eval as a sibling implementation:

```text
ProgrammaticComposition
   |- ToolProgram (declarative)
   `- Eval kernel (imperative Python first)
```

All tool re-entry passes through the exact current Harness Tool admission and normal Tool effect lifecycle.

Exit:

- retained Python state across cells;
- denied Tool cannot be called from Eval;
- computation workload demonstrates lower model round trips/context than shell-loop baseline;
- no duplicate Tool authority plane.

## R4 — Resource references

Introduce the smallest Resource Resolver proven by R3/child-output pressure.

Start with existing natural authorities:

```text
workspace:// -> Runtime Workspace read projection
artifact://  -> Runtime/Harness Artifact owner
```

Add `agent://` only when Child Runs land.

Exit:

- large content stays out of model context by default;
- references retain provenance;
- resource possession grants no new action.

## R5 — Child Harness Runs

Translate OMP subagent mechanics onto existing Harness semantics:

```text
parent Run
  -> exact ChildRunRequest + explicit Tool subset
  -> child Harness Run
  -> optional isolated Runtime Workspace
  -> schema-validated ChildYield
```

Add projection/control operations only after child identity is durable:

- list/inspect;
- message/steer;
- cancel;
- wait;
- later park/revive.

Exit:

- response loss cannot duplicate spawn;
- parent restart can reattach;
- child Workspace cannot mutate parent source implicitly;
- typed yield does not require injecting entire child transcript.

## R6 — Live provider availability / MCP

Now introduce an ephemeral live availability registry because a real consumer exists.

Pipeline:

```text
provider discovery/connect
  -> available descriptors
  -> intersect immutable Run admission
  -> derive next-turn surface
```

No dynamic discovery directly modifies Run authority.

Exit:

- late MCP provider can appear without Run restart;
- unauthorized late Tool remains invisible;
- schema revisions have stable identities;
- provider disappearance preserves historical receipts.

## R7 — LSP + DAP standard providers

Adopt protocol clients; do not create Ordivon protocol clones.

LSP mutation path:

```text
LSP WorkspaceEdit
  -> Adaptive Edit Gateway
  -> exact Runtime Patch
```

DAP execution should bind Runtime-owned target processes when practical; otherwise clearly record DAP provider as physical process owner.

Exit: one real code task proves semantic navigation/refactor/debug behavior and downstream tests.

## R8 — Experimental cognition interceptors

Only after the stable ports are proven:

- TTSR-like stream intervention;
- Advisor/watchdog;
- alternative context/compaction strategies.

Every mechanism needs an ablation against baseline. Do not promote merely because OMP implements it.

# Provider package shape

Do not force one language/package format prematurely. The logical package contract should be approximately:

```text
provider identity/version
supported port/action families
input/output schemas
session scope
consequence/effect classification
health/readiness projection
configuration references
natural credential owner
optional resource resolvers
verification/conformance tests
```

Credentials stay with the natural provider where possible, following the n8n rule `capability != credential`.

# Composition API direction

Target composition should become simple enough that an application can say, conceptually:

```python
run = HarnessAgentRun.create(
    contract=contract,
    provider=openai_or_deepseek,
    cognition=working_view_projector,
    actions=[edit, lsp, runtime_tools, n8n],
    resources=[workspace_resources, artifact_resources],
    execution=runtime_effects,
)
```

The exact Python API need not use these names. The law is that composition binds implementations while the `HarnessRunContract` and per-turn request bind authority.

# Routing rules

To avoid duplicating mature systems:

```text
short deterministic Tool dataflow -> HarnessToolProgram
algorithmic in-turn computation -> Persistent Eval
SaaS/API integration workflow -> n8n
long-running durable workflow -> Temporal / mature workflow engine
business/domain work continuity and acceptance -> Host/domain owner
physical machine execution/evidence -> Runtime
uncertain Agent reasoning/action loop -> Harness
```

# Migration safety rules

1. **No big bang.** One port/donor at a time.
2. **No rename-only architecture.** Do not create replacement types unless behavior/consumer pressure proves a separate contract.
3. **Existing seams first.** Normalize `AgentTurnAdapter`, `WorkingViewProjector`, `DomainToolBridge`, `HarnessRuntimeClient` before inventing new abstractions.
4. **No second Store.** Provider/plugin registries are ephemeral unless a real state owner requires persistence.
5. **No second Tool authority.** Eval, subagents, MCP and Skills all consume existing Run/turn authority.
6. **No second Runtime.** Edit/LSP/DAP/browser adapters lower physical work to natural providers/Runtime instead of owning generic execution.
7. **No framework lock-in.** OMP/Codex/OpenHands/Claude/Aider mechanisms enter through ports and remain removable.
8. **A/B or conformance proof before cutover.** Keep old path until replacement passes the same current workload.
9. **Delete obsolete path after proof.** Do not keep two long-lived mechanisms “just in case.”

# First implementation slice

The next concrete engineering slice should be **R0 + R2 preparation**, not all ports at once:

1. freeze current Harness baseline;
2. make a current seam/consumer inventory;
3. define an internal `EditCodec -> CanonicalEditPlan` contract;
4. implement exact-replace codec using the already-proven path;
5. implement anchored/hashline-like codec;
6. lower both to current Runtime Patch;
7. add protocol-selection benchmark fixtures;
8. run stale-source, ambiguity and response-loss falsifiers;
9. only then decide whether the generic Action/Capability Provider descriptor earned promotion into supported API.

This sequence deliberately lets a real donor implementation *earn* the generic port instead of creating an abstract plugin system first.

## Acceptance

R1 architecture passes only if all are true:

- current Harness semantic laws remain unchanged;
- one mature donor mechanism can be replaced without editing the Run state machine;
- provider availability and authority remain distinct;
- Runtime remains physical truth owner;
- Host/domain remains semantic completion owner;
- old implementation can be deleted after equivalent/better verified behavior;
- no new global capability/workflow/credential ontology is introduced.

## Final rule

**Stable semantics at the waist; replaceable mechanisms at the edges.**

Harness should become easier to automate in the same sense that n8n is easy to extend: new implementations register against narrow contracts, while execution authority and state ownership remain stable and explicit.
