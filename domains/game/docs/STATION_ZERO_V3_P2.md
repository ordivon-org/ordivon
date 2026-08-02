# Station Zero v3 — P2 durable Turn execution

## Status

P2 implements and verifies the sole durable execution path for the frozen Station Zero v3 encounter.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
World schema: 3
Reducer: complete
SQLite Turn persistence: complete
Embedded Host lifecycle: complete
Crash recovery and replay: complete
Bounded Mission Control projection: complete
Product registration: deferred
Agent planning and browser play: deferred
```

The current product still executes only `station-zero@2 / station-zero-core@3`. P2 does not register v3 in `src/registry.ts`, add public HTTP routes, alter the current browser, or invoke a cognition Provider.

## Responsibility split

P2 preserves the existing ownership boundary rather than creating another generic runtime.

### Station Zero v3 domain owns

- Genesis and current World Head;
- Planning Heads;
- one immutable Faction Plan per faction and Planning Head;
- one canonical Turn Batch;
- deterministic reducer execution;
- World Events and Turn Records;
- faction Knowledge and bounded player projection;
- replay and recovery from domain evidence.

### Embedded Host owns

- Task identity;
- Effect and executor request artifacts;
- Dispatch identity and idempotency key;
- Observation;
- Verification Receipt;
- Task Outcome;
- Host Journal integrity.

### Providers do not own

- World state;
- Planning state;
- Task continuity;
- commitment identity;
- retry policy;
- completion claims.

## Durable lifecycle

One Turn follows this retained lifecycle:

```text
open Planning Head
→ submit Rescue Plan
→ submit Pirate Plan
→ submit Swarm Plan
→ freeze canonical Turn Batch
→ prepare one Host Task / Effect / Dispatch
→ deliver the original Batch to the World executor
→ atomically retain World Event + Turn Record + World Head
→ observe the retained World result
→ retain Host Observation + Verification + Outcome
→ permit the next Planning Head
```

The player and Agent planning interfaces may submit Plans in any order. Submission order is not authoritative.

## Stable identities

All identities derive from the Run and source World revision.

```text
planning:station-zero-v3:<run>:r<revision>
turn-batch:station-zero-v3:<run>:r<revision>
task:station-zero-v3:<run>:r<revision>
effect:station-zero-v3:<run>:r<revision>
dispatch:station-zero-v3:<run>:r<revision>
```

The same source revision cannot produce a second Planning Head, Turn Batch, Task, Effect, or Dispatch identity.

An uncertain execution is observed using these original identities. It is never retried under a new ID.

## Planning Head

A Planning Head binds:

- Run identity;
- source World revision and Turn;
- source World digest;
- commitment-phase World digest;
- Standing Order revision;
- Planning revision;
- submitted Faction Plan digests;
- canonical Turn Batch digest;
- Host Task, Effect, and Dispatch identities;
- lifecycle state.

Planning lifecycle:

```text
open
→ committed
→ resolved
```

### `open`

Faction Plans may be submitted. Each faction has exactly one immutable Plan slot.

Re-submitting identical content is idempotent. Reusing the faction slot for different content fails closed.

### `committed`

All three Plans have been canonicalized into one Turn Batch. No Plan can be replaced.

### `resolved`

The authoritative World Event, Turn Record, and new World Head have committed atomically.

## Canonical Turn Batch

P2 exposes `canonicalizeStationZeroV3TurnBatch()` as the sole canonicalization function used by both the reducer and persistence layer.

Canonical ordering is:

1. Rescue, Pirate, Swarm;
2. Commander Action identity;
3. Actor identity;
4. Intent identity.

Equivalent Plan submission order produces the same:

- Batch content;
- Batch digest;
- World Event digest;
- Turn Record digest;
- final World digest.

Turn admission also rejects duplicate Intent or Commander Action identities across factions, preventing one Resolution map key from representing two committed operations.

## SQLite authority

P2 adds Station Zero v3-specific tables without changing the current executable tables.

```text
station_zero_v3_genesis
station_zero_v3_world_heads
station_zero_v3_planning_heads
station_zero_v3_faction_plans
station_zero_v3_turn_batches
station_zero_v3_world_events
station_zero_v3_turn_records
```

The existing compatible `runs` table supplies Run identity and allows the existing Host Journal foreign-key contract to remain unchanged.

### Rebuildable state

`station_zero_v3_world_heads` is a materialized current head. It can be rebuilt from:

```text
Genesis
+ ordered Turn Records
```

Planning Heads, canonical Batches, World Events, Turn Records, and Host Journal entries are retained authority, not caches.

## Atomic World commit

One accepted Turn commits in one `BEGIN IMMEDIATE` transaction:

1. deterministic reducer execution;
2. World Event insertion;
3. Turn Record insertion;
4. World Head replacement;
5. Planning transition to `resolved`;
6. Run status update.

Faults before commit roll back every item above.

There is no state where an Event is authoritative without its Record, or where the World Head advances without both evidence streams.

## World Event and Turn Record streams

P2 retains two aligned hash chains.

### World Event

The World Event contains the bounded domain summary:

- source and resulting World revisions;
- source and resulting Turn numbers;
- World digests;
- commitment digest;
- Resolution digest;
- Turn Record digest;
- Intent status counts;
- encounter status and reason;
- per-faction outcomes;
- Task and Dispatch identity.

### Turn Record

The Turn Record retains the complete deterministic proof:

- canonical Batch;
- every Intent Resolution;
- every Fact;
- faction-local Observations;
- before-state digest;
- after-state digest;
- Record digest.

The Event stream and Record stream must have identical sequence, Planning identity, Batch identity, and cross-digests.

## Host lifecycle

P2 reuses `EmbeddedHostAuthority` and `HostContractStore`.

One Turn creates:

```text
TaskDescriptor
→ DispatchEnvelope
→ ObservationEnvelope
→ VerificationReceipt
→ TaskOutcome
```

The Dispatch binds:

- exact Turn Batch request digest;
- exact source World digest;
- exact Planning commitment digest;
- executor identity;
- Batch identity as idempotency key.

The Verification Receipt contains one item per committed Intent. An Intent may be tactically interrupted, contested, or invalidated while its authoritative execution remains correctly verified.

Host completion therefore verifies the retained reducer result; it does not rewrite tactical success.

## Failure and recovery semantics

### Failure before World commit

Injected failure after Event insertion, Record insertion, or Head update rolls the whole transaction back.

Result:

```text
Planning remains committed
World revision remains unchanged
Event count remains unchanged
Record count remains unchanged
```

The original prepared Turn may be delivered again because no effect committed.

### Response loss after World commit

The World may commit successfully while the caller receives no response.

Recovery:

```text
observe original Turn Batch identity
→ read retained Event and Record
→ verify deterministic replay
→ retain Observation / Verification / Outcome under original Dispatch
```

No duplicate World effect occurs.

### Host incomplete after World commit

A resolved World Turn may still have a Host Task in `reconciling` state. Recovery reconstructs the exact expected Host objects and idempotently fills the missing stages.

A new Planning Head is not opened until the previous Turn has an authoritative World result and the original Host Task reaches `completed`.

### Restart before Host preparation

A committed Planning Head and canonical Batch survive restart. P2 recreates the same Task, Effect, request, and Dispatch identities from retained domain state.

### Corruption

Recovery fails closed on:

- missing or discontinuous Event / Record sequence;
- hash-chain divergence;
- Event / Record count mismatch;
- Planning / Batch / Event / Record identity mismatch;
- malformed or re-bound Batch content;
- tampered Planning content;
- divergent World Head;
- Genesis mismatch;
- deterministic replay mismatch;
- Host Journal corruption;
- retained Host objects that differ from the expected lifecycle.

## Historical verification

Historical Planning and Plan validation uses the World state reconstructed at that Planning revision, not the latest World Head.

For every retained Turn, recovery verifies:

```text
historical World state
→ Planning source digest
→ commitment digest
→ three admitted Faction Plans
→ canonical Batch
→ Event
→ Turn Record
→ deterministic reducer replay
→ resulting World state
→ Host lifecycle
```

This allows multi-Turn Runs to be verified without treating old Plans as if they targeted the current World.

## Bounded Mission Control projection

`createStationZeroV3MissionControlView()` is a pure read model.

It exposes:

- Run and World head identity;
- Planning readiness;
- submitted and missing factions;
- resource telemetry;
- exact own-faction Actors;
- player-faction objectives;
- known Rooms, Zones, Systems, Hazards, Items, and reports;
- enemy contacts only through player-faction Knowledge;
- bounded Host execution state;
- visible Fact identities from the latest player Observation.

It does not expose:

- hidden enemy positions;
- hidden health values;
- hidden inventory;
- hidden Systems, Hazards, or Items;
- raw SQLite rows;
- raw reducer mutation controls;
- another source of World truth.

## P2 implementation

```text
src/station-zero-v3/p2-model.ts
src/station-zero-v3/persistence.ts
src/station-zero-v3/executor.ts
src/station-zero-v3/turn-service.ts
src/station-zero-v3/mission-control.ts
```

`EmbeddedHostAuthority` now accepts any owner exposing the shared `DatabaseSync`, allowing both the current `GameStore` and the v3 Store to reuse the same Host authority without introducing a new Host implementation.

## P2 tests

`test/station-zero-v3-persistence.test.ts` verifies:

1. Planning Head idempotency and CAS;
2. immutable one-Plan-per-faction slots;
3. canonical Batch identity;
4. complete durable Turn and Host lifecycle;
5. response-loss observation under the original identity;
6. atomic rollback at multiple pre-commit fault points;
7. after-commit recovery without redelivery;
8. missing World Head reconstruction;
9. divergent and tampered evidence rejection;
10. submission-order independence;
11. Knowledge-limited Mission Control projection;
12. cross-faction identity collision rejection;
13. restart after commitment but before Host preparation;
14. aligned multi-Turn World and Host recovery;
15. blocking the next Planning while the prior World result is absent;
16. reconciling a response-lost result before opening the next Planning;
17. canonical Batch and Planning tamper detection;
18. independently retained Faction Plan tamper detection.

## Deferred to P3

P2 proves the durable authority path but does not yet make v3 a playable product.

P3 should add the bounded planning layer:

```text
player Commander Orders
→ Rescue specialist Agent Plans
→ Pirate Captain Plan
→ Hive Alpha Plan
→ deterministic policy-unit expansion
→ canonical durable Turn execution
→ Mission Control v3 interaction
```

P3 must also provide a first-playable product journey before v3 registration:

- player-visible Situation and uncertainty;
- Commander Ability and Standing Order controls;
- explainable Agent intent previews;
- one explicit Commit boundary;
- bounded Turn aftermath;
- recovery after process restart;
- no raw reducer stepping;
- no omniscient enemy projection;
- no model-owned World state.
