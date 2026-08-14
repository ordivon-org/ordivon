---
schema_version: 1
id: game.station-zero-v3.reducer
title: Station Zero v3 — P1 deterministic Turn reducer
type: reference
profile: engineering
lifecycle: accepted
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
updated: 2026-08-03
summary: Accepted target reference for the unregistered Station Zero v3 deterministic Turn reducer, ordering, combat, interaction, environment, knowledge, outcomes, and pure replay.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero-v3-unregistered
related:
  - game.station-zero-v3.encounter
  - game.station-zero-v3.execution
  - game.authority
---
# Station Zero v3 — P1 deterministic Turn reducer

## Scope

This reference defines the pure deterministic reducer that resolves one complete v3 Turn from a frozen World revision and one admitted plan per faction.

## Contract

The reducer validates Turn identity and faction plans, applies the fixed resolution order, resolves movement, reactions, combat, interaction, commander actions, environment, cleanup, objectives, outcomes, knowledge, World Events, and Turn Records, and produces replayable deterministic output without persistence or Provider calls.

## Errors

Stale revisions, invalid topology, unknown or duplicate identities, unauthorized actors or abilities, hidden targets, over-budget plans, conflicting content, and invariant violations fail before an authoritative partial result can escape.

## Compatibility

The reference applies only to the unregistered v3 encounter and Ruleset target. P2 persists and executes this reducer unchanged; public compatibility begins only after v3 registration replaces the current executable contract.

## Status

P1 implements and verifies the pure authoritative reducer for the frozen Station Zero v3 encounter.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
World schema: 3
Execution status: pure reducer and replay complete
P2 durable Game-owned persistence/execution: complete
P3 player/Agent planning and /v3 first-playable: complete
Current executable replacement: deferred
```

The root product still executes only `station-zero@2 / station-zero-core@3`. P1 remains the sole deterministic rules boundary; P2 adds durable execution and P3 adds the separate playable planning surface documented in [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md) and [`STATION_ZERO_V3_P3.md`](STATION_ZERO_V3_P3.md).

## Responsibility

`src/station-zero-v3/reducer.ts` owns one responsibility:

> Given one admitted World head and one complete three-faction Turn Batch, produce exactly one deterministic next World state, one Resolution for every committed Intent, faction-local observations, and one content-addressed Turn Record.

It does not own:

- player draft state;
- Agent cognition;
- Provider sessions;
- durable commitment identity;
- retries or crash recovery;
- product projections;
- UI controls.

Those concerns are implemented by the P2 durable execution boundary.

## Commit boundary

A Turn is admitted only when:

- the input World satisfies every v3 invariant;
- the Encounter is running and in `commitment` phase;
- World revision and Turn match exactly;
- one Plan exists for Rescue, Pirate, and Swarm;
- every Plan binds the current Standing Order revision;
- Commander Actions remain within faction, charge, cooldown, target, and Command Point limits;
- every Actor owns at most one Intent;
- every Intent references admitted World objects and known targets.

Admission failure returns:

```text
status: rejected
code: invalid_turn_batch
```

The input World is never mutated.

Once admitted, local tactical failure cannot reject the complete Turn.

## Resolution order

One accepted Turn is resolved in this fixed order:

```text
Commander
→ Movement
→ Reaction
→ Combat
→ Interaction
→ Environment
→ Cleanup
```

Faction Plan and Intent array order are not authoritative. The reducer canonicalizes them by:

1. faction order;
2. Resolution Phase;
3. descending Actor initiative;
4. Actor identity;
5. Intent identity.

Reordering equivalent input arrays produces the same World, Resolution digest, and Turn Record digest.

## Intent results

Every committed Intent receives exactly one result:

| Status | Meaning |
|---|---|
| `executed` | The committed operation produced its admitted effect. |
| `interrupted` | The Actor became unable to complete the operation during the same Turn. |
| `invalidated` | The operation was legal at commitment but its target or conditions no longer existed at execution. |
| `contested` | Another admitted operation won a finite shared claim such as Zone capacity or ground loot. |
| `no_effect` | The rules executed correctly, but no material World change was needed or triggered. |

Every result also retains:

```text
verificationPassed: true
```

This means the authoritative rules resolved and recorded the operation correctly. It does not claim the Actor achieved its desired outcome.

## Tactical topology

Movement derives exclusively from the current Passage graph.

- `open` Passages admit movement;
- `closed` and `sealed` Passages block movement;
- `vent` and `swarm-route` Passages admit only Swarm movement;
- Actor movement is bounded by current Movement Range;
- Commander Passage changes occur before movement.

There is no second adjacency table.

### Zone contention

P1 uses conservative simultaneous capacity:

- current active occupants reserve their Zone capacity for the complete Turn;
- incoming contenders are ranked by initiative and stable identity;
- available positions are assigned to the highest-ranked contenders;
- remaining contenders receive `contested / target_zone_capacity_lost`.

P1 deliberately does not support same-Turn swaps into capacity vacated by another mover. This avoids recursive movement dependencies in the first reducer and can be reconsidered only if playtesting proves it necessary.

## Reactions

A Guard or reaction Ability may watch one Zone.

When a hostile admitted mover would enter that Zone:

1. the Reaction executes before arrival;
2. deterministic damage is applied;
3. an incapacitated or killed mover remains in its source Zone;
4. its Move resolves as `interrupted`;
5. the rest of the Turn continues.

One Reaction Actor fires once per Turn, and one mover triggers at most one Reaction in P1.

## Combat

There are no hidden hit rolls.

Damage is computed from explicit World state:

```text
Ability damage
− effective armor after armor piercing
− target Zone cover
```

Reaction attacks ignore destination cover because they occur before arrival.

System integrity changes are quantized to thousandths before they enter authoritative state or Replay.

### Focus fire

Multiple Actors may legally commit attacks against the same target.

Combat resolves by initiative:

- earlier attacks may wound or incapacitate the target;
- a later attack against an incapacitated target becomes a finishing strike;
- a later attack against a dead, captured, or extracted target becomes `invalidated`;
- earlier effects remain committed.

This replaces the v2 assumption that competing operations on one mutable target must reject the whole Tick.

### Life state

P1 supports:

```text
active
incapacitated
dead
captured
extracted
```

At zero health:

- creatures die;
- humanoids and civilians normally become incapacitated;
- deterministic overkill may kill directly;
- a later attack may finish an incapacitated target.

Death drops inventory and equipment into the current Zone. Biological equipment becomes Alien Tissue; ordinary equipment maps to its retained Item definition.

## Interaction

P1 implements:

- ground Item pickup;
- System repair;
- System or Passage hacking;
- medical stabilization;
- civilian escort binding;
- capture of incapacitated targets;
- Swarm devouring and Biomass gain;
- System infection;
- faction extraction;
- objective Item extraction.

Finite ground loot is resolved by initiative. A later claimant receives `contested` rather than rolling back the winner.

Consumed Spare Parts are retained as explicit `item_consumed` Facts.

## Commander Actions

The reducer applies the frozen P0 Commander catalog before Actor movement:

### Rescue

- Orbital Scan;
- Emergency Power Reroute;
- Bulkhead Lockdown;
- Emergency Uplink;
- Rescue Extraction.

### Pirate

- Signal Jam;
- Door Spoof;
- Pirate Extraction;
- Mark Prize.

### Swarm

- Pheromone Surge;
- Brood Awakening;
- Vent Spread.

Commander resources are consumed deterministically and cooldowns advance in Cleanup.

## Environment

Environment advances exactly once per accepted Turn.

### Battery

Powered Systems draw their retained `powerDraw`. The battery ledger remains conserved:

```text
batteryCharge + energyConsumed = batteryInitial
```

A brownout disables powered consuming Systems after available charge is exhausted.

### Oxygen

Oxygen combines:

- baseline consumption;
- uncontrolled Hull Breach loss;
- operational powered Life Support recovery.

Low oxygen damages active Actors.

### Reactor heat

Operational powered Cooling lowers heat. Otherwise heat rises from unavailable Cooling and unresolved Reactor Instability.

Actors in the Reactor may take high-heat damage.

### Alert and Biomass

Combat raises Alert once per Turn. Devour, Brood Awakening, and Brood Call alter Biomass through explicit Facts.

## Cleanup

Cleanup:

- resolves Wait and Cleanup Abilities;
- can spawn one deterministic policy Brood through `brood-call`;
- decrements Ability and Commander cooldowns;
- restores Action Points, Command Points, and Uplink slots for the next Turn;
- removes one-Turn Pheromone statuses;
- advances World revision, Turn, and Standing Order head exactly once.

## Objectives and outcomes

Objective progress derives from World state after Cleanup.

The reducer evaluates:

- rescued civilians;
- extracted Specialists and Pirates;
- extracted Research Core and equipment;
- Hive Alpha survival or death;
- capture;
- Biomass;
- Life Support infection;
- devoured Specialists.

At a terminal boundary, each faction independently receives:

```text
victory
partial
failure
```

One World terminal state may therefore produce Pirate victory, Swarm partial success, and Rescue failure.

## Faction knowledge and observations

Faction knowledge remains authoritative gameplay state.

After resolution, each faction receives a content-addressed Observation containing only:

- Facts visible from its current local visibility;
- persistent discovered Rooms and Zones;
- known Actors, Systems, Hazards, and ground Items.

Active faction Actors reveal their Zone and one open Passage step around it. Remote combat Facts remain hidden from factions without local visibility, while global environmental telemetry remains visible.

Known remote enemy positions become `stale`; they are not silently updated from hidden World truth.

## Turn Records and replay

Every accepted Turn produces a content-addressed Record containing:

- exact before-state digest;
- canonical Turn Batch;
- every Intent Resolution;
- every Fact;
- three faction Observations;
- exact after-state digest;
- Record digest.

`replayStationZeroV3Turn()` re-executes one retained Record and verifies all digests.

`replayStationZeroV3History()` starts from raw Genesis, prepares each commitment boundary, and replays a multi-Turn Record sequence through every retained Intent Resolution.

Tampering with the Record, before-state, Resolution, or after-state fails closed.

## P1 tests

`test/station-zero-v3-reducer.test.ts` verifies:

1. one complete three-faction Turn;
2. environment advancement exactly once;
3. input-order independence;
4. deterministic Zone contention;
5. Overwatch interruption;
6. legal focus fire;
7. local invalidation without whole-Turn rollback;
8. death and equipment drop;
9. ground loot pickup;
10. Item and Actor extraction;
11. Commander / System / environment coupling;
12. faction-local observations;
13. exact one-Turn and multi-Turn Replay;
14. independent faction outcomes;
15. deterministic Brood spawning;
16. admission rejection without input mutation.

## Implemented by P2

P2 supplies the sole durable Turn execution path:

```text
open Planning Head
→ retain one immutable Plan per faction
→ commit one canonical Turn Batch
→ prepare one exact durable Turn Batch
→ execute outside model ownership
→ atomically retain World Event + Turn Record + World Head
→ recover uncertain response by original identity
→ expose bounded Mission Control state
```

See [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md) for persistence, exact Turn receipt/recovery, evidence-chain, and projection boundaries.

P1 remains the sole deterministic rules owner. Persistence and Host orchestration must invoke the reducer rather than reimplementing combat or environment rules.
