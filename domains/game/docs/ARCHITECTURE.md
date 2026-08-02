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

### Advancement hot path

Mission advancement distinguishes internal progress from player-facing projection:

```text
TeamHost Step Receipt
→ local boundary decision
→ continue without rebuilding the full product view
→ build Mission Control View only for an actual intervention, budget boundary, or terminal result
```

A Step Receipt carries the current World revision, mission status, Round status, and blocker. Full Mission Control views remain pure projections, but are no longer rebuilt after every Context, Proposal, Dispatch, Observation, and Verification stage.

One Run has one active Mission writer. Identical concurrent advance requests share the same in-flight result; a different advance or player mutation fails closed until that writer finishes. Different Runs may overlap external Provider cognition while SQLite serializes their short durable checkpoints.

## Persistence and replay

SQLite retains:

- final Run identity;
- canonical Tick Commands and Events;
- before/after digests;
- command and event hash chains;
- sparse snapshots as caches;
- Team and Host journals;
- immutable deployment manifests.

Recovery begins from the newest valid snapshot and replays the tail. A successful recovery establishes a verified in-memory World Head. Normal current-state reads compare that Head with the latest retained Command/Event digest and return it directly; a mismatch invalidates the Head and triggers recovery. Full verification still begins from Genesis and checks the complete retained history. Snapshot deletion cannot destroy truth; corrupted snapshots or journal chains fail closed.

Hot-path validation and deep audit are intentionally separate:

| Boundary | Validation |
|---|---|
| current read | latest sequence and retained Head digests |
| Team transition | identity, revision CAS, lease, and projection-head digest |
| Effect preparation | required World revision/digest and idempotency key |
| Effect observation | retained World Event and Observation binding |
| Round completion | VerificationReceipt and terminal projection heads |
| recovery / explicit audit | complete World streams, Host Journal, Contracts, and Replay |

Host Contract events remain authoritative in the Host Journal. `host_contract_entries` is a rebuildable materialized index written in the same transaction and point-validated against Journal and Artifact evidence before use. It is not a second history.

Team Projection tables retain complete current objects. Lifecycle Journal events retain compact object identity, revision, and digest heads rather than copying the complete object at every transition. Readers accept existing full-object events and the compact head form, preserving retained Run compatibility.

Large Artifact bodies and non-Contract Journal payloads use transparent gzip storage when it is smaller. Digests continue to bind canonical logical content, and public read APIs return the original JSON objects.

Durable Team work uses short checkpoint transactions around Context preparation, Provider result admission, Tick planning, Dispatch preparation, post-Effect Observation, and Verification. Provider calls and World Effects remain outside long Host transactions.

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
