# Product definition: Station Zero

This document defines the first product vertical. It does not define the full purpose of Ordivon Game. The broader project may support playgrounds, creative worlds, social spaces, Agent habitats, and research or Security verticals; see [`VISION.md`](VISION.md).

## Product thesis

The player should feel responsible for a capable but imperfect autonomous team. The central tension is not direct control; it is deciding what to delegate, what to verify, when to intervene, and which losses to accept.

The game succeeds only when Agent autonomy creates meaningful decisions that a conventional scripted unit system would not create as naturally.

## Player role

The player is the remote mission-control director for an isolated station. They cannot move crew members directly. They can:

- define mission goals and priorities;
- assign specialists, tools, and scarce resources;
- grant or revoke authority;
- approve exceptional or dangerous operations;
- request observations and evidence;
- redirect, pause, or cancel work;
- review the mission history and improve the next deployment.

## First scenario

A compact station suffers a linked failure:

```text
power instability
→ partial blackout
→ oxygen circulation degradation
→ unreliable communications
→ injured or isolated personnel
```

The first map contains roughly 8–12 rooms:

- command center;
- medical bay;
- reactor room;
- life-support room;
- communications room;
- storage;
- isolation chamber;
- connecting corridors.

## Initial Agent team

### Engineer

- strong repair and energy-system capability;
- can inspect, isolate, replace, and test equipment;
- tends to accept technical risk to restore critical systems.

### Medic

- strong diagnosis, treatment, and life-support capability;
- prioritizes preventable loss of life;
- cannot perform most heavy engineering actions.

### Security specialist

- strong exploration, access control, transport, and hazard containment capability;
- prioritizes containment and crew survival;
- may conflict with high-risk repair plans.

Differences must be expressed through capabilities, goals, observations, risk preferences, and admitted actions—not merely different dialogue styles.

## Core loop

```text
receive the mission brief
→ choose a Command Doctrine
→ Agents observe, plan, and execute routine verified work
→ Mission Control stops at consequential intervention boundaries
→ player authorizes, denies, redirects, pauses, or changes standing orders
→ the team continues from durable World and Host state
→ mission reaches a verified outcome
→ replay, diagnose, and compare the decision chain
```

The product is intervention-driven rather than Tick-confirmation-driven. Every World Tick remains individually authoritative and verified, but the player is interrupted only when a decision has material consequence. Exact per-Tick Proposal review remains a Lab capability.

## Sources of fun

1. **Delegation tension** — more autonomy increases speed but reduces control.
2. **Incomplete information** — Agents possess different local observations.
3. **Professional disagreement** — specialists prefer different valid solutions.
4. **Resource trade-offs** — power, oxygen, time, equipment, and personnel are scarce.
5. **Recoverable failure** — failed attempts leave consequences and evidence.
6. **System mastery** — the player improves by changing team design and authority, not by learning hidden prompts.
7. **Emergent stories** — memorable outcomes arise from goals, constraints, and world state.

## Design principles

### The world is authoritative

Models never directly mutate inventory, health, doors, equipment, power, oxygen, mission score, or victory state.

### Freedom is bounded by capability

Agents may propose open-ended plans, but every world effect must map to a typed action with explicit preconditions and completion semantics.

### Failure must be legible

The player should be able to identify the chain that caused a failure and make a concrete change before the next run.

### Dialogue supports action

Conversation can explain, negotiate, warn, or request approval. It is not the primary product by itself.

### Model calls are low-frequency cognition

Pathfinding, animation, damage, resource updates, and routine execution remain deterministic. Models are invoked for goal interpretation, planning, disagreement, exception handling, and high-value decisions.

## First-playable scope

The first playable includes:

- one deterministic station map;
- three specialist Agents;
- six authoritative resources or conditions: time, power, oxygen, health, equipment integrity, communications;
- a small typed action set;
- one linked emergency mission;
- player-facing Command Doctrines compiled into the existing authority boundary;
- exact next-Tick consequence forecasts and Mission Fronts;
- automatic execution until a meaningful intervention;
- player approval, redirection, pause, and cancellation;
- complete event replay and outcome verification.

## Explicit non-goals

The first playable does not include:

- 3D rendering or real-time action combat;
- a general-purpose game engine;
- hundreds of autonomous residents;
- persistent civilization simulation;
- multiplayer competition;
- user-authored arbitrary tools;
- a general workflow DSL;
- model-generated authoritative rules;
- monetization or live-service infrastructure.

## Product acceptance criteria

The vertical slice is successful when:

1. Agents cannot create nonexistent objects, capabilities, observations, or outcomes.
2. The same Agent configuration produces a recognizable behavioral style across runs.
3. Different team authority settings produce materially different mission trajectories.
4. The mission can pause and resume without losing semantic state.
5. Every terminal outcome has evidence that can be independently checked.
6. A failed run exposes at least one understandable decision or coordination error.
7. A player can improve subsequent performance through configuration changes.
8. The experience is interesting before visual polish or large content volume is added.

## M1 playable proof

The first deterministic scenario now makes three pressures advance together:

- reactor heat rises unless repaired cooling receives power;
- oxygen falls until the hull breach is sealed and life support is restored;
- an injured crew member loses health until stabilized.

The Engineer has exactly three spare parts across the station, one sealant charge, one medkit, and a finite battery. Repairing or powering one system does not pause the other hazards.

The intended strategic lesson is visible without an LLM:

> Completing communications first is locally sensible but globally fatal. The player must control the hazard frontier, collect finite supplies, decide when cooling can be switched off, and preserve enough energy to transmit the final signal.

This is the first evidence that Station Zero contains an actual management problem rather than only an Agent integration demonstration.
