# M3 design — multi-Agent team, communication, authority, and conflict

Status: proposed for Issue #5  
Design baseline: `main@b5e3db64c38c93c22a75ca54020ff3bc33d9eef6`  
Prerequisites: M2 persistent Host and M2.1 public goal-directed strategy semantics

## 1. Decision summary

M3 will add a persistent three-specialist team:

```text
Engineer Imani
Medic Reyes
Security Chen
```

The system will use:

```text
one authoritative deterministic World
+ one shared Team Goal
+ actor-scoped Tasks, Attempts, Contexts, and Providers
+ typed delivery-limited communication
+ explicit player-configured authority
+ deterministic proposal conflict resolution
+ interleaved single-writer World execution
```

M3 will **not** add a manager model that privately chooses what the specialists should do. The Host compiles public task, authority, communication, conflict, and scheduling semantics. Each specialist remains an independent cognitive actor and may use a different Provider.

M3 also will not introduce simultaneous World mutation. Multiple Agents may reason, communicate, hold active plans, and wait concurrently, but the authoritative World continues to commit exactly one primitive Command per simulation Tick. This preserves the existing Command/Event journal, idempotent Dispatch, Facts, Verification, and replay model while still allowing genuine multi-Agent coordination through interleaved execution.

## 2. Goals

M3 must satisfy Issue #5:

- each specialist has at least one exclusive capability;
- each specialist receives an independent bounded observation;
- communication is typed, limited, and can fail or be delayed;
- Team Tasks have explicit AND/OR dependencies;
- restricted Operations require authority under player-defined policy;
- conflicting proposals produce explicit deterministic resolution;
- one Agent can progress while another waits, is denied, loses communication, or becomes incapacitated;
- no duplicate or contradictory World mutation occurs;
- M1, M1.5, M2, and M2.1 receipts remain unchanged.

## 3. Non-goals

M3 does not include:

- a general-purpose multi-Agent framework;
- a full Agent-to-Agent network protocol implementation;
- free-form shared group chat or transcript replay;
- hidden centralized planning by another language model;
- same-Tick simultaneous physical mutations;
- a polished player-facing interface; M4 owns that surface;
- large societies, competitive arenas, or emergent governance;
- unrestricted dynamic role creation;
- a general theorem prover for plan feasibility.

## 4. Core invariants

### I-1 — World authority remains singular

Only the versioned Ruleset may mutate World State. Agent messages, beliefs, proposals, approvals, and task states are Host records and cannot directly change the World.

### I-2 — Providers choose only exact current specialist Operations

A Provider may select only an `operationCandidateId` present in its actor-scoped Context. It cannot invent an actor, target, Task, WorldCommand, authority grant, message delivery, or completion claim.

### I-3 — Every primitive mutation remains idempotent and verified

The existing stable chain remains:

```text
Attempt step
→ Effect
→ Dispatch
→ stable Command ID
→ World Journal Event
→ Observation
→ Verification
```

### I-4 — Private observation is derived, not copied from a shared transcript

Each Context is compiled from the authoritative World, actor Observation Policy, assigned Tasks, delivered typed Messages, and verified Facts visible to that actor.

### I-5 — Communication is not authority

A Message can inform, request, offer, warn, or announce intent. It cannot authorize a restricted Operation or mutate another Agent's Task.

### I-6 — Authority is explicit, bounded, and stale-sensitive

An approval is bound to Run, actor, proposal, Operation identity, Context identity, World digest, and expiry. It is single-use and invalid after material World drift.

### I-7 — Conflict resolution is deterministic

No model judges which proposal wins. The Host constructs a typed conflict graph and applies a public priority tuple.

### I-8 — Independent progress is preserved

A waiting or failed specialist cannot block unrelated ready work. The scheduler may interleave primitive steps from multiple admitted Attempts.

### I-9 — No hidden team policy

The Host may expose public ranks, dependency edges, threat horizons, authority requirements, conflict reasons, and wait reasons. It may not silently replace a valid Provider Decision with a scripted team plan.

### I-10 — Backward compatibility is versioned

M3 uses `station-zero@2` and `station-zero-core@3`. Existing Scenario v1 and Ruleset v1/v2 remain byte- and digest-stable.

## 5. Structural model

M3 uses three explicit graph structures and one finite authority lattice.

### 5.1 Team Task AND/OR DAG

```text
G_task = (V_task, E_requires, E_alternative)
```

- `requires`: all predecessor Tasks must be satisfied;
- `alternative`: any one predecessor may satisfy the requirement;
- the graph must remain acyclic;
- the deterministic Ready Frontier contains Tasks whose required predecessors are satisfied and that have at least one capable active specialist.

The breach branch is the first explicit OR dependency:

```text
control breach
├── Engineer: physically seal breach
└── Security: remotely contain maintenance section
```

### 5.2 Dynamic communication graph

```text
G_message(t) = (V_actor ∪ {player}, E_local(t) ∪ E_radio(t) ∪ E_player)
```

- a local edge exists between actors in the same room;
- a radio edge exists only while Communications is operational and powered;
- the player authority edge is available for approval requests but does not reveal hidden World State;
- delivery is evaluated against the World at the delivery revision, not when the sender generated text.

### 5.3 Proposal conflict graph

```text
G_conflict(round) = (V_proposal, E_conflict)
```

Two proposals are adjacent when their deterministic resource claims conflict. Conflict edge kinds include:

- `same_actor`;
- `same_task_claim`;
- `same_target_write`;
- `opposite_target_state`;
- `shared_consumable`;
- `exclusive_authority`;
- `dependency_invalidated`;
- `spatial_control`.

A deterministic greedy maximal independent set, ordered by the public priority tuple, determines which non-conflicting proposals may become active Attempts.

### 5.4 Authority lattice

```text
routine < specialist < restricted < critical
```

An actor's configured auto-approval level must dominate the Operation requirement. Otherwise the proposal enters `awaiting_authority` and produces an immutable approval request.

## 6. Persistent domain model

### 6.1 Team Goal

```ts
interface TeamGoal {
  goalId: string;
  runId: string;
  statement: string;
  successCondition: GoalSuccessCondition;
  status: GoalStatus;
  revision: number;
}
```

The Goal is owned by the team, not by `engineer-01`.

### 6.2 Agent Profile

```ts
interface AgentProfile {
  actorId: string;
  role: "engineer" | "medic" | "security";
  providerOrder: string[];
  roleGoal: string;
  riskPolicyId: string;
  observationPolicyId: string;
  communicationPolicyId: string;
  autoApproveThrough: AuthorityLevel;
  status: "active" | "incapacitated" | "disabled";
}
```

Profiles are configuration and persistent identity. Provider Sessions are replaceable.

### 6.3 Team Task

```ts
interface TeamTask {
  taskId: string;
  goalId: string;
  runId: string;
  kind: string;
  assignedActorId: string | null;
  requiredCapabilities: string[];
  phase:
    | "blocked_dependency"
    | "ready"
    | "claimed"
    | "active"
    | "waiting_message"
    | "awaiting_authority"
    | "waiting_conflict"
    | "waiting_replan"
    | "succeeded"
    | "failed"
    | "cancelled";
  allOfTaskIds: string[];
  anyOfTaskGroups: string[][];
  activeAttemptId: string | null;
  completedAttemptIds: string[];
  waitRecordId: string | null;
  priorityClass: "critical" | "high" | "normal" | "low";
  revision: number;
}
```

### 6.4 Agent Attempt

The current Attempt model becomes actor-generic and adds:

```ts
actorId: string;
proposalId: string;
planDependencyDigest: string;
lastVerifiedWorldRevision: number;
```

### 6.5 Agent Proposal

```ts
interface AgentProposal {
  proposalId: string;
  runId: string;
  roundId: string;
  actorId: string;
  taskId: string;
  attemptNumber: number;
  contextId: string;
  worldDigest: string;
  operationCandidateId: string;
  strategicRank: number;
  authorityRequirement: AuthorityRequirement;
  resourceClaims: ResourceClaim[];
  messageDrafts: TeamMessageDraft[];
  status:
    | "retained"
    | "awaiting_authority"
    | "admitted"
    | "waiting_conflict"
    | "superseded"
    | "rejected";
}
```

### 6.6 Coordination Round

```ts
interface CoordinationRound {
  roundId: string;
  runId: string;
  worldRevision: number;
  worldDigest: string;
  eligibleActorIds: string[];
  proposalIds: string[];
  admittedProposalIds: string[];
  conflictSetIds: string[];
  status: "collecting" | "resolving" | "resolved" | "stale";
}
```

### 6.7 Typed Team Message

```ts
type TeamMessageKind =
  | "fact_share"
  | "help_request"
  | "task_offer"
  | "task_accept"
  | "intent_announce"
  | "blocker_notice"
  | "conflict_notice"
  | "status_update";

interface TeamMessage {
  messageId: string;
  runId: string;
  senderActorId: string;
  recipientActorIds: string[];
  kind: TeamMessageKind;
  taskId: string | null;
  referencedFactIds: string[];
  referencedArtifactDigests: string[];
  boundedSummary: string;
  channel: "local" | "station_radio";
  createdWorldRevision: number;
  expiresAfterTick: number;
  status: "queued" | "delivered" | "expired" | "rejected";
  deliveredWorldRevision: number | null;
}
```

Messages are delivery envelopes. Important evidence remains an immutable Fact or Artifact reference.

### 6.8 Authority Request and Grant

```ts
interface AuthorityRequest {
  requestId: string;
  proposalId: string;
  actorId: string;
  requiredLevel: AuthorityLevel;
  reason: string;
  projectedConsequences: OperationStrategyAnalysis;
  status: "pending" | "approved" | "denied" | "expired";
}

interface AuthorityGrant {
  grantId: string;
  requestId: string;
  proposalId: string;
  actorId: string;
  contextId: string;
  worldDigest: string;
  authorityLevel: AuthorityLevel;
  issuedBy: "player" | "policy";
  expiresAfterWorldRevision: number;
  consumedAtWorldRevision: number | null;
}
```

### 6.9 Wait Record

```ts
interface WaitRecord {
  waitRecordId: string;
  actorId: string;
  taskId: string;
  reason:
    | "dependency"
    | "message_delivery"
    | "authority"
    | "conflict"
    | "replan"
    | "provider";
  blockingIds: string[];
  sinceWorldRevision: number;
  unblockCondition: typed predicate;
  resolvedAtWorldRevision: number | null;
}
```

## 7. Scenario v2 specialists

M3 introduces a new versioned scenario rather than mutating the existing one.

### 7.1 Engineer Imani

Initial role:

- command-center;
- toolkit;
- breaker-key;
- one spare part.

Exclusive capabilities:

- `repair_system`;
- `set_power`;
- `seal_hull`.

Shared capabilities:

- move;
- pickup;
- send distress;
- wait.

Role Goal:

> Restore and control station infrastructure while preserving enough power and time for verified rescue.

### 7.2 Medic Reyes

Initial role:

- medical-bay;
- two medkits.

Exclusive capabilities:

- `stabilize_crew`;
- `treat_agent`.

`TreatAgentCommand`:

- target must be a co-located living Agent;
- consumes one medkit;
- restores bounded health;
- cannot resurrect a zero-health Agent;
- emits treatment Facts and independent Verification.

Role Goal:

> Preserve crew and specialist capability long enough for the Team Goal to complete.

### 7.3 Security Chen

Initial role:

- new `security-post` room;
- security access credential.

Exclusive capability:

- `contain_hazard`.

`ContainHazardCommand`:

- issued from the security console;
- closes emergency bulkheads around the maintenance breach;
- consumes an immediate bounded battery amount;
- stops breach oxygen loss;
- requires restricted authority by default;
- does not consume sealant;
- remains distinct from physical sealing.

Role Goal:

> Contain hazards, preserve station access, and use restricted controls only when their consequences are justified.

### 7.4 Multiple valid breach plans

The Team Goal uses `breach_controlled`:

```text
breach sealed by Engineer
OR
maintenance section contained by Security
```

The two plans have different costs:

- physical sealing costs travel, time, and sealant;
- remote containment costs authority and battery.

Both are valid, auditable, and strategy-dependent.

### 7.5 Individual incapacitation

An Agent at zero health becomes unavailable and loses its active proposal/Attempt. The mission does not immediately fail because one specialist is incapacitated. Remaining Agents continue unrelated work. Existing environmental terminal failures remain, and full Team incapacitation is terminal.

M3 does not add a hidden `unwinnable` oracle. Capability loss may make later victory impossible, but the World reaches that conclusion through ordinary resource, timeout, and team-incapacitation rules.

## 8. Actor-scoped observation

`AgentContext v3` remains bounded to 16 KiB but is compiled per actor.

Every actor sees:

- own location, health, inventory, capabilities, and role policy;
- current room and adjacent room identifiers;
- objects and actors in the current room;
- public station alarms;
- shared Team Goal;
- assigned/claimable Tasks visible to that role;
- delivered typed Messages;
- verified Facts whose visibility policy includes the actor;
- actor-specific allowed Operations and strategic semantics.

Role-specific observation:

### Engineer

- local system integrity;
- station power state while at command-center or power-junction;
- engineering alarms and resource requirements.

### Medic

- exact health and treatment state of co-located Agents and Crew;
- station oxygen alarm;
- bounded last-known health shared through delivered Facts.

### Security

- hazard containment and bulkhead state;
- local room access state;
- security-console alarms;
- restricted-control consequences.

An actor does not receive another actor's private Provider rationale, undelivered Messages, full inventory, or hidden room detail.

## 9. Communication semantics

### 9.1 Channels

#### Local

- sender and recipient are in the same room;
- delivery is immediate and durable;
- no station communications dependency.

#### Station radio

- recipients may be remote;
- delivery requires Communications operational and powered at delivery time;
- otherwise the Message remains queued until TTL or restoration;
- delivery never rewrites the original creation revision.

### 9.2 Limits

Default M3 policy:

- at most one outbound Message per actor per Coordination Round;
- maximum canonical payload 512 bytes;
- maximum eight delivered Messages retained in an Agent Context;
- TTL of four simulation Ticks unless the message type defines a shorter bound;
- expired Messages remain auditable but are not exposed as current information.

### 9.3 No free-form group transcript

A bounded human-readable summary is allowed, but routing, Task references, Fact references, urgency, channel, TTL, and status are typed. Providers cannot rely on an unbounded shared conversation.

## 10. Team Task compiler

The deterministic Task compiler derives a small Team Task DAG from Scenario v2 and current World State.

Initial task families:

```text
mitigate_reactor
control_breach
restore_life_support
preserve_crew
preserve_specialists
restore_communications
transmit_distress
```

Example dependencies:

```text
transmit_distress
  allOf:
    restore_communications
    communications_powered

station_victory
  allOf:
    mitigate_reactor
    control_breach
    restore_life_support
    preserve_crew
    transmit_distress
    oxygen_safe
    reactor_safe
```

The compiler exposes claimable work; it does not assign a hidden optimal plan. A specialist may claim only a Task with compatible required capabilities.

## 11. Proposal and authority flow

```text
private Context
→ Provider Decision
→ exact Operation admission
→ Agent Proposal
→ Authority check
→ Conflict graph
→ Proposal admission or typed wait
→ Agent Attempt
```

Authority examples:

| Operation | Default requirement |
|---|---|
| move, wait, fact share | routine |
| repair, treatment, normal power enable | specialist |
| remote hazard containment | restricted |
| disable life support under low oxygen | critical |
| cancel or override another actor's admitted Attempt | critical |

Player configuration sets `autoApproveThrough` independently per actor. A Security Agent may therefore be allowed to self-execute containment in one run and require player approval in another.

## 12. Resource claims and conflict graph

Every admitted Operation compiles deterministic claims before execution.

```ts
type ResourceClaim =
  | { kind: "actor"; actorId: string }
  | { kind: "task"; taskId: string }
  | { kind: "target_write"; targetType: string; targetId: string; desiredState?: string }
  | { kind: "consumable"; holderType: "room" | "actor"; holderId: string; itemId: string; quantity: number }
  | { kind: "authority"; authorityClass: string }
  | { kind: "spatial_control"; roomId: string; control: string };
```

Examples:

- Engineer seal and Security containment conflict on the same breach-control Task but represent alternative plans;
- two Agents cannot claim the same medkit quantity;
- power-on and power-off for the same system are opposite writes;
- two unrelated movements do not conflict;
- treatment and infrastructure repair can be admitted together.

## 13. Deterministic conflict resolver

Unauthorized, stale, or invalid proposals are removed before graph selection.

The resolver orders proposals by:

1. projected verified victory;
2. shortest critical threat horizon mitigated;
3. already-issued authority grant;
4. number of Team Task dependencies unlocked;
5. Operation strategic rank;
6. waiting age;
7. actor ID;
8. proposal ID.

It then greedily selects a deterministic maximal independent set. Selected proposals become active Attempts. Conflicting losers enter `waiting_conflict` with explicit blocking proposal and conflict-edge evidence.

This is intentionally not a globally optimal solver. It is bounded, replayable, understandable, and sufficient for the small M3 team.

## 14. Execution model — concurrent cognition, serialized World

### 14.1 Why not same-Tick multi-intent mutation

Current World receipts bind one Command to one Event and advance environment once per Command. True simultaneous mutation would require redefining:

- per-intent before/after digests;
- environment Facts;
- verification order;
- command/event stream alignment;
- snapshot and replay receipts;
- idempotent retry of partial multi-intent batches.

Issue #5 does not require physical simultaneity. M3 therefore preserves one authoritative primitive Command per Tick and obtains useful concurrency through multiple persistent active Attempts and interleaving.

### 14.2 Interleaving

At each World Tick, the Team Scheduler selects one ready primitive Skill step from admitted Attempts.

Default scheduling tuple:

1. critical threat class;
2. proposal admission priority;
3. Task dependency unlock;
4. actor waiting age;
5. actor ID.

Fairness rule:

> An actor may not execute more than two consecutive primitive steps while another non-conflicting ready Attempt exists.

### 14.3 Plan freshness under interleaving

The current M2 equation:

```text
expectedRevision = contextRevision + skillStepIndex
```

must be removed for Team execution because unrelated actors may advance the World between steps.

M3 introduces a `PlanDependencySet` containing only state paths and resource claims relevant to the remaining Skill. Before each primitive step, the Host recomputes a canonical dependency digest:

- unchanged relevant dependencies: continue at current World revision;
- unrelated World changes: allowed;
- relevant target, inventory, authority, route, or Task changes: enter `waiting_replan`;
- terminal or invalidated Task: stop the Attempt.

This allows Medic movement to interleave with Engineer repair preparation without declaring both plans stale.

## 15. Team Host loop

```text
1. verify World and Host journals
2. deliver or expire queued Messages
3. refresh Team Task graph
4. resolve Wait Records whose conditions are now true
5. if no unresolved Coordination Round:
     compile private Contexts for eligible actors
     invoke bounded Provider calls
     retain Decisions and Proposals
6. evaluate authority
7. build and resolve conflict graph
8. admit non-conflicting proposals
9. select one ready primitive step
10. execute or reconcile stable Dispatch
11. retain Observation and Verification
12. advance Task, Attempt, Message, and wait projections
13. repeat until terminal, blocked for player authority, or step budget exhausted
```

Provider calls may run concurrently with a configured maximum of three, but all outputs are persisted before conflict resolution. Execution remains deterministic after Decisions are retained.

## 16. Persistence

Existing tables remain for backward-compatible single-Agent Runs. M3 adds projections rather than overloading one-row-per-Run M2 tables:

```text
host_agents
host_team_tasks
host_task_edges
host_coordination_rounds
host_proposals
host_conflict_sets
host_messages
host_authority_requests
host_authority_grants
host_wait_records
```

Existing `host_attempts`, `host_effects`, `host_dispatches`, and `host_observations` are generalized with actor/proposal identity while retaining stable IDs and old row compatibility.

All meaningful transitions also enter the existing independent Host Journal.

## 17. Recovery

Fresh-process recovery must cover:

- Provider returned but Proposal not retained;
- Proposal retained but conflict set not resolved;
- authority approved but grant not consumed;
- Message queued but delivery result not retained;
- Attempt admitted but first Effect not prepared;
- World Command committed but Observation absent;
- one actor's step verified while another remains waiting;
- actor incapacitated during another actor's active Skill;
- conflict winner completed while loser still references the old blocker.

Recovery never recalls a Provider after its valid Decision/Proposal is retained.

## 18. API scope

M3 adds engineering control APIs:

```text
POST /api/team/initialize
GET  /api/team/state
POST /api/team/round
POST /api/team/step
POST /api/team/run
GET  /api/team/tasks
GET  /api/team/messages
POST /api/team/messages
GET  /api/team/conflicts
GET  /api/team/authority
POST /api/team/authority/:requestId/approve
POST /api/team/authority/:requestId/deny
```

These APIs expose evidence and enable testing. M4 will convert them into a player-readable mission-control interface.

## 19. Acceptance scenarios

### A — Exclusive capability

- Engineer repair succeeds;
- Medic repair fails `capability_missing`;
- Medic treatment succeeds;
- Security containment succeeds only with correct capability and authority.

### B — Multiple valid plans

Same Scenario v2 seed:

- Team configuration 1 approves Security containment;
- Team configuration 2 denies containment and Engineer seals the breach;
- both can reach verified victory with different event traces and resource curves.

### C — Authority

- restricted containment proposal enters `awaiting_authority`;
- unrelated Engineer/Medic work continues;
- stale approval cannot authorize a changed proposal;
- approval or denial materially changes the admitted plan.

### D — Communication limit

- remote Message queues while Communications is down;
- same-room local Message delivers;
- queued radio Message delivers after restoration if TTL remains;
- expired information is not exposed as current Context;
- coordination outcome differs between connected and disconnected configurations.

### E — Conflict and waiting

- Engineer seal and Security containment create a typed alternative conflict;
- resolver admits one and persists why;
- loser waits rather than failing;
- conflict clears when the selected breach-control Task succeeds.

### F — Independent progress

- Medic may wait for a delivered health request while Engineer progresses;
- Security may await player authority while Medic acts;
- one incapacitated specialist does not immediately terminate unrelated active work.

### G — Interleaving

- unrelated Skill steps from two actors interleave without stale-plan rejection;
- a relevant resource or target change forces deterministic replan;
- no duplicate World effect occurs after interruption.

### H — Replay

- every M3 World Event replays exactly;
- Host conflict, authority, message, wait, and Task evidence verifies independently;
- M1/M2 receipts remain unchanged.

## 20. Live evaluation

Minimum M3 evaluation matrix:

1. all-Fixture deterministic Team baseline;
2. all-Codex specialists;
3. mixed Engineer Codex / Medic Hermes / Security Codex;
4. provider replacement during an active Team run;
5. communication connected vs disconnected;
6. containment auto-approved vs player-denied;
7. one-specialist incapacitation.

Report:

- mission outcome and score;
- Provider calls, tokens, latency, and reported cost;
- per-actor Task and Attempt counts;
- messages created, delivered, queued, and expired;
- authority requests, approvals, denials, and stale grants;
- conflicts and waiting duration;
- interleaving fairness;
- World/Host replay equality;
- human interventions.

## 21. Rejected alternatives

### Manager Agent

Rejected because it would become hidden team policy, re-centralize cognition, and make specialist independence difficult to evaluate.

### Free-form group chat

Rejected because it creates unbounded context, unclear delivery semantics, and weak provenance.

### Full multi-intent Tick in M3

Rejected for now because it would force a broad World Journal redesign without being required to prove communication, authority, conflict, or independent progress.

### Full state-space team planner

Rejected because M2.1 already measured unbounded search as too expensive. M3 preserves bounded public semantics.

### Full A2A protocol server

Deferred. M3 borrows the useful separation of Tasks, Messages, and Artifacts, but internal game coordination does not need external interoperability yet.

## 22. Exit boundary

M3 is complete when Ordivon Game can truthfully claim:

```text
three persistent specialists
+ independent bounded cognition
+ typed limited communication
+ shared AND/OR task dependencies
+ player-configured authority
+ deterministic conflict resolution
+ interleaved verified execution
+ explicit waiting and recovery
```

M3 does not need a polished game UI. It must deliver the trustworthy team substrate that M4 can expose to the player.
