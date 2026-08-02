# Architecture

## Objective

Ordivon Game connects uncertain Agent cognition to a deterministic, persistent game world without allowing model output to become authoritative reality.

The repository supports one executable architecture:

```text
Mission Control
→ Station Zero Team domain
→ Embedded Host authority
→ Game World
→ SQLite evidence
→ Replay / Diagnosis / Comparison
```

It runs as one local Node.js process with one SQLite database. Module boundaries are semantic ownership boundaries, not network services.

## Final executable contract

```text
Scenario: station-zero@2
Ruleset: station-zero-core@3
World schema: 2
Actors: Engineer, Medic, Security
Maximum coordinated specialists: 3
```

Unknown Scenario or Ruleset versions fail closed. The repository contains no previous reducer, single-Agent execution stack, compatibility API, or database migration path.

## State ownership

| State | Sole authority |
|---|---|
| map, actors, crew, inventory, systems, hazards, resources | Game World |
| World revision, simulation Tick, mission result | Game World |
| Commands, Events, snapshots, hash chains | GameStore |
| actor Tasks, Messages, Decisions, Grants, Proposals, Rounds | Team domain |
| Task, Effect, Dispatch, Observation, Verification, Outcome | Embedded Host authority |
| provider output | immutable cognition record |
| player view and forecasts | Mission Control projection |
| replay, diagnosis, comparison | pure projection over retained evidence |

No layer may create a second source of truth for another layer's state.

## World transition

The authoritative reducer accepts either a primitive command or an atomic multi-Actor Tick:

```text
WorldState(revision N)
+ TickBatch(expected revision N)
→ validate identities, capabilities, preconditions, and conflicts
→ reserve shared resources
→ apply compatible intents atomically
→ advance environment once
→ evaluate terminal state once
→ verify invariants
→ WorldState(revision N+1) + TickEvent
```

Every accepted Tick advances one World revision and one simulation Tick. Conflicting mutable targets, duplicate actors, duplicate command identities, stale revisions, and over-allocated inventory fail without partial mutation.

### World invariants

- room adjacency is symmetric;
- every actor, crew member, system, and hazard references an existing room;
- item quantities are conserved across rooms, actors, and consumed ledgers;
- battery charge plus consumed energy equals initial energy;
- health, oxygen, heat, and integrity remain bounded;
- running missions have no terminal reason;
- terminal missions have an explicit reason.

## Team domain

Engineer, Medic, and Security have distinct capabilities and actor-local observations. Team coordination owns:

- persistent actor Tasks;
- bounded typed Context blocks;
- local and station-radio Messages;
- Provider decisions and admitted Proposals;
- attribute-based authority;
- exact, expiring, single-use Grants;
- deterministic legal-subset selection;
- Round and TickPlan persistence;
- interruption reconciliation.

The Station Zero selector intentionally supports no more than three specialists. It is a domain policy, not a general scheduler.

## Embedded Host authority

`src/host-contract/` provides the one generic commitment path retained in Game:

```text
TaskDescriptor
→ Effect
→ Dispatch
→ Observation
→ VerificationReceipt
→ TaskOutcome
```

Completion requires an accepted VerificationReceipt. Stable identities make response-loss recovery idempotent: after uncertainty, the system observes retained World evidence before considering redelivery.

This adapter is deliberately thin. Generic Agent sessions, planning loops, strategic Operations, and alternative Host implementations do not live in this repository.

## Provider boundary

Fixture, Codex, Hermes, and bounded fallback chains implement one Team Provider contract. Providers receive actor-specific Context and return one structured candidate identity or abstention.

Provider isolation guarantees that cognition cannot:

- read or mutate the repository or database;
- alter World rules or scoring;
- invent an actor or candidate;
- bypass authority;
- claim completion;
- own task continuity.

Technical Provider failure may trigger a configured fallback. A valid admitted choice is never replaced because another Provider might choose better.

## Mission Control

Mission Control is a pure bounded product projection over World, Team, Host, deployment, and replay evidence. It owns no independent database.

The default player cadence is intervention-driven:

```text
run ordinary verified work
→ stop at authority, conflict, provider failure, block, budget, or terminal outcome
→ show exact next-Tick forecast and Mission Fronts
→ accept player command
→ continue from durable state
```

Reads must not create semantic events or mutate Team state.

## Persistence and replay

SQLite retains:

- final Run identity;
- canonical Tick Commands and Events;
- before/after digests;
- command and event hash chains;
- sparse snapshots as caches;
- Team and Host journals;
- immutable deployment manifests.

Recovery begins from the newest valid snapshot and replays the tail. Full verification begins from Genesis and checks the complete retained history. Snapshot deletion cannot destroy truth; corrupted snapshots or journal chains fail closed.

Replay, diagnosis, and comparison are derived views. They never write a second history.

## HTTP surface

The service exposes only current product responsibilities:

- Run listing;
- Provider readiness;
- Mission Control;
- replay timeline/report/frame;
- deployment manifest;
- compatible Run comparison;
- browser assets.

Primitive World mutation, raw Team stepping, single-Agent control, and debug compatibility endpoints are not part of the executable.

## Repository constraints

New permanent structure must own a responsibility that the current modules cannot safely own locally. A second materially different world is required before Station Zero mechanisms are generalized into a reusable Game platform.
