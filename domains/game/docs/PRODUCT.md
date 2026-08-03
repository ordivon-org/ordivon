---
schema_version: 1
id: game.product.station-zero
title: Station Zero
type: concept
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - player
  - designer
  - builder
  - agent
updated: 2026-08-03
summary: Canonical product definition for the registered Station Zero experience, player role, core loop, sources of play, scope, outcomes, and acceptance.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero@2
related:
  - game.start
  - game.architecture
  - game.vision
  - game.authority
---
# Station Zero

## Problem

A conventional unit-control game does not test the central experience Ordivon Game is pursuing: delegating consequential work to capable but imperfect autonomous specialists while preserving meaningful player authority, understandable failure, and recoverable history.

## Model

Station Zero is an intervention-driven deterministic mission game. The player sets doctrine, Provider assignments, authority, objectives, and bounded messages; specialists act from local information; the World admits legal consequences; Mission Control interrupts only when judgment is required; replay exposes what happened and why.

## Boundary

This document defines the registered Station Zero product experience and acceptance criteria. It does not define every future Ordivon world, the exact implementation schema, or the unregistered v3 replacement contract.

## Related work

[`ARCHITECTURE.md`](ARCHITECTURE.md) defines executable ownership and persistence, [`VISION.md`](VISION.md) defines the broader Game direction, and [`STATION_ZERO_V3_P0.md`](STATION_ZERO_V3_P0.md) begins the accepted v3 target specification.

## Product thesis

The player leads a capable but imperfect autonomous response team. The central decision is not how to move every unit; it is what to delegate, what to verify, when to intervene, and which losses to accept.

Agent autonomy earns its place only when it creates meaningful coordination, authority, information, or recovery decisions that a conventional scripted unit system would not produce as naturally.

## Situation

A remote station suffers a linked emergency:

```text
power instability
→ cooling and life-support failure
→ oxygen loss and reactor heating
→ unreliable communications
→ injured personnel
```

Time advances after every accepted Tick. Power, oxygen, health, equipment integrity, consumables, communications, and specialist location constrain the available response.

## Team

### Engineer

Repairs systems, manages power, carries technical supplies, and may seal the hull breach.

### Medic

Stabilizes injured crew and protects life under incomplete local information.

### Security

Explores, transports resources, controls access, and can contain the breach without consuming Engineer sealant.

Their differences are enforced through capabilities, observations, inventory, objectives, and admitted actions—not dialogue style alone.

## Player role

The player operates Mission Control and can:

- choose a doctrine;
- select Providers for each specialist;
- approve or deny restricted Proposals;
- redirect an actor's objective;
- send bounded messages;
- pause, resume, or cancel specialist work;
- review the verified outcome;
- clone and compare deployments.

The player cannot directly mutate World state.

## Core loop

```text
choose Scenario Case, doctrine, coordination profile, and Providers
→ team executes routine verified work
→ Mission Control stops at a consequential boundary
→ player approves, denies, redirects, or changes standing orders
→ execution resumes from durable state
→ mission reaches victory or a specific failure
→ replay and diagnosis expose the decision chain
→ a revised deployment can be compared with the retained Run
```

## Sources of play

- **Delegation tension:** autonomy increases speed while reducing direct control.
- **Incomplete information:** actors see different local facts and depend on communication.
- **Professional conflict:** several valid specialist plans compete for scarce time and resources.
- **Authority:** a safe default may delay a high-value action; broader autonomy may accept more risk.
- **Resource coupling:** solving one subsystem can make another impossible.
- **Recoverable failure:** interrupted execution preserves evidence and can continue without duplicate effects.
- **System mastery:** improvement comes from changing doctrine, coordination, Provider assignment, and intervention—not hidden prompt tricks.

## Current scope

Station Zero includes:

- one eight-room deterministic station;
- three persistent specialists;
- three Scenario Cases;
- one linked emergency;
- atomic multi-Actor Ticks;
- local and radio communication;
- attribute-based authority and exact Grants;
- three player doctrines;
- automatic execution until intervention;
- exact next-Tick forecasts and four Mission Fronts;
- durable replay, evidence-linked diagnosis, deployment cloning, and comparison.

## Success and failure

Victory requires a verified distress signal, stabilized crew, controlled breach, operational cooling and life support, adequate oxygen, and bounded reactor heat.

Failure is explicit and retained, including:

- reactor meltdown;
- station asphyxiation;
- crew loss;
- complete team incapacitation;
- power exhaustion;
- mission timeout.

A terminal outcome is never inferred from model prose.

## Product principles

1. **The World is authoritative.** Models propose; the reducer decides.
2. **Capability and authority are separate.** Being able to act does not imply permission.
3. **Player attention is scarce.** Routine work proceeds automatically; meaningful decisions interrupt.
4. **Failure must be legible.** Every outcome should expose evidence the player can use in the next deployment.
5. **Dialogue supports consequence.** Communication matters when delivery and content change later action.
6. **Provider replacement preserves identity.** The specialist and Task survive model or process replacement.
7. **Play comes before platform.** Station Zero does not justify a universal game engine.

## Explicit non-goals

The current product does not include:

- 3D rendering or action combat;
- multiplayer;
- hundreds of residents;
- a persistent civilization simulation;
- arbitrary user-authored tools;
- model-generated authoritative rules;
- hosted live-service infrastructure;
- a general workflow or multi-Agent scheduling platform.

## Product acceptance

The current vertical slice is valid when:

- actors cannot invent World objects, capabilities, observations, actions, or outcomes;
- authority settings materially change trajectories;
- communication reachability can change the result;
- process interruption does not duplicate World effects;
- every revision can be reconstructed and verified;
- a failed Run identifies an understandable contributor;
- a player can produce and compare a materially different deployment;
- the experience remains interesting without large content volume or visual spectacle.
