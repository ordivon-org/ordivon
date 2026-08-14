---
schema_version: 1
id: game.station-zero-v3.encounter
title: Station Zero v3 — P0 frozen encounter contract
type: decision
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
updated: 2026-08-14
summary: Accepted target decision for the unregistered Station Zero v3 three-faction encounter, player role, deterministic turn contract, tactical space, and fixed Genesis.
evidence_status: not_applicable
readiness: READY
applies_to:
  - station-zero-v3-unregistered
related:
  - game.station-zero-v3.reducer
  - game.station-zero-v3.execution
  - game.authority
---
# Station Zero v3 — P0 frozen encounter contract

## Context

The registered Station Zero product proved intervention-driven multi-Agent play but did not yet provide the stronger adversarial tactical form, opposing factions, commander abilities, and repeatable encounter structure selected for the next implementation.

## Decision

Freeze one deterministic three-faction encounter contract for Rescue, Pirate, and Swarm commanders. The contract fixes player and Agent responsibilities, tactical topology, actor fidelity, turn and resolution identity, faction knowledge, content boundaries, and one reproducible Genesis before service or browser registration.

## Consequences

Reducer, persistence, planning, Host execution, Agent integration, and product registration must conform to this encounter contract. The phase-coded path remains the current target authority until a stable human-oriented product specification explicitly supersedes it; it does not make v3 the registered executable.

## Status

This document defines the **next Station Zero domain contract** without replacing the current executable.

```text
Current executable: station-zero@2 / station-zero-core@3 / World schema 2
P0 frozen target: station-zero@3 / station-zero-core@4 / World schema 3
```

The v3 code under `src/station-zero-v3/` remains deliberately absent from `src/registry.ts`. P1 implemented the pure deterministic reducer, P2 implemented durable Turn execution and recovery, and P3 implemented bounded player/Agent planning plus a verified `/v3` first-playable; see [`STATION_ZERO_V3_P1.md`](STATION_ZERO_V3_P1.md), [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md), and [`STATION_ZERO_V3_P3.md`](STATION_ZERO_V3_P3.md). Replacement of the current executable remains deferred until repeated playtesting and live-Provider evaluation justify deleting the v2 approval loop.

## Product form

```text
single-player asymmetric turn-based tactical encounter
```

The fixed P0 encounter contains:

- one player-controlled Rescue faction;
- one Pirate faction directed by a Captain Agent;
- one Swarm faction directed by a Hive Mind Agent;
- 12 persistent Actors;
- 8 Rooms split into 20 tactical Zones;
- named equipment and deterministic Abilities;
- coupled power, oxygen, reactor heat, alert, biomass, hazards, and passages;
- faction-local knowledge rather than an omniscient player view;
- mandatory and optional objectives for every faction;
- faction-specific victory, partial-success, and failure outcomes.

The first playable v3 encounter is bounded to 20 Turns.

### G3 viability correction

The original P0 budget was 14 Turns. G3 strategic-viability falsification showed that this budget made the mandatory Rescue objective effectively fake under the bounded game surface: objective-consistent Rescue play could reach and recover one civilian but could not complete both extraction chains before the terminal Turn. The same World rules, enemy policies, bounded Knowledge, Candidate admission, and Rescue policy completed both mandatory objectives at Turn 20 when only the encounter budget was extended.

The audit separately tested and rejected narrower explanations before changing the contract: a `life-console` capacity increase from two to three did not create a 14-Turn victory; bounded `emergency-uplink` and known-contact priority targeting did not create one; fixture responsibility/successor-state defects for cargo extraction, civilian support, and moving Hive pursuit were fixed independently rather than compensated by the budget. The 20-Turn limit is therefore a content/balance correction, not an authority or reducer change.

This does not guarantee victory. Enemy movement, Zone contention, casualties, partial objectives, and competing priorities remain capable of consuming the additional Turns.

## Mature genre mechanisms retained

| Source family | Retained in Station Zero v3 | Explicitly not copied |
|---|---|---|
| Roguelite / deckbuilder | encounter rewards, build-relevant equipment, costly extraction, content that can later enter a branching Run | route map, meta progression, random hit resolution in P0 |
| Tactical RPG / warband | position, cover, equipment, initiative, named persistent Actors, injuries and asymmetric objectives | direct control of every ordinary movement, global binary victory |
| Sandbox / Minecraft-like systemic world | material objects, passages, systems, loot and hazards that can be changed and combined | arbitrary construction, infinite world, generated rules |
| FTL-like systemic crisis | coupled power, oxygen, heat and multiple responses to the same failure | real-time pause control and simulation detail without decisions |
| Character / colony simulation | roles, traits, leaders, death, capture and a path to persistent history | hundreds of full-fidelity Agent calls or social simulation in P0 |

These influences are encoded in `STATION_ZERO_V3_P0_CONTRACT` and tested. They are constraints, not marketing labels.

## Core player loop

```text
Situation
→ Command
→ Agent Deliberation
→ Commitment
→ Deterministic Resolution
→ Aftermath
```

### Player owns

- three Command Points each Turn;
- Commander Ability use;
- objectives and priority targets;
- protection and retreat rules;
- lethal-force, collateral, and loot policies;
- the decision to commit or extract.

### Agents own

- bounded legal movement;
- weapon and Ability selection;
- local target and cover selection;
- execution within Standing Orders;
- later adaptation to invalidated actions.

A normal attack, move, pickup, or guard action is not individually approved by the player.

## Determinism policy

Randomness may select future encounter setup, enemy composition, loot, hidden modules, and route nodes. Once a Turn is committed, the authoritative reducer must be deterministic.

```text
Randomness generates the problem.
Rules resolve the committed Turn.
Player and Agent decisions determine the trajectory.
```

There are no hidden hit rolls in the frozen Ability catalog. Damage is an integer property of an Ability and is modified only by explicit World state such as armor, cover, range, status, or interruption.

## Tactical space

A Room is narrative and systemic space. A Zone is tactical space.

Zones own:

- capacity;
- cover;
- console, extraction, vent, nest, objective, and chokepoint tags.

Passages connect Zones and may be opened, closed, sealed, spoofed, or locked down. P1 must derive movement from Passage state rather than maintaining a second adjacency truth.

This is intentionally smaller than a tile grid but materially richer than one location per Room.

## Actor fidelity

High-fidelity cognition is limited:

```text
Engineer + Medic + Security
Pirate Captain
Hive Alpha
```

The Captain and Hive Alpha direct lower-cost policy Actors. This proves hierarchical Agent control before any hundred-Agent world is attempted.

Each Actor has:

- faction and controller kind;
- role and leader identity;
- health, armor, initiative, movement, and Action Points;
- traits and capabilities;
- equipped weapon, armor, utility, or biology;
- inventory, cooldowns, status, and life state.

Civilians are neutral World Actors. They can be rescued, captured, killed, or devoured without becoming a fourth faction.

## Turn contract

Every committed Turn contains exactly one `FactionTurnPlan` for Rescue, Pirate, and Swarm.

A Faction Plan binds:

- exact World revision and Turn;
- exact Standing Order revision;
- bounded Commander Actions;
- at most one Intent per Actor;
- the identity that committed the Plan.

The current P0 validator rejects:

- stale World or Turn heads;
- missing or duplicate Faction Plans;
- Commander Ability use outside faction, charge, cooldown, target, or Command Point limits;
- attacks against Actors outside faction knowledge;
- invented Actors, Zones, Passages, Systems, Hazards, Items, Equipment, Abilities, or Objectives;
- multiple Intents for one Actor;
- actions exceeding Actor Action Points;
- extraction outside a faction extraction Zone.

## Resolution contract

P1 must resolve one accepted Turn in this fixed order:

```text
Commander
→ Movement
→ Reaction
→ Combat
→ Interaction
→ Environment
→ Cleanup
```

Every Intent receives one Resolution status:

- `executed`;
- `interrupted`;
- `invalidated`;
- `contested`;
- `no_effect`.

`verificationPassed` answers whether the authoritative rules correctly resolved and recorded the Intent. It does **not** mean the Actor achieved its desired outcome.

Example:

```text
A Pirate shoots a target that was removed by an earlier reaction.
Intent status: invalidated
Reason: target no longer active
Verification: passed
```

This replaces the current assumption that one invalid local action should reject the complete multi-Actor Tick.

## Faction identity

### Rescue

Mandatory:

- extract two civilians;
- extract at least one Specialist.

Optional:

- recover the Research Core;
- eliminate the Hive Alpha.

### Pirate

Mandatory:

- extract the Research Core;
- extract at least one Pirate.

Optional:

- capture Engineer Imani;
- steal the Medical Drone.

### Swarm

Mandatory:

- accumulate 12 Biomass;
- preserve or extract the Hive Alpha.

Optional:

- infect Life Support;
- devour a Specialist.

The Encounter becomes terminal once the rules determine that no further meaningful faction outcome can change. Each faction then receives its own `victory`, `partial`, or `failure` result.

## P0 fixed Genesis

The fixed Genesis is created by `createStationZeroV3Genesis()` and verified by `assertStationZeroV3World()`.

It contains:

- Rescue at Command Center;
- Pirates entering through Cargo Airlock;
- Swarm occupying Maintenance and the Life Support duct;
- two civilians in Medical Bay and Life Support;
- the Research Core at the Reactor Console;
- damaged Cooling, Communications, Life Support, and Power Grid systems;
- a Hull Breach, Biomass Nest, and Reactor Instability;
- incomplete and different knowledge for every faction.

Rescue initially knows no exact Pirate or Swarm Actor position. This is a hard invariant of the player-facing design, not a UI concealment over omniscient data.

## P0 boundaries

P0 does not implement:

- damage, movement, cover, reaction, or environmental reducers;
- Agent Context compilation;
- Mission Control v2 UI;
- route selection;
- post-encounter inventory persistence;
- player-controlled Pirate or Swarm factions;
- relationships, stress, careers, settlements, or a hundred-Agent world.

Those mechanisms must be earned in later phases.

## P1 entry criteria

P1 may begin only from this contract and must demonstrate:

1. one complete deterministic Turn across all three factions;
2. order-independent input Plans;
3. legal multi-attacker focus fire;
4. deterministic Zone contention;
5. reactions that can interrupt movement;
6. local invalidation without whole-Turn rollback;
7. death, equipment drop, pickup, and extraction;
8. environment advancement exactly once;
9. faction-local observations after resolution;
10. replay of every Intent Resolution from Genesis.
