# Ordivon Agent Service — LEGO Node Graph R2

Status: NODE-DECOMPOSED IMPLEMENTATION SPEC
Base: `ordivon-agent-service-minimal-kernel-r1.md`
Method: `project-kernel-decomposition` + LEGO Node Graph Contract

## One-sentence model

**Ordivon Agent Service is a graph of small semantic authority, reconciliation, routing, identity, execution-adapter, verification, and projection nodes that together manage agent-cluster intent without absorbing Host, Runtime, or Harness responsibilities.**

## Level 0 — one composite node

```text
[Agent Service]
```

Fails Atomicity Gate because it owns multiple distinct authorities and effects. Split.

## Level 1 — major composite nodes

```text
[Registry & Revision]
[Birth & Identity]
[Goal / Task / Assignment]
[Fleet Desired State]
[Session / Routing]
[Policy / Capability]
[Runtime/Host Integration]
[Verification]
[Events / Projection]
```

Each still contains mixed responsibilities. Split again.

## Level 2 — first atomic kernel set

### Semantic state authorities

```text
N01 AgentDefinitionStore       STATE_AUTHORITY
N02 AgentRevisionStore         STATE_AUTHORITY
N03 AgentInstanceStore         STATE_AUTHORITY
N04 GoalStore                  STATE_AUTHORITY
N05 TaskStore                  STATE_AUTHORITY
N06 AssignmentStore            STATE_AUTHORITY
N07 SessionStore               STATE_AUTHORITY
N08 DesiredPlacementStore      STATE_AUTHORITY
N09 ServiceEventStore          STATE_AUTHORITY
```

### Decision / orchestration nodes

```text
N10 BirthCoordinator           DECISION_ROUTER
N11 AssignmentPlanner          DECISION_ROUTER
N12 ServiceRouter              DECISION_ROUTER
N13 SemanticVerifier           VERIFIER_OBSERVER
```

### Reconciliation nodes

```text
N14 PlacementReconciler        RECONCILER
N15 AssignmentActivator        RECONCILER
```

### Boundary / adapter nodes

```text
N16 IdentityAdapter            ADAPTER_GATEWAY
N17 PolicyAdapter              ADAPTER_GATEWAY
N18 HostAdapter                ADAPTER_GATEWAY
N19 RuntimeAdapter             ADAPTER_GATEWAY
N20 A2AAdapter                 ADAPTER_GATEWAY
N21 MCPAdapter                 ADAPTER_GATEWAY
```

### Observation / projection nodes

```text
N22 ProviderObserver           VERIFIER_OBSERVER
N23 BoardProjector             PROJECTION_SINK
N24 TraceBridge                PROJECTION_SINK
```

This is an R2 architectural atom set, not a claim that each node requires one process or package.

## Node contracts

### N01 AgentDefinitionStore

```text
Responsibility: own mutable definition metadata and references to immutable revisions.
Authority: AgentDefinition identity.
IN: define/update request + expected revision.
OUT: AgentDefinition snapshot/event.
Truth: yes.
Effect: no.
Replaceability: repository/store interface.
Acceptance: create definition, update with optimistic revision, stale update fails.
```

### N02 AgentRevisionStore

```text
Responsibility: own immutable AgentRevision records.
Authority: AgentRevision identity/content digest.
IN: frozen definition payload.
OUT: immutable revision reference.
Truth: yes.
Effect: no.
Acceptance: A1 remains byte/semantic stable after A2 exists.
```

### N10 BirthCoordinator

```text
Responsibility: coordinate semantic provisioning stages without owning provider execution.
Authority: no independent physical truth; orchestrates stores/adapters.
IN: BirthRequest + AgentRevision.
OUT: AgentInstance + DesiredPlacement intent.
Effect: delegated through adapters/reconciler.
Acceptance: retry after coordinator crash does not create duplicate semantic AgentInstance.
```

### N16 IdentityAdapter

```text
Responsibility: bind/resolve first-class Agent identity through an external identity provider.
Authority: delegated to identity provider.
IN: AgentInstance/Revision context.
OUT: AgentIdentity reference / scoped credential reference.
Effect: provider call.
Acceptance: identity remains distinct from user, Host, Task, and Runtime Job identities.
```

### N14 PlacementReconciler

```text
Responsibility: converge DesiredPlacement toward observed carrier presence.
Authority: owns reconciliation decision/progress, not Host truth.
IN: DesiredPlacement + ProviderObservation.
OUT: ensure/retire requests + reconciliation event.
Effect: through HostAdapter.
Acceptance: missing observation never becomes READY.
```

### N19 RuntimeAdapter

```text
Responsibility: translate TaskExecutionProposal into Runtime Job operations.
Authority: none over Runtime Job truth; Runtime remains authoritative.
IN: execution proposal / RuntimeExecutionRef.
OUT: submit/observe/cancel/artifact references.
Effect: Runtime calls.
Acceptance: Runtime retry Attempt never creates a new Service Task.
```

### N13 SemanticVerifier

```text
Responsibility: decide Service-level Task success from declared acceptance + evidence.
Authority: Task semantic completion decision.
IN: Task acceptance contract + evidence refs.
OUT: semantic verdict.
Effect: none beyond Task state update.
Acceptance: Runtime exit 0 alone does not force Task SUCCEEDED.
```

### N23 BoardProjector

```text
Responsibility: derive read/UI state from authoritative records/events.
Authority: none.
IN: ServiceEvents + snapshots.
OUT: Board read model.
Acceptance: delete projection and rebuild without losing semantic truth.
```

## Typed edge graph — Birth vertical slice

```text
BirthRequest
   |
   | DATA
   v
[N10 BirthCoordinator]
   | DATA                 | IDENTITY
   v                      v
[N02 AgentRevisionStore] [N16 IdentityAdapter]
   | DATA                 |
   +----------+-----------+
              |
              v
      [N03 AgentInstanceStore]
              |
              | CONTROL
              v
      [N08 DesiredPlacementStore]
              |
              | CONTROL
              v
       [N14 PlacementReconciler]
              |
              | EFFECT
              v
          [N18 HostAdapter]
              |
              | OBSERVATION
              v
       [N22 ProviderObserver]
              |
              | EVIDENCE
              +---------------------> [N14 PlacementReconciler]
```

Invariant: desired placement is committed before provider effect; READY requires observed provider evidence.

## Typed edge graph — Task execution slice

```text
[N05 TaskStore]
      |
      | DATA
      v
[N11 AssignmentPlanner]
      |
      | CONTROL
      v
[N06 AssignmentStore]
      |
      | CONTROL
      v
[N15 AssignmentActivator]
      |
      | EFFECT
      v
[N19 RuntimeAdapter] ----> Ordivon Runtime
      |
      | OBSERVATION / EVIDENCE
      v
[N22 ProviderObserver]
      |
      | EVIDENCE
      v
[N13 SemanticVerifier]
      |
      | CONTROL
      v
[N05 TaskStore]
```

Invariant: physical execution and semantic completion remain separate authorities.

## Typed edge graph — governed Agent-to-Agent route

```text
[N07 SessionStore]
      |
      | DATA + IDENTITY
      v
[N12 ServiceRouter]
      |
      +---- POLICY ----> [N17 PolicyAdapter]
      |                     |
      |<---- allow/deny -----+
      |
      +---- DATA ------> [N20 A2AAdapter] ---> remote Agent
      |
      +---- DATA ------> [N21 MCPAdapter] ---> capability/tool
```

Invariant: discovery/routing is not authorization; denied route never reaches effect adapter.

## Reusable LEGO assemblies extracted

### Revisioned registry brick

```text
DefinitionStore + immutable RevisionStore
```

Reusable for Agent, Plugin, Skill, Tool, policy bundle, deployment specs.

### Desired-state brick

```text
DesiredStateStore + Reconciler + Adapter + Observer
```

Reusable for Agent presence, deployments, service carriers, provider bindings.

### Durable work brick

```text
TaskStore + Assignment + Activator + EffectAdapter + Evidence
```

Reusable for research jobs, artifact jobs, media jobs, Agent organization work.

### Governed capability brick

```text
Router + Identity + Policy + ProtocolAdapter
```

Reusable across MCP, A2A, HTTP/provider calls.

### Semantic verification brick

```text
AcceptanceContract + EvidenceRefs + Verifier + SemanticStateStore
```

Reusable wherever mechanical success must not be confused with domain success.

### Projection brick

```text
Authoritative state/events + Projector + disposable read model
```

Reusable for Board, dashboards, search indexes, fleet views.

## Minimal clean-room subgraph for first implementation

Do not implement all 24 nodes first. The smallest useful connected graph is:

```text
N01 AgentDefinitionStore
N02 AgentRevisionStore
N03 AgentInstanceStore
N08 DesiredPlacementStore
N09 ServiceEventStore
N10 BirthCoordinator
N14 PlacementReconciler
N18 HostAdapter
N22 ProviderObserver
```

Optional identity stub for Slice 1:

```text
N16 IdentityAdapter -> deterministic local test provider
```

This proves the most important control-plane invariant before Task/Session/Gateway complexity is added.

## Slice 1 behavioral acceptance

1. create AgentDefinition and immutable A1 revision;
2. submit BirthRequest for A1;
3. create exactly one AgentInstance;
4. persist DesiredPlacement before Host effect;
5. simulate coordinator/reconciler restart;
6. resume convergence without duplicate AgentInstance;
7. HostAdapter reports observed carrier ready;
8. only then mark AgentInstance READY;
9. lose observation and record UNKNOWN/PENDING rather than invented success;
10. create A2 and prove A1 historical identity remains resolvable.

## Node-mode acceptance

```text
NODE-GRAPH COVERAGE: PASS
ATOMICITY GATE: PASS FOR R2 ARCHITECTURAL LEVEL
EDGE-TYPING: PASS
REASSEMBLY SUFFICIENCY: PASS FOR SLICE 1 SPEC
```

These markers mean implementation can begin from the graph without broad rediscovery. They do not claim the Agent Service code exists yet.
