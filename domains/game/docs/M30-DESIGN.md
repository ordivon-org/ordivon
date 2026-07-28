# M3.0 design — cross-stack correction before multi-Agent implementation

Status: implemented historical entry contract
Tracking: Issue #24
Parent milestone: Issue #5 completed by M3
Game baseline: `ordivon-game@9b9281c8b15beb61a0173a7eca157e292a4d71f5`
Computing baseline: `ordivon-computing@67360093631bdffd9f9ad00fcae0f3a755ba2245`
Host baseline: `ordivon-host@a536b01c0672e7f74ff5b22829f951e17f58fc3f`
Runtime baseline: `ordivon-runtime@2d4141b30ebabd9119ed4e9547c36759cb5b7b77`

## 1. Purpose

M3.0 is an architecture-correction milestone between the completed single-Agent stack and M3 multi-Agent implementation.

The first M3 design correctly identified independent specialists, limited communication, authority, conflict, waiting, and recovery. A first-principles audit then found that its implementation shape would duplicate already-proven Ordivon Host mechanisms and preserve a single-Agent time model inside a nominally multi-Agent game.

M3.0 therefore freezes the cross-stack boundaries before any specialist, database table, API, or Provider loop is implemented.

The corrected target is:

```text
Ordivon Host semantics
+ Game-specific Team Coordinator workload
+ atomic multi-Actor Game Tick
+ actor-visible knowledge
+ typed communication
+ attribute-based authority
+ exact Effect / Dispatch / Verification continuity
```

M3.0 originally produced design contracts only. The reviewed contracts were subsequently implemented through PRs #26–#29 and the final M3 evaluation PR. The implementation selected the embedded TypeScript form, added no runtime dependency or sidecar, and is evidenced by [`M3-RECEIPT.md`](M3-RECEIPT.md).

### Implementation outcome

```text
embedded Host-conformant Team adapter
+ Scenario v2 / Ruleset v3
+ atomic multi-Actor TickBatch
+ actor-visible Context and typed Messages
+ ABAC and exact Grants
+ bounded legal-subset selection
+ Team Effect / Dispatch / Observation / Verification
```

The document remains the architectural entry contract and design history; it is no longer the current implementation status page.

## 2. First-principles constraints

### P-1 — Reality has one owner

The deterministic Game World owns rooms, actors, systems, hazards, inventories, health, resources, simulation time, and mission outcome. A Provider, Host Task, Message, Proposal, approval, or UI cannot directly change World State.

### P-2 — Continuity has one owner

Ordivon Host owns Goal and Task continuity, Host Event state, checked projections, bounded cognition, candidate admission, leases, Effect preparation, Dispatch correlation, verification receipts, waiting, and task outcomes.

The Game may implement a domain adapter or temporary conformance-backed reference implementation. It must not define a second incompatible Host architecture.

### P-3 — Physical execution keeps its strongest owner

Ordivon Runtime owns trusted-local Workspace, Job, Attempt, process, Artifact, cancellation, and physical recovery truth. In-world deterministic Game actions remain a domain execution plane and do not become Runtime Jobs merely to preserve conceptual symmetry.

### P-4 — Computing owns protocol, not product state

Ordivon Computing owns cross-project semantic definitions, conformance vectors, reference behavior, experiments, and evidence. It does not own live Game Tasks or World State.

### P-5 — Provider output is cognition, not authority

A model returns one structured Action Proposal for one immutable Context. It cannot invent another actor, Task, authority grant, Message delivery, Tick outcome, World object, or completion claim.

### P-6 — Multi-Agent must change time semantics

Three specialists sharing one global action slot are not a concurrent team. One simulation Tick must be able to contain one primitive Intent from each eligible actor while environment and mission evaluation advance once.

### P-7 — Partial observation must be real

An Agent cannot receive hidden World truth through a globally compiled Task, rank, explanation, or candidate annotation. Actor strategy data must derive only from public alarms, local Observation, delivered Messages, and verified Facts visible to that actor.

### P-8 — Use the smallest sufficient structure

M3.0 rejects a new general workflow engine, actor framework, graph runtime, distributed scheduler, policy platform, or A2A server. Each retained abstraction must enforce a concrete invariant required by the three-specialist Game.

## 3. Mature-practice reference model

M3.0 borrows narrow invariants rather than adopting external frameworks.

### 3.1 Durable workflow practice

Temporal demonstrates the value of retaining durable execution history so coordination can resume after process, network, or infrastructure failure. Ordivon already owns this problem through Host Event streams and Runtime recovery, so M3.0 borrows the deterministic-history principle without adding Temporal.

Borrow:

- durable event history;
- deterministic continuation;
- external cognition and physical action outside short state transitions;
- stable identities across process loss.

Reject:

- a Temporal deployment;
- a general workflow language;
- long-lived distributed worker infrastructure.

### 3.2 Selective event sourcing

Microsoft's Event Sourcing guidance treats the event store as the system of record and materialized views as query projections, while warning that event sourcing has substantial schema, concurrency, and operational costs and should be applied selectively.

M3.0 applies event sourcing only to:

- authoritative World history;
- Host Goal/Task/control history.

Static role configuration, display preferences, and ordinary query projections do not automatically become event streams.

### 3.3 Actor identity and turn isolation

Orleans demonstrates stable logical actor identity, asynchronous messages, and turn-based single-threaded execution per actor. M3.0 borrows:

- stable Actor identity independent from process or Provider Session;
- one active cognition turn per actor;
- mailbox-style delivered Messages;
- external blocking Provider calls outside the actor transition lease.

M3.0 does not add Orleans, clusters, grain placement, or distributed activation.

### 3.4 Task, Message, and Artifact separation

A2A distinguishes stateful Tasks, communication Messages, and durable Artifacts. M3.0 keeps the same semantic separation internally:

- Task: durable unit of coordinated work;
- Message: bounded delivery envelope between actors;
- Artifact/Fact: durable evidence or result referenced by Messages and Context.

M3.0 does not implement the A2A wire protocol or Agent Card discovery.

### 3.5 Code orchestration rather than hidden manager cognition

The OpenAI Agents SDK documents both LLM-driven orchestration and code-driven orchestration, noting that code orchestration is more deterministic and predictable in speed, cost, and performance. M3.0 uses code for authority, proposal compatibility, Tick admission, and replay. Specialists retain model autonomy inside their exact candidate frontier; no hidden manager model selects the team plan.

### 3.6 Attribute-based authority

NIST ABAC evaluates subject, object, requested operation, environment conditions, and policy. M3.0 replaces the original one-dimensional authority ladder with a minimal attribute-based decision:

```text
subject attributes
+ action attributes
+ target attributes
+ environment attributes
+ player policy
→ permit | require-human | deny
```

## 4. Current Ordivon capabilities that M3.0 reuses

The first M3 design assumed several mechanisms still needed to be invented in Game. They already exist in the independent Ordivon Host.

### 4.1 Checked Event / Projection protocol

`ordivon-host` already retains:

```text
immutable CAS object
+ Host Event
+ stream head
+ complete resulting TaskProjection
```

in one semantic transition. A fresh Host validates the referenced object and confirms that the materialized projection equals the event head. The projection is a checked cache, not an independent authority.

M3.0 therefore forbids adding a new collection of Game-private team projection tables as the primary truth source.

### 4.2 Revision CAS and Task Lease

`ordivon-host` already provides:

- per-Task stream revision compare-and-swap;
- short active-writer lease;
- lease revision and expiry;
- one transition per lock;
- Provider and Runtime calls outside the lease.

M3.0 maps each specialist cognition Task to this mechanism instead of inventing an Actor lease table in Game.

### 4.3 Task-local frontier and Goal-scoped revision references

The active `ordivon-host` implementation stores one checked `TaskProjection` with a Task-local active node token, Ready Frontier, revision, and state. Historical `task_nodes`, `task_edges`, `wakeups`, and `runtime_links` tables are explicitly legacy-unused and are not the current coordination substrate.

Multi-Actor coordination therefore uses multiple independent Tasks sharing one Goal, plus exact Task revision and head-digest references retained by one ordinary Coordinator Task. Game-specific Objective semantics remain domain Artifacts and predicates; no generic DAG or scheduler is introduced.

### 4.4 Token-budget Context compiler

`ordivon-host` already compiles required and optional typed Context Blocks under a token budget, retaining source digests, freshness classes, priorities, and a manifest of selected and omitted blocks.

M3.0 therefore does not freeze a new global 16 KiB Context limit. Existing M2 compatibility remains unchanged, while M3 actor Contexts use token-budgeted Host Context Blocks and measured byte ceilings.

### 4.5 Effect / Dispatch / Observation / Verification boundary

Ordivon Computing and Runtime already separate stable semantic Effect identity from concrete Dispatch attempts and execution evidence. M3.0 preserves that chain and defines only the Game-specific binding from an admitted Team Tick Effect to a deterministic TickBatch.

## 5. Stack ownership after M3.0

| Concern | Computing | Host | Runtime | Game | Workbench/Web |
|---|---|---|---|---|---|
| Semantic IDs, Effect/Dispatch state algebra, conformance | owns | consumes | consumes | consumes | consumes |
| Goal, Task, Task Event, checked projection, lease | defines candidates/references | owns | does not own | domain adapter | reads/commands |
| Context blocks, Provider turn, Decision admission | reference contract | owns | does not own | supplies actor-visible blocks/candidates | does not own |
| Workspace, Job, process Attempt, physical Artifact | references | correlates | owns | not used for primitive World actions | observes |
| Room, health, inventory, hazards, resources | does not own | references | does not own | owns | projects |
| Objective predicates and specialist capabilities | may study | hosts references | does not own | owns | displays/configures |
| Message envelope and delivery state | protocol candidate | owns durable delivery state | does not own | supplies channel reachability | sends/displays |
| Authority decision and Grant lifecycle | protocol candidate | owns decision/Grant history | enforces only Runtime-specific grants | supplies subject/action/target/environment attributes | player decision surface |
| TickPlan / TickBatch / TickEvent | sees Effect contract | prepares/correlates | does not own | owns | projects |
| Mission score and victory | does not own | records outcome | does not own | owns | displays |

## 6. Corrected M3 architecture

```text
Player policy / input
        │
        ▼
Ordivon Host
├─ shared Mission Goal identity
├─ one durable Actor Task per specialist
├─ one short Team Coordinator Task
├─ Task Event streams and checked projections
├─ Task leases and revision CAS
├─ actor-visible Context Blocks
├─ typed Messages and Authority Grants
└─ Action Proposals
        │
        ▼
Game Team Coordinator workload
├─ derive current visible candidate frontiers
├─ admit exact actor Proposals
├─ evaluate authority
├─ choose a compatible proposal subset
├─ construct one Team Tick Effect
└─ bind it to one deterministic TickBatch
        │
        ▼
Game World Kernel
├─ validate all Intents against one before-state
├─ reserve shared resources
├─ reject conflicting or stale batch atomically
├─ apply compatible deltas in canonical order/combination
├─ advance environment once
├─ evaluate mission once
└─ emit one TickEvent with per-Intent receipts
        │
        ▼
Observations / Verification / Facts
        │
        └──────────────→ Host Task continuation
```

The Team Coordinator is a Game workload running on Host contracts. It is not a fourth Kernel and does not own generic Host state.

## 7. Durable identity model

### 7.1 Shared Mission Goal

```ts
interface MissionGoalRef {
  goalId: string;
  runId: string;
  objectiveGraphDigest: string;
  successPredicateId: string;
}
```

The complete Goal statement and Objective Graph are immutable content-addressed Artifacts. Host events reference their digests.

### 7.2 Actor Profile

Actor Profile is static configuration, not dynamic World status.

```ts
interface ActorProfile {
  actorId: string;
  role: "engineer" | "medic" | "security";
  providerOrder: string[];
  observationPolicyId: string;
  authorityPolicyId: string;
  riskPreferenceId: string;
}
```

Health, location, inventory, capability loss, and incapacitation are derived from World State.

### 7.3 Actor Task

Each specialist owns one durable Host Task stream for cognition continuity:

```text
task:<runId>:actor:<actorId>
```

The Actor Task references:

- shared Goal;
- current claimed Objective;
- latest actor-visible Knowledge digest;
- active strategic Operation/Skill continuation;
- unresolved Effect/Dispatch references;
- prepared Context and admitted Decision;
- waiting reason.

Each Actor Task has its own short Host lease, allowing independent cognition without holding a global team lock.

### 7.4 Team Coordinator Task

One small Host Task stream coordinates only the current World Tick:

```text
task:<runId>:team-coordinator
```

It references:

- exact World Tick and digest;
- eligible Actor Task revisions;
- received Action Proposal Artifacts;
- Authority Decision/Grant references;
- selected proposal subset;
- prepared Team Tick Effect and Dispatch;
- TickEvent Observation and Verification.

It does not contain a second copy of actor Tasks or World State.

## 8. Unified Objective Graph

M3.0 replaces the separate M2.1 Goal Requirement Graph and proposed M3 Team Task DAG with one Game-domain Objective Graph.

```ts
interface ObjectiveNode {
  objectiveId: string;
  label: string;
  visibility: "public" | "discovered";
  allOf: string[];
  anyOf: string[][];
  requiredCapabilities: string[];
  satisfactionPredicateId: string;
  priorityClass: "critical" | "high" | "normal" | "low";
}
```

Example:

```text
breach_controlled
  anyOf:
    breach_sealed
    maintenance_contained
```

A Task is not another dependency graph. It is an actor's durable claim or attempt to advance one visible Objective.

The Objective Graph is Game-owned because its predicates depend on Station Zero rules. Computing may promote a generic graph contract only after another real domain proves the same semantics.

## 9. Actor Knowledge and partial observation

### 9.1 Authoritative World versus visible Knowledge

```text
World State
  ├─ public alarm projection
  ├─ actor-local observation
  ├─ verified Fact visibility
  └─ delivered Message references
          ↓
Actor Knowledge
          ↓
Context Blocks and candidate annotations
```

The Host and World may know more than an actor. They may use hidden truth for physical admission, but cannot expose it through an actor's Task, rank, summary, or candidate explanation.

### 9.2 Required Context Blocks

Each actor Context must include:

- Actor identity and role;
- Goal identity and visible Objective slice;
- exact World digest and Observation revision;
- actor-local current Observation;
- active Task/Skill continuation;
- unresolved Dispatches;
- exact allowed Action candidates.

### 9.3 Optional Context Blocks

Selected under the Host token budget:

- delivered Messages;
- visible recent Facts;
- historical actor outcomes;
- optional team status summaries;
- optional strategy annotations derived from actor-visible Knowledge.

### 9.4 Strategy split

M3.0 separates:

```text
Authoritative admission semantics
Actor-visible advisory semantics
```

Authoritative admission may evaluate real preconditions, resource conflicts, authority, and World consistency.

Actor-visible advice may expose only known:

- Goal delta;
- threat delta;
- resource estimate;
- reversal cost;
- uncertainty;
- visible prerequisites.

M2.1's omniscient `strategicScore` cannot become the multi-Agent scheduler or leak hidden World truth.

## 10. Typed communication

### 10.1 Message is not Task or Artifact

```ts
interface TeamMessage {
  messageId: string;
  senderActorId: string;
  recipientActorIds: string[];
  kind:
    | "fact-share"
    | "help-request"
    | "task-offer"
    | "task-accept"
    | "intent-announce"
    | "blocker-notice"
    | "status-update";
  referencedFactIds: string[];
  referencedArtifactDigests: string[];
  boundedSummary: string;
  channel: "local" | "station-radio";
  createdTick: number;
  expiryTick: number;
}
```

Message delivery state is a Host event. Channel reachability is a Game-domain fact evaluated against the World.

### 10.2 Delivery rules

- local delivery requires sender and recipient co-location under the relevant Tick observation;
- station radio delivery requires Communications operational and powered;
- undelivered radio Messages wait until reachability or expiry;
- expired Messages remain historical evidence but leave current Context;
- Messages reference durable Facts/Artifacts for important evidence rather than becoming the evidence themselves.

Numeric defaults such as payload bytes, retained count, and TTL are scenario policy parameters to be measured. They are not universal architecture constants.

## 11. Authority model

### 11.1 Minimal ABAC input

```ts
interface AuthorityRequestAttributes {
  subject: {
    actorId: string;
    role: string;
    capabilities: string[];
    mandate: string[];
  };
  action: {
    operationKind: string;
    riskTags: string[];
  };
  target: {
    objectId: string;
    domain: string;
    criticality: string;
  };
  environment: {
    missionPhase: string;
    oxygenBand: string;
    reactorBand: string;
    communicationAvailable: boolean;
  };
  policyId: string;
}
```

Result:

```text
permit
require-human
 deny
```

### 11.2 Grant binding

A human or policy Grant is single-use and binds:

- actor;
- exact Action Proposal;
- exact operation and target;
- actor Context digest;
- World digest;
- authority policy revision;
- expiry Tick/revision.

A Message may request authority but never supplies it.

### 11.3 Capability versus authority

Capability answers:

> Can this actor physically/semantically perform this kind of action?

Authority answers:

> Is this exact action permitted under current policy and environment?

Both must pass.

## 12. Actor-turn leases and cognition

### 12.1 One cognition turn per actor

Each Actor Task uses the existing Host Task lease and revision CAS. The Provider call occurs outside the lease:

```text
lock Actor Task
→ compile and persist immutable Context
→ release lease
→ call Provider
→ reacquire Actor Task lease
→ reread current Task/World/Knowledge
→ admit or supersede Decision
→ persist Action Proposal reference
```

This mirrors the existing Ordivon Host cognition boundary.

### 12.2 No global Provider barrier

Eligible actors may be invoked concurrently. A slow or failed Provider cannot indefinitely block returned Proposals from other actors.

The Team Coordinator uses an explicit bounded collection condition, such as:

- all eligible actor decisions retained; or
- configured deadline/budget reached; or
- enough proposals exist to form a valid TickPlan.

An actor without an admitted Proposal contributes no Intent to that Tick. Missed cognition is not a World failure.

### 12.3 Coordinator lease

The Team Coordinator Task lease protects construction of one TickPlan for one exact World Tick/digest. Revision CAS prevents two coordinators from committing different plans for the same coordinator frontier.

The lease does not remain held during Provider calls or World dispatch.

## 13. Action Proposal and conflict selection

### 13.1 Action Proposal

```ts
interface ActionProposal {
  proposalId: string;
  actorId: string;
  actorTaskId: string;
  actorTaskRevision: number;
  contextDigest: string;
  worldDigest: string;
  objectiveId: string | null;
  actionCandidateId: string;
  intentBindingDigest: string;
  claimedResources: ResourceClaim[];
  requiredAuthorityAttributesDigest: string;
}
```

### 13.2 Conflict predicates

Typed conflict predicates include:

- same actor;
- same mutable target;
- opposite target state;
- shared consumable over-allocation;
- alternative Objective claim;
- spatial exclusion;
- action-specific simultaneous precondition conflict.

Examples:

- treatment conflicts with target movement in the same Tick because co-location is evaluated at Tick start;
- repair and power-on of the same broken system cannot occur in one Tick because power-on preconditions are not satisfied at Tick start;
- unrelated movement and treatment in different rooms may coexist;
- Engineer sealing and Security containment compete as alternative breach-control actions.

### 13.3 Exhaustive subset selection

With three specialists there are at most eight proposal subsets. M3.0 rejects a general maximal-independent-set engine.

The Coordinator:

1. enumerates all subsets;
2. removes unauthorized, stale, or conflicting subsets;
3. compares remaining subsets using public deterministic control criteria;
4. retains the selected subset and rejection evidence.

Control criteria may include:

- explicit human Grant;
- critical visible Objective class;
- longest waiting age;
- number of compatible actor Intents;
- stable actor/proposal identity tie-break.

The Coordinator must not use an omniscient model-strategy score to silently choose the team plan.

## 14. Atomic multi-Actor Tick

M3.0 supersedes the first M3 design's one-Command-per-Tick interleaving model.

### 14.1 TickPlan

```ts
interface TickPlan {
  tickPlanId: string;
  runId: string;
  worldRevision: number;
  worldDigest: string;
  selectedProposalIds: string[];
  intentBindings: ActorIntentBinding[];
  policyDecisionRefs: string[];
}
```

### 14.2 TickBatch

```ts
interface MultiActorTickBatch {
  batchId: string;
  runId: string;
  expectedRevision: number;
  intents: ActorIntent[];
}
```

Rules:

- at most one primitive Intent per actor;
- every Intent is bound to an admitted Proposal;
- all preconditions are evaluated against the same before-state;
- shared resources are reserved across the whole batch;
- the complete batch is rejected atomically on stale identity, conflict, or invariant failure;
- compatible deltas are combined under versioned deterministic rules;
- environment advances once;
- mission is evaluated once;
- one TickBatch produces one TickEvent.

### 14.3 TickEvent

```ts
interface MultiActorTickEvent {
  batchId: string;
  tick: number;
  beforeDigest: string;
  afterDigest: string;
  intentReceipts: ActorIntentReceipt[];
  environmentFacts: WorldFact[];
  missionStatus: MissionStatus;
}
```

The TickEvent contains per-Intent facts and verification so each Actor Task can observe the part relevant to its Proposal.

### 14.4 Backward compatibility

- `station-zero-core@1` and `@2` retain one Intent per Tick and all frozen receipts;
- `station-zero-core@3` introduces atomic multi-Actor Tick semantics;
- old Runs replay with their bound Ruleset;
- new M3 Runs use Scenario v2 / Ruleset v3.

## 15. Effect and Dispatch mapping

M3.0 avoids inventing a generic EffectGroup primitive.

Provider Action Proposals are not yet external Effects. After authority and compatibility selection, the Team Coordinator creates one semantic Game Effect:

```text
Effect: advance Station Zero by one admitted Team Tick
```

The Effect binds:

- World Run identity and version;
- exact TickPlan digest;
- selected Proposal references;
- exact actor Intent bindings;
- expected World digest/revision;
- idempotency identity;
- TickEvent verification plan.

The Game adapter binds that Effect to one Dispatch containing one `MultiActorTickBatch`.

The resulting Observation contains one TickEvent and per-Intent receipts. Host verification maps those receipts back to the actor Proposals and advances each Actor Task independently.

This preserves the current Computing contract:

```text
one Effect
→ one concrete Dispatch attempt
→ one Observation
→ one Verification
```

without promoting Game Tick semantics into Runtime or Computing.

## 16. Host integration strategy

### 16.1 Normative versus deployment ownership

Normative Task/Event/Lease/Context semantics come from `ordivon-host` and future `ordivon-protocol` conformance vectors.

The target architecture is a Host-owned Team Coordinator workload with a Game World adapter.

M3.0 does not force an immediate cross-process Python/TypeScript service boundary. Before implementation, one of two deployment forms must be selected through a small design experiment:

#### Option A — Conformance-backed embedded Game adapter

- TypeScript implementation remains in-process with Game;
- implements the exact promoted Host protocol subset;
- validated against shared JSON conformance vectors;
- lowest operational friction;
- temporary semantic duplication remains explicit.

#### Option B — Local Ordivon Host sidecar

- Python Host owns Tasks, leases, Context, and events directly;
- Game exposes a narrow local World adapter;
- strongest code reuse and ownership purity;
- adds process, protocol, deployment, and failure boundaries.

M3.0 recommends Option A for the first M3 executable slice unless a sidecar proof demonstrates lower total complexity. Extraction is triggered by a second real consumer or a measured need for independent Host operation.

### 16.2 No Game-private generic expansion

The following may not be added as Game-only permanent abstractions without a cross-stack conformance decision:

- generic Task event state machine;
- generic lease semantics;
- generic Context compiler;
- generic authority envelope;
- generic Effect/Dispatch state algebra;
- generic mailbox runtime.

Game-specific Objective predicates, observation rules, message reachability, specialist capabilities, conflict predicates, and TickBatch rules remain local.

## 17. Persistence design

M3.0 rejects the original plan to add a second generic scheduler or Task graph as primary state.

The implemented P0–P2 logical storage is:

```text
Host contract semantics:
  immutable TaskDescriptor / Context / Decision objects
  Host Contract journal events
  Task-local revision and frontier semantics
  Goal-scoped Task revision snapshots
  Effect / Dispatch / Observation / Verification / Outcome objects
  short Task leases in the independent Ordivon Host

Game domain truth:
  Run metadata
  World command/TickBatch journal
  TickEvent journal
  sparse World snapshots
  domain proposals, authority, Messages, and compatibility policy
```

The embedded convergence adapter currently stores protocol objects in the existing Game `host_artifacts` and `host_journal` tables. Legacy `team_*` tables remain as executable compatibility projections during dual-run validation; they are not claimed as the final cross-project Host authority.

The completed implementation and measured boundary are recorded in [`HOST-CONVERGENCE-P0-P2.md`](HOST-CONVERGENCE-P0-P2.md).

## 18. API target

M3.0 reduces the proposed Team API surface to four primary operations:

```text
GET  /api/team/state
POST /api/team/step
POST /api/team/run
POST /api/team/input
```

`team/input` uses a typed union for:

- approve;
- deny;
- send-message;
- redirect-objective;
- pause;
- cancel.

The Team State projection contains actor cards, Objective state, current proposals, Messages, authority requests, waits, latest TickPlan, and evidence references. M4 may redesign presentation without changing semantic ownership.

## 19. M3.0 design decisions that supersede the first M3 design

| First M3 design | M3.0 correction |
|---|---|
| Game-specific Host projections and many new tables | reuse Host Event/projection/lease protocol; query views only |
| one primitive Command per simulation Tick | atomic multi-Actor TickBatch; environment once |
| Team Task DAG in addition to M2.1 Goal graph | one Game Objective Graph; Tasks are claims/attempts |
| global Coordination Round | actor Tasks plus one short Team Coordinator Task bound to World Tick |
| one-dimensional authority lattice | minimal ABAC decision and exact Grant |
| general greedy conflict graph selection | enumerate at most eight subsets |
| fixed 16 KiB M3 Context | Host token budget and measured envelope target |
| omniscient shared strategic rank | actor-visible advisory semantics only |
| dynamic Agent status in Profile | derive status from World State |
| many narrow Team APIs | State / Step / Run / Input |
| new Game Control Kernel | Game Team Coordinator workload on Host contracts |

## 20. M3.0 non-goals

M3.0 does not:

- implement Engineer, Medic, or Security;
- modify the World reducer;
- add TickBatch v3 code;
- migrate current Host storage;
- add an Ordivon Host service process;
- add Runtime tools;
- implement A2A, Temporal, Orleans, LangGraph, or OpenAI Agents SDK;
- choose final Context token budgets or Message TTLs without measurement;
- close Issue #5;
- claim that M3 architecture is implemented.

## 21. M3.0 exit criteria

M3.0 is complete when the design repository records all of the following:

1. exact ownership across Computing, Host, Runtime, Game, and UI;
2. Host Event/projection/lease/context mechanisms are reused rather than reimplemented conceptually;
3. one Objective Graph replaces duplicate Goal/Task dependency models;
4. Actor Knowledge prevents hidden global truth from entering private Context;
5. authority uses subject/action/target/environment policy attributes;
6. actor cognition and coordinator transitions have explicit lease/CAS boundaries;
7. multi-Agent time uses atomic multi-Intent TickBatch semantics;
8. Team Tick maps to existing Effect/Dispatch/Observation/Verification semantics without a new generic EffectGroup;
9. implementation begins only after the embedded-versus-sidecar deployment experiment is selected;
10. original M3 design is marked superseded; Issue #5 remained open until the subsequent M3 implementation and evaluation merged.

## 22. Mature reference sources

- Temporal documentation: `https://docs.temporal.io/`
- Microsoft Azure Event Sourcing pattern: `https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing`
- Microsoft Orleans overview and turn-based concurrency: `https://learn.microsoft.com/en-in/dotnet/orleans/overview`, `https://learn.microsoft.com/en-us/dotnet/orleans/grains/external-tasks-and-grains`
- A2A protocol specification: `https://a2a-protocol.org/dev/specification/`
- NIST SP 800-162 ABAC: `https://csrc.nist.gov/pubs/sp/800/162/upd2/final`
- OpenAI Agents SDK orchestration: `https://openai.github.io/openai-agents-python/multi_agent/`
