# Ordivon Agent Service — Slice 1 Clean-Room Kernel R3

Status: **IMPLEMENTED / LOCAL PROVIDER SEAM / NOT YET CUT OVER**
Date: 2026-09-17
Base architecture: `knowledge/graphs/ordivon-agent-service-r2.json`
Acceptance receipt: `evidence/acceptance/agent-service-slice1-r3.json`

## One-sentence result

**The first Ordivon Agent Service vertical slice now implements durable revisioned Agent birth and desired/observed placement reconciliation as nine small LEGO nodes, proving the R2 architecture can be rebuilt from its graph without folding Host execution or Harness cognition into Service authority.**

## Implemented node set

```text
N01 AgentDefinitionStore
N02 AgentRevisionStore
N03 AgentInstanceStore
N08 DesiredPlacementStore
N09 ServiceEventStore
N10 BirthCoordinator
N14 PlacementReconciler
N18 HostAdapter          # contract only; test provider used in R3
N22 ProviderObserver
```

Composition root:

```text
agent_service.slice1.AgentServiceSlice1
```

Persistence is deliberately minimal: Python standard-library SQLite. This is a clean-room proof of the state/transaction contracts, not a commitment that SQLite is the production Agent Service database.

## Executable flow

```text
AgentDefinition
      |
      v
immutable AgentRevision
      |
      v
BirthCoordinator
      |
      +--> AgentInstance(PROVISIONING)
      |
      +--> DesiredPlacement(READY/UNKNOWN)
      |
      +--> AGENT_BIRTH_REQUESTED event
      |
      v
PlacementReconciler
      |
      | ensure(effect request)
      v
HostAdapter
      |
      | observe(provider fact)
      v
ProviderObserver
      |
      +-- UNKNOWN --> keep/revoke semantic READY
      |
      +-- READY ---> atomic AgentInstance READY + AGENT_READY event
```

## Proven invariants

1. Agent revisions are immutable and historical revisions remain resolvable after newer revisions exist.
2. `birth_request_id` is an idempotency identity: replay returns the same AgentInstance; replay against a different revision fails closed.
3. AgentInstance + DesiredPlacement + birth event are persisted before any Host effect is requested.
4. Desired state never counts as observed readiness.
5. Provider `UNKNOWN` cannot produce semantic `READY`.
6. Service restart can recover the same birth identity and continue reconciliation without duplicating AgentInstance.
7. READY semantic state and `AGENT_READY` event commit atomically.
8. Loss of provider readiness revokes semantic READY and appends `AGENT_READINESS_LOST`.
9. Provider observation state may persist independently from semantic transition, allowing safe retry after a semantic transaction failure.

## Important authority boundary

R3 intentionally uses a `HostAdapter` interface and a deterministic test implementation. It does **not** yet call the real Ordivon Host MCP.

This is deliberate:

```text
Agent Service
  owns desired Agent presence + semantic Agent state

Host
  owns local carrier/presence observations and wake/ensure effects

Runtime
  remains outside Slice 1; it owns physical Job/Attempt execution
```

The next integration step should implement the existing Host as a provider behind `HostAdapter`, without moving Host truth into SQLite and without changing Birth/Placement semantics.

## TDD evidence

The implementation followed red-green cycles:

- initial RED: `agent_service` module absent;
- GREEN: seven core Slice 1 behaviors;
- RED: semantic state could commit before event history;
- GREEN: state + event moved under one transaction seam;
- RED: readiness loss changed state silently;
- GREEN: `AGENT_READINESS_LOST` added atomically.

Fresh verification after the final test fixture cleanup:

```text
Slice 1: 9 tests, 0 failures
Repository: 42 tests, 0 failures
ResourceWarning treated as error: PASS
compileall: PASS
git diff --check: PASS
```

## What R3 does not claim

- no production Agent Service deployment exists yet;
- no real Host provider has been connected;
- no Runtime Task/Job mapping exists yet;
- no Agent Identity provider exists yet;
- no Goal/Task/Assignment semantics are implemented yet;
- no A2A/MCP routing path is implemented yet;
- no Board projector is implemented yet.

## Next LEGO slice

The least-coupled next move is **Host provider integration**, not Slice 2 expansion:

```text
existing Ordivon Host
       |
       v
RealHostAdapter
       |
       v
existing R3 PlacementReconciler
```

Acceptance should prove that replacing the fake provider with the real Host requires no changes to the nine-node semantic kernel.

Only after that boundary is proven should R4 add:

```text
TaskStore -> AssignmentPlanner -> AssignmentStore
          -> AssignmentActivator -> RuntimeAdapter
          -> ProviderObserver -> SemanticVerifier
```
