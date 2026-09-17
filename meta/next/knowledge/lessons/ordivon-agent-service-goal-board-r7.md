# Ordivon Agent Service — Goal / DAG / Board Projection R7

Status: **IMPLEMENTED / LIVE HOST BOARD DOGFOOD / NOT YET CANONICAL CUTOVER**
Date: 2026-09-18
Base implementation: `9ad9fea48591c0c323aa234ca0365355e09e61b6`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r7-goal-board-delta.json`
Acceptance: `evidence/acceptance/agent-service-goal-board-r7.json`

## One-sentence result

**R7 adds durable Goal and Task-DAG semantics above the R5/R6 Task truth, derives readiness without duplicating Task state, and projects Goal events into Host Board as replay-safe collaboration records without making Board a second Goal/Task authority.**

## Why Goal sits above Task rather than Runtime

The lower slices already established:

```text
Agent carrier readiness      -> R3/R4
Task / Assignment / Runtime  -> R5
Evidence / semantic verdict  -> R6
```

R7 therefore defines Goal convergence only in terms of Task semantic truth:

```text
Goal
  ↓ contains
Task DAG
  ↓
existing Task execution/verification
  ↓
Task SUCCEEDED / FAILED
  ↓
GoalReconciler
```

Runtime Job status and Host Board messages do not participate in Goal truth.

## Goal state

R7 Goal state is minimal:

```text
PENDING
RUNNING
SUCCEEDED
FAILED
```

Derived convergence rules:

- any linked Task `FAILED` or `CANCELLED` -> Goal `FAILED`;
- all linked Tasks `SUCCEEDED` and at least one Task -> Goal `SUCCEEDED`;
- any linked Task has left `PENDING` -> Goal `RUNNING`;
- otherwise -> Goal `PENDING`.

Terminal Goal state cannot later be reinterpreted.

## Goal graph decomposed into four real LEGO bricks

The first R7 implementation used one `GoalTaskGraph` class. Tests passed, but the class still mixed four responsibilities. It was then decomposed without changing observable behavior:

```text
GoalGraphMutationGuard
  graph freeze law

GoalTaskLinkStore
  Goal <-> Task membership + stable order

TaskDependencyStore
  same-Goal dependency edges + cycle rejection

TaskReadinessProjector
  PENDING + all dependencies SUCCEEDED => ready
```

`GoalTaskGraph` remains only as a compatibility facade over these four objects. It owns no separate truth.

## Readiness is a projection, not another Task state

R7 deliberately does not add:

```text
Task READY
Task BLOCKED
```

as persistent states.

A Task remains `PENDING`; readiness is recomputed from:

```text
Task.state == PENDING
AND
all dependency Tasks == SUCCEEDED
```

This prevents a derived readiness cache from drifting away from Task/dependency truth.

## DAG mutation freezes at execution start

Graph structure may be built while the Goal and all linked Tasks remain `PENDING`.

Once either condition is false:

```text
Goal.state != PENDING
OR
any linked Task.state != PENDING
```

membership and dependency mutations fail closed.

This prevents adding a dependency after a Task is already running and retroactively changing the meaning of admitted execution.

## Dependency rules

R7 enforces:

```text
no self dependency
no cross-Goal dependency
no cycle
```

Cycle detection occurs before edge commit.

## Assignment remains one authority

R7 does not create a second AssignmentStore or scheduler. `GoalAssignmentPlanner` is a thin readiness gate:

```text
TaskReadinessProjector
  ↓ ready only
existing R5 AssignmentPlanner
```

Agent matching and Assignment identity remain R5 truth.

## Board is projection-only

Host v2's own Board contract explicitly defines messages as collaboration records rather than Task priority, execution authority, owner standing, or domain truth.

R7 aligns with that contract:

```text
Goal semantic event
  ↓
GoalBoardProjector
  ↓ deterministic clientMessageId
HostBoardMcpAdapter
  ↓
Host board.post
```

The Board message itself says:

```text
Projection only; Agent Service remains the semantic Goal/Task authority.
```

A Host Board write failure never rolls back Goal state or Goal semantic events.

## Deterministic projection identity

Each Goal ServiceEvent maps to:

```text
clientMessageId =
agent-service-goal-event-v1:<sha256(ServiceEvent.id)>
```

If Host commits the Board message but the Agent Service loses the response before persisting its local projection receipt, retry uses exactly the same `clientMessageId` and payload.

Host then returns `admission=existing` rather than creating a duplicate collaboration message.

## BoardProjectionReceiptStore

Agent Service persists only delivery acknowledgement:

```text
ServiceEvent.id
Goal.id
clientMessageId
provider sequence
```

The receipt does not redefine Goal state. Host Board does not become a Goal event store.

## Catch-up semantics

The initial `project_latest()` implementation could skip intermediate Goal events if the projector was offline. R7 therefore adds `project_pending(goalId)`.

It iterates the complete Goal event sequence in order and for each event:

- returns the existing local projection receipt if already delivered;
- otherwise posts using the event's deterministic identity;
- stops naturally on provider failure, allowing replay from that same event later.

Messages use the event-specific semantic state, not the current Goal state masquerading as historical state.

## Host provider integration

Production Host v2 exposes a loopback-only stateless Streamable HTTP MCP server:

```text
http://127.0.0.1:8898/mcp
```

R7 reads the endpoint components from `/etc/ordivon/host-v2.env` and rejects non-loopback or non-streamable-http configuration.

`HostBoardMcpAdapter` exposes only `BoardAdapter.post()`. Its HTTP client keeps generic Tool invocation private; Agent Service R7 does not route Goal/Task state through Host `task.*` tools and does not use Host News tools.

## Live Host proof

A post-refactor acceptance Goal was converged locally to `SUCCEEDED` and projected through the actual Host v2 MCP.

Projection identity:

```text
clientMessageId:
agent-service-goal-event-v1:df096a466a8464ba023c67d9f9749582147183f8d4b7182fde0c678a3923c7fc

Host Board sequence: 17722
```

Exact `board.list(clientMessageId=...)` re-entry returned one message with:

```text
messageKind = note
topic = agent-service-goal-projection
truthRole = coordination-message-not-domain-truth
```

The exact same `board.post` payload was then replayed. Host returned:

```text
admission = existing
sequence = 17722
```

No duplicate message was created.

## R7 architecture result

```text
GoalStore
   ↓
GoalTaskLinkStore
   +
TaskDependencyStore
   ↓
TaskReadinessProjector
   ↓
DependencyAwareAssignmentPlanner
   ↓
R5/R6 Task execution + verification
   ↓
GoalReconciler
   ↓ semantic Goal event
BoardProjector
   ↓
HostBoardMcpAdapter
   ↓
Host Board collaboration record
```

Board can be unavailable while Goal/Task truth continues to advance. Catch-up restores the projection later.

## Next decomposition boundary

The remaining R2 cluster-management blocks are now much clearer:

```text
N07 SessionStore
N12 PolicyEvaluator
N16 AgentIdentityAdapter
N17 CapabilityRegistryAdapter
N20 McpRouterAdapter
N21 A2aRouterAdapter
N24 AuditProjector
```

The next useful slice should not be another monolithic router. It should first separate **Agent identity**, **advertised capability**, **session/conversation continuity**, and **delegation envelope**, then plug MCP and A2A in as transports over those semantic objects.
