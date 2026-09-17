# Ordivon Agent Service — Minimal Kernel R1

Status: **DESIGN SYNTHESIS / IMPLEMENTATION-READY SPEC**
Synthesized: 2026-09-17
Evidence basis: AWS AgentCore, Microsoft Foundry Agent Service, Google Gemini Enterprise Agent Platform, LangSmith Deployment, plus current local Host/Runtime/Harness boundaries.

## 1. One-sentence model

**Ordivon Agent Service is the durable agent-cluster control and service plane that turns service requests into versioned agent identities, goals, tasks and assignments, reconciles desired agent presence onto Hosts/Runtimes, governs agent/tool communication through standard protocol adapters, and projects fleet state without owning physical execution or the model loop.**

It is not primarily:

- an Agent Harness;
- a physical execution Runtime;
- a general workflow engine;
- a Board/database UI;
- a replacement for MCP, A2A, IAM, OTel, Temporal, Kubernetes or policy engines.

## 2. External-common kernel vs Ordivon-specific organization semantics

### External-common service kernel

The four reference platforms converge strongly on these responsibilities:

```text
Agent definition / revision / registry
Deployment desired state
Session / run identity
Runtime/provider abstraction
Reconciliation / scheduling
Capability/tool gateway
Agent/workload identity
Policy/authorization boundary
Standard protocol adapters
Observability / evaluation hooks
```

These are not uniquely Ordivon concepts and should remain provider-neutral.

### Ordivon-specific service semantics

Ordivon adds a higher organizational model:

```text
Service Request
Agent Birth
Agent Goal
Agent Task
Agent Assignment
Agent Team / Organization
Agent Board projection
A2A communication / service routing
```

These are useful only if they remain thin service semantics over mature substrates below them.

## 3. Final authority boundary

```text
                         ORDIVON AGENT SERVICE

  Request  Agent Registry  Birth  Goal  Task  Assignment  Session
     |           |          |      |     |        |          |
     +-----------+----------+------+-----+--------+----------+
                              |
                    desired fleet / routing
                              |
                   policy / identity / gateway
                              |
                       Service Reconciler
                              |
               +--------------+--------------+
               |                             |
               v                             v
          ORDIVON HOST                 OTHER HOST/PROVIDER
       node/local continuity                adapter
               |
               v
          ORDIVON RUNTIME
 physical execution / workspace / Job / Attempt / Artifact
               |
               v
          AGENT HARNESS
 model/context/tool/subagent loop
               |
               v
      Plugin / Skill / Tool / MCP
```

### Agent Service owns

- semantic Agent identity and revision references;
- Agent lifecycle intent (`desired presence`);
- Birth orchestration;
- Goal hierarchy and progress semantics;
- Task identity, dependency and assignment semantics;
- service-facing Sessions/messages;
- team/organization relationships;
- routing and protocol endpoint selection;
- fleet desired state and reconciliation policy;
- projection/event model for Board and fleet observability;
- mapping to external identity/policy/gateway providers.

### Host owns

- node/local-process presence evidence;
- wake/re-entry/continuity primitives;
- local supervision;
- observation of whether the locally requested service carrier is present/alive.

Host does **not** own global desired fleet state, Goal/Task semantics, or cluster scheduling.

### Runtime owns

- physical Workspace identity;
- Job/Attempt identity;
- command/process execution;
- cancellation/recovery mechanics;
- exact execution/effect evidence within its declared boundary;
- Artifact retention and physical execution state.

Runtime does **not** declare Agent Task semantic completion.

### Harness owns

- model invocation loop;
- context assembly/projection;
- Skill disclosure/loading;
- tool selection/request;
- subagent delegation inside one cognitive run;
- termination/replanning semantics of that loop.

Harness does **not** own Agent fleet lifecycle or cluster control.

## 4. Core object and identity algebra

The minimum Service must preserve these identities separately:

```text
ServiceRequestId
AgentDefinitionId
AgentRevisionId
AgentInstanceId
AgentIdentityId
GoalId
TaskId
AssignmentId
TeamId
SessionId
MessageId
DesiredPlacementId
HostId
RuntimeJobId       # foreign reference
RuntimeAttemptId   # foreign reference
PluginProfileId
CapabilityId
PolicyBindingId
TraceId
EventId
```

### Why they must remain distinct

```text
AgentDefinitionId != AgentInstanceId
AgentInstanceId   != AgentIdentityId
TaskId            != RuntimeJobId
SessionId         != TaskId
HostId            != AgentIdentityId
GoalId            != TaskId
Board item        != any authoritative object identity
```

Collapsing these would destroy version history, delegation, retries, reassignments, or auditability.

## 5. Minimal data model

```text
ServiceRequest {
  id
  requestClass
  requesterRef
  inputRef
  status
  createdAt
}

AgentDefinition {
  id
  name
  harnessKind
  pluginProfileRef
  defaultRuntimeProfile
}

AgentRevision {
  id
  definitionId
  immutableRevision
  harnessRef
  pluginProfileRef
  runtimeProfileRef
  provenance
}

AgentInstance {
  id
  revisionId
  identityRef
  desiredState
  observedState
  placementRef?
  createdAt
  retiredAt?
}

Goal {
  id
  parentGoalId?
  ownerAgentOrTeamRef
  objective
  acceptanceRef
  status
}

Task {
  id
  goalId?
  requestId?
  taskType
  inputRef
  acceptanceRef
  desiredState
  semanticState
  priority
  dependencies[]
}

Assignment {
  id
  taskId
  assigneeAgentId
  assignmentRevision
  runtimeRefs[]
  status
}

Session {
  id
  participants[]
  purposeRef?
  protocol
  stateRef?
}

DesiredPlacement {
  id
  agentInstanceId
  placementPolicyRef
  targetHostRef?
  desiredState
  observedState
}

ServiceEvent {
  id
  aggregateType
  aggregateId
  revision
  eventType
  payloadRef
  traceId
  createdAt
}
```

Board data is a derived projection from these records/events and is intentionally absent from the authoritative core data model.

## 6. Agent Birth R1 semantics

Agent Birth moves to Agent Service as a provisioning/lifecycle protocol.

```text
BirthRequest
   |
resolve AgentDefinition + immutable AgentRevision
   |
bind AgentIdentity
   |
bind Plugin/Capability profile
   |
create AgentInstance
   |
create DesiredPlacement
   |
Service Reconciler -> Host/Runtime provider
   |
observe reachable/ready service carrier
   |
READY
```

Suggested lifecycle:

```text
REQUESTED
 -> DEFINED
 -> IDENTITY_BOUND
 -> CAPABILITIES_BOUND
 -> PLACEMENT_DESIRED
 -> PROVISIONING
 -> READY
 -> DRAINING
 -> RETIRED

terminal/error side state:
 FAILED / BLOCKED
```

The exact state names are not important; the invariant is that Birth distinguishes semantic provisioning stages from Host process presence and Runtime execution attempts.

## 7. Goal semantics

`Goal` is the objective/acceptance layer above Tasks.

```text
Goal
├── objective
├── owner (Agent/Team)
├── acceptance contract
├── child goals?
└── derived progress from tasks/evidence
```

Goal completion must be determined by its acceptance/verification contract, not by all child Runtime Jobs merely exiting zero.

A Goal hierarchy is optional. Do not force every tiny request into a deep objective tree.

## 8. Task semantics

`Agent Task` is an organization/service work unit.

```text
Task
  -> Assignment
      -> Agent Instance
          -> zero/one/many Runtime Jobs/Attempts
```

One Task may:

- need no Runtime Job (pure routing or external provider call);
- create one Job;
- retry the same Job identity through Attempts;
- create multiple Jobs for fan-out;
- move between Agents while retaining Task identity.

Therefore:

```text
Task semantic state != Runtime Job state
```

Suggested Task states:

```text
PROPOSED
READY
ASSIGNED
ACTIVE
WAITING
VERIFYING
SUCCEEDED | FAILED | CANCELLED
```

Runtime statuses are referenced as evidence, not reused as the Service Task state machine.

## 9. Assignment and scheduling

The minimal scheduler should initially be a policy function, not a new distributed scheduling platform.

Input:

```text
Task requirements
available Agent revisions/instances
capability/profile compatibility
Host/Runtime availability
identity/policy constraints
load/priority
```

Output:

```text
Assignment(taskId, agentInstanceId, revision)
```

Placement of the process itself is a separate decision:

```text
Assignment answers: WHO should do the work?
Placement answers: WHERE should the Agent carrier run?
Runtime Job answers: WHAT physical execution was admitted?
```

## 10. Desired state and reconciliation

Borrow the mature control-plane pattern:

```text
Service desired state
       |
append durable revision/event
       |
Reconciler
       |
Host/Runtime/provider API
       |
observed state
       |
compare / converge / report ambiguity
```

The reconciler must not convert missing observation into success.

Minimal reconciliation targets:

- Agent presence/retirement;
- assignment activation;
- endpoint/session reachability;
- provider revision convergence.

Do not make every domain object reconciled unless a real asynchronous desired/observed gap exists.

## 11. Service routing / Gateway

The Agent Service should own logical routing policy but preferably reuse mature gateway/proxy substrates.

```text
source AgentIdentity
       |
Service Router
       |
resolve target Capability / Agent
       |
Policy decision
       |
Protocol adapter
  +----+----+
  |    |    |
 A2A  MCP  HTTP/provider
       |
observed response/effect reference
```

Gateway invariants:

- discovery != authorization;
- model choice != authorization;
- direct bypass paths must be explicit and separately governed;
- credentials stay outside prompt/context;
- A2A and MCP share policy/identity semantics without being collapsed into one wire protocol.

## 12. Session / communication model

A Session is communication continuity, not Task or Agent identity.

Minimal contract:

```text
Session.open(participants, protocol, purpose?)
Session.send(sessionId, message)
Session.stream(sessionId)
Session.close(sessionId)
```

A2A should be one adapter for Agent-to-Agent sessions. Local/native Ordivon messages may use another carrier while preserving the same Service session/message identity.

## 13. Board semantics

Agent Board is a **projection**:

```text
ServiceEvents + authoritative objects
             |
          projector
             |
            Board
```

Board may display:

- Agent presence;
- Goal progress;
- Task queues;
- assignments;
- blocked/waiting work;
- Runtime evidence links;
- conversations/hand-offs;
- alerts.

Deleting/rebuilding Board storage must not delete Agent/Goal/Task truth.

## 14. Event and observability spine

A minimal append-only Service event stream should capture semantic transitions while OTel carries distributed execution telemetry.

```text
ServiceEvent
  -> who/what semantic aggregate changed
  -> old/new revision reference
  -> reason/provenance
  -> TraceId

OTel span
  -> distributed execution/request timing and technical telemetry
```

Do not create a private tracing system. Service events and OTel traces solve related but different problems.

## 15. Minimal interfaces

The R1 core can remain small:

```text
service.request.submit(request) -> ServiceRequest
service.request.get(id)

agent.define(spec) -> AgentDefinition
agent.version(definitionId, spec) -> AgentRevision
agent.birth(revisionId, birthSpec) -> AgentInstance
agent.get(instanceId)
agent.retire(instanceId)

goal.create(spec) -> Goal
goal.get(id)
goal.update(id, expectedRevision, patch)

task.create(spec) -> Task
task.assign(taskId, agentId) -> Assignment
task.cancel(taskId)
task.verify(taskId, evidenceRefs[]) -> semantic decision

a2a/session.open(spec) -> Session
session.send(id, message) -> MessageId
session.stream(id)

fleet.desire(agentId, placementSpec) -> DesiredPlacement
fleet.observe(agentId) -> observed state
fleet.reconcile(agentId) -> reconciliation receipt

board.project(query) -> projection
```

The actual MCP/API naming may differ; these names express responsibilities, not a committed wire format.

## 16. Runtime adapter contract

Agent Service should consume Runtime through a narrow adapter rather than knowing its internal Job schema everywhere.

```text
RuntimeAdapter.submit(TaskExecutionProposal) -> RuntimeExecutionRef
RuntimeAdapter.observe(RuntimeExecutionRef) -> RuntimeObservation
RuntimeAdapter.cancel(RuntimeExecutionRef) -> CancelReceipt
RuntimeAdapter.artifacts(RuntimeExecutionRef) -> ArtifactRef[]
```

The current Ordivon Runtime Job/Attempt identities remain authoritative on the execution side and are stored as foreign references in Assignment/Task evidence.

## 17. Host adapter contract

```text
HostAdapter.observe(hostOrCarrierRef) -> PresenceObservation
HostAdapter.ensure(desiredCarrier) -> EnsureReceipt
HostAdapter.wake(carrierRef) -> WakeReceipt
HostAdapter.retire(carrierRef) -> RetireReceipt
```

Host reports local continuity/presence. Service decides why that presence is desired.

## 18. Minimal build order

### Slice 1 — Registry + Birth + one local Runtime

1. Durable store for `AgentDefinition`, `AgentRevision`, `AgentInstance`, `ServiceEvent`.
2. Create immutable revision.
3. `agent.birth()` creates identity binding and desired placement.
4. Reconciler targets one existing Ordivon Host/Runtime adapter.
5. Observe AgentInstance as READY only after provider evidence.

### Slice 2 — Task -> Assignment -> Runtime

6. Add `Task` and `Assignment`.
7. Bind one Task to one READY Agent.
8. RuntimeAdapter admits execution and returns exact Runtime Job reference.
9. Service persists Job/Attempt evidence without equating process exit to Task success.
10. Explicit `task.verify()` decides semantic completion.

### Slice 3 — Communication and team behavior

11. Add Session/Message identity.
12. Add A2A adapter between two Agents.
13. Add capability/plugin profile resolution.
14. Add policy check before A2A/tool routes.

### Slice 4 — Fleet/control-plane behavior

15. Add HostRegistry and simple placement policy.
16. Add desired/observed reconciliation across two Host adapters.
17. Add Task reassignment with duplicate-effect safeguards.
18. Build Board as disposable projection from events/state.

### Slice 5 — external standards integration

19. MCP capability routes.
20. OTel trace linkage.
21. mature identity provider adapter.
22. mature policy engine adapter.

Only after these slices are proven should a more advanced scheduler, long-term memory, autoscaling or marketplace be considered.

## 19. Behavioral acceptance suite

The minimal kernel is not complete until all are demonstrated:

1. **Revision identity** — define Agent A, create A1 and A2; historical A1 remains resolvable and immutable.
2. **Birth convergence** — Birth A1; desired placement is durable before Host/Runtime action; READY is reached only from observed provider evidence.
3. **Birth recovery** — crash Agent Service after desired placement commit but before observation; restart and reconcile without creating a second semantic AgentInstance.
4. **Task/Job separation** — one Task creates a Runtime Job; Job exit zero alone leaves Task in VERIFYING until semantic verification passes.
5. **Retry identity** — a Runtime retry/Attempt does not create a new Agent Task.
6. **Cancellation** — cancelling Task requests Runtime cancellation but Service waits for observed execution state before finalizing physical execution status.
7. **No invented success** — Runtime/Host becomes unreachable after acceptance; Service records ambiguity/pending observation rather than marking Task complete.
8. **Harness neutrality** — replace Harness implementation for a new Agent revision without changing Agent Service Task/Goal/Session schemas.
9. **A2A route** — two Agents exchange one message through A2A while preserving source/target identity and SessionId.
10. **Policy deny** — denied Agent/capability route never invokes target Tool/Runtime endpoint.
11. **Credential separation** — downstream credential is issued/bound outside model prompt/context.
12. **Board rebuild** — delete Board projection and rebuild it from authoritative records/events with no loss of Task/Goal state.
13. **Host reassignment** — unavailable Host either leaves desired placement pending or reassigns under explicit policy; it never silently duplicates an irreversible Runtime effect.
14. **Restart durability** — Service restart preserves Agent/Goal/Task/Assignment identities and exact external Runtime references.
15. **Traceability** — one request can be traced `ServiceRequest -> Goal/Task -> Assignment -> Agent -> RuntimeJob/Attempt -> evidence -> semantic verification`.

## 20. What not to build in R1

Do not add by default:

- a universal long-term memory service;
- a custom IAM/identity protocol;
- a custom policy language/PDP;
- another generic durable workflow engine;
- another container scheduler;
- a private substitute for MCP or A2A;
- a Board database as source of truth;
- a second physical-execution ledger duplicating Runtime;
- a second Agent loop duplicating Harness;
- autonomous optimization/prompt mutation authority;
- enterprise marketplace/product UI.

## 21. Migration delta from current Ordivon documentation

Current migration/classification records still describe `Agent Birth` as part of the historical Harness semantic core/provisioning history. R1 proposes a narrower split:

```text
HISTORICAL
ordivon-harness
  -> Agent loop
  -> Agent Birth/provisioning

TARGET
Agent Service
  -> Agent Birth semantic provisioning/lifecycle
  -> Agent identity/revision/desired placement

Harness
  -> context/model/tool/subagent execution loop only
```

This is a migration proposal, not a silent rewrite of historical evidence. The historical docs should remain as provenance until the new Agent Service vertical slice passes and a dedicated migration record is committed.

## 22. Relationship to current `ordivon-control-plane` Agent Plugin

The existing `plugins/ordivon-control-plane` package merely exposes Runtime and Host MCP connections. It is **not** the future Agent Service control plane.

Keep the distinction:

```text
ordivon-control-plane Agent Plugin
  = portable client capability bundle for Runtime/Host MCP surfaces

Ordivon Agent Service
  = durable cluster/service authority described in this document
```

The plugin may later expose or compose an Agent Service endpoint, but it must not become the Service source of truth merely because its name contains `control-plane`.

## 23. Project-study acceptance

- **ONE-SENTENCE TEST: PASS** — Service authority is distinguishable from Host, Runtime and Harness.
- **MODULE-COMPLETENESS TEST: PASS** — every R1 responsibility has an owner and explicit non-owner boundary.
- **MINIMAL-CLONE SPEC TEST: PASS** — data model, interfaces, build order and provider adapters are sufficient to implement a first vertical slice.
- **BEHAVIORAL-ACCEPTANCE TEST: PASS (SPECIFIED, NOT YET IMPLEMENTED)** — 15 tests define proof of the architecture.

## Verdict

**BUILD ORDIVON AGENT SERVICE AS A HARNESS-NEUTRAL DURABLE CLUSTER CONTROL PLANE: keep semantic Agent/Goal/Task/Assignment/Session truth above Host and Runtime, use desired/observed reconciliation for lifecycle, and reuse standard identity, policy, MCP/A2A and telemetry substrates instead of absorbing them.**
