# Ordivon Game

**Intervention-driven worlds for people and Agents.**

Ordivon Game currently ships one executable world: **Station Zero**, a deterministic multi-Agent mission game. The player commands Engineer, Medic, and Security specialists through standing doctrine and consequential interventions rather than moving units directly.

## Station Zero

A damaged station is losing power, oxygen, communications, and crew health at the same time. Each specialist receives bounded local context, proposes only actions permitted by their capability, and may communicate through local or station-radio channels. Compatible proposals execute together in one atomic World Tick.

The player can:

- choose a Command Doctrine;
- assign or replace cognition Providers;
- approve or deny consequential actions;
- redirect objectives;
- pause, resume, or cancel specialist work;
- inspect verified mission history;
- compare deployments and outcomes.

The default loop is:

```text
configure deployment
→ run until intervention
→ approve, deny, redirect, or change doctrine
→ continue from durable state
→ reach a verified outcome
→ replay, diagnose, and compare
```

## Authority model

```text
Player / Browser
        ↓ doctrine, commands, approvals
Mission Control
        ↓ bounded product state and intervention rules
Station Zero Team domain
        ↓ actor Contexts, Messages, Proposals, authority, coordination
Embedded Host authority
        ↓ Task, Effect, Dispatch, Observation, Verification, Outcome
Deterministic World
        ↓ atomic Tick and authoritative state transition
SQLite evidence
        ↓ recovery, replay, diagnosis, comparison
```

The model never owns World state. It cannot create objects, capabilities, observations, approvals, actions, or completion claims. Every accepted consequence is checked by the World and independently represented as evidence.

## Current contract

```text
Scenario: station-zero@2
Ruleset: station-zero-core@3
Actors: Engineer, Medic, Security
Persistence: SQLite
Service: one local Node.js process
Runtime dependencies: none
```

Only this Scenario and Ruleset are supported. Older executable paths, compatibility APIs, migration layers, milestone fixtures, and release-era evidence have been removed from the repository.

## Run

Requirements:

- Node.js 26 or newer;
- pnpm 10.33.2.

```bash
pnpm install --frozen-lockfile
pnpm check
pnpm start
```

Open `http://127.0.0.1:4173`.

Browser acceptance journey:

```bash
pnpm e2e
```

## Product API

```text
GET  /api/runs
GET  /api/providers/preflight

GET  /api/mission-control/catalog
GET  /api/mission-control/state
GET  /api/mission-control/timeline
POST /api/mission-control/initialize
POST /api/mission-control/advance
POST /api/mission-control/command

GET  /api/replay/timeline
GET  /api/replay/report
GET  /api/replay/frame

GET  /api/deployments/manifest
GET  /api/compare
```

## Repository map

```text
src/model.ts, scenario.ts, world.ts, facts.ts
    authoritative World state, rules, facts, and verification

src/storage.ts, run.ts, registry.ts
    final contract identity, persistence, recovery, and replay source

src/team/
    specialist Context, Messages, authority, Proposals, coordination, Providers

src/host-contract/
    embedded Task/Effect/Dispatch/Observation/Verification authority

src/mission-control/
    player-facing doctrine, forecast, intervention, and bounded read model

src/replay/, src/deployment/, src/comparison/
    evidence projection, diagnosis, retained configuration, and Run comparison

src/server.ts, web/
    product HTTP service and browser interface

test/, scripts/e2e-first-playable.ts
    current-contract verification and one complete browser journey
```

See [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and [`docs/VISION.md`](docs/VISION.md).

## License

Apache License 2.0.
