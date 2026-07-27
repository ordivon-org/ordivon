# Architecture

## Architectural objective

Build the smallest system in which persistent Agent cognition can influence a deterministic game world through typed, observable, verifiable effects.

The implementation should reuse Ordivon concepts without coupling the game to a remote MCP round trip for every in-world action.

## Components

### 1. Web client

Owns:

- station map and status presentation;
- player input;
- Agent requests and reports;
- goal, authority, and tool configuration;
- timeline, task graph, and replay views.

It does not own authoritative world state.

### 2. Game World Kernel

Owns:

- authoritative clock and turn ordering;
- map topology and locations;
- resources and conservation rules;
- inventory and ownership;
- health, hazards, and equipment state;
- legal typed actions and preconditions;
- deterministic action resolution;
- mission success, failure, and score;
- snapshots and replayable world events.

Candidate actions include:

```text
observe
move
communicate
carry
use_tool
isolate_system
repair
run_test
treat
open_or_close_access
request_authority
evacuate
```

### 3. Game Host

A game-focused adapter over Ordivon Host concepts. It owns:

- persistent Agent and mission Goals;
- Task nodes and readiness;
- bounded Context compilation;
- provider invocation;
- structured candidate decisions;
- decision admission against current world state;
- unresolved action tracking;
- task outcomes and continuation.

The first implementation may share one process and SQLite database with the world kernel while preserving clear module and schema boundaries.

### 4. Semantic boundary

Adapts the relevant Ordivon Computing primitives:

```text
WorldObjectRef
Effect
Dispatch
Observation
Artifact
Verification
Fact
Authority / Capability reference
```

It is responsible for stable semantic identities and evidence, not frame-level simulation.

### 5. Runtime and provider adapters

Ordivon Runtime is initially used for:

- long-running simulation experiments;
- batch scenario execution;
- retained logs and replay artifacts;
- cancellation and recovery tests;
- conformance and regression workloads.

Production in-world actions use a local world adapter. External model calls use replaceable provider adapters and do not own task continuity.

## State ownership

| State | Authority |
|---|---|
| map, resources, health, equipment | Game World Kernel |
| Agent goals and task frontier | Game Host |
| candidate model output | immutable provider result |
| admitted semantic action | Host + semantic journal |
| concrete world transition | Game World Kernel |
| observation and verification receipt | semantic boundary |
| UI projection | Web client cache |

No state may have two independent authorities.

## Decision cadence

The system uses three control frequencies:

```text
high level — model / Host
mission goals, plans, exceptions, negotiation

middle level — deterministic controller
path selection, ordered procedures, routine work

low level — world and rendering loop
turn updates, timers, damage, resource changes, animation
```

A model call should be triggered by a meaningful frontier or exception, not by every turn or movement step.

## Main execution path

```text
1. World emits bounded observations for an Agent.
2. Host compiles current Goal, ready Tasks, relevant memory, authority, and observations.
3. Provider returns structured candidate decisions.
4. Host checks identity, freshness, legality, unresolved work, and allowed candidates.
5. An admitted decision proposes an Effect.
6. The world adapter binds the Effect to one typed action and Dispatch.
7. Game World Kernel checks preconditions and resolves the action.
8. The result produces immutable Observation and optional Artifact evidence.
9. Verification evaluates declared completion conditions.
10. Host advances, waits, replans, or terminates the Task.
```

## Minimum persistent identities

- MissionId
- AgentId
- GoalId
- TaskId
- WorldObjectId
- EffectId
- DispatchId
- ObservationId
- VerificationId
- ArtifactId
- WorldRevision

## Determinism and replay

The world kernel must support deterministic replay from:

```text
initial scenario snapshot
+ admitted world commands
+ explicit random seed
```

Model outputs do not need to be reproducible, but admitted decisions and their exact input context must be retained. A replay can therefore reproduce the world trajectory even when cognition cannot be regenerated identically.

## Safety and fairness boundaries

- Untrusted dialogue never becomes a control instruction automatically.
- World observations and system instructions use separate typed channels.
- Agent capability is enforced by the world adapter.
- Model/provider choice cannot alter resource rules or scoring.
- The same scenario evaluation uses bounded and recorded inference budgets.
- An uncertain Dispatch blocks duplicate mutation until reconciled.

## Initial deployment shape

Prefer one local development service with modular boundaries:

```text
apps/web
packages/world
packages/host
packages/protocol
packages/simulation
```

Do not split into network services until measured workload or independent deployment demands it.
