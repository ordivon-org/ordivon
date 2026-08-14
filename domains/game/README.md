---
schema_version: 1
id: game.start
title: Ordivon Game
type: start
profile: organization
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
updated: 2026-08-08
summary: Canonical entry to Ordivon Game, the current Station Zero executable, the unregistered v3 target, and their authority boundaries.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.product.station-zero
  - game.architecture
  - game.vision
  - game.authority
---
# Ordivon Game

## Purpose

**Intervention-driven worlds for people and Agents.**

Ordivon Game currently ships one executable world: **Station Zero**, a deterministic multi-Agent mission game. The player commands Engineer, Medic, and Security specialists through standing doctrine and consequential interventions rather than moving units directly.

## Current boundary

The registered product remains Station Zero `station-zero@2` with Ruleset `station-zero-core@3`. The v3 encounter, reducer, durable execution, planning layer, dedicated API, and separate `/v3` first-playable are implemented as an accepted replacement target, but v3 remains unregistered and does not replace the root product. Replacement is deferred until repeated human playtesting and live-Provider evaluation justify deleting the v2 approval loop.

## Start here

- [`docs/PRODUCT.md`](docs/PRODUCT.md) defines the current Station Zero product and player experience.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines the current executable architecture and state ownership.
- [`docs/VISION.md`](docs/VISION.md) defines the broader Game direction without turning possibilities into commitments.
- [`docs/DEVELOPMENT_MODEL.md`](docs/DEVELOPMENT_MODEL.md) defines how Ordivon classifies and develops games, where Agent-specific mechanisms fit inside the normal game lifecycle, and how Game consumes Studio production without taking over Studio authority.
- [`docs/STATION_ZERO_V3_P0.md`](docs/STATION_ZERO_V3_P0.md), [`P1`](docs/STATION_ZERO_V3_P1.md), [`P2`](docs/STATION_ZERO_V3_P2.md), and [`P3`](docs/STATION_ZERO_V3_P3.md) define the accepted but unregistered v3 target slices.
- [`docs/authority.md`](docs/authority.md) identifies which records may define current or target behavior.

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

Only this Scenario and Ruleset are registered as the current product. Older executable paths, compatibility APIs, migration layers, milestone fixtures, and release-era evidence have been removed from the repository.

## Station Zero v3 preview

The next Station Zero form is retained under `src/station-zero-v3/` and documented in:

- [`docs/STATION_ZERO_V3_P0.md`](docs/STATION_ZERO_V3_P0.md): frozen encounter and content contract;
- [`docs/STATION_ZERO_V3_P1.md`](docs/STATION_ZERO_V3_P1.md): deterministic Turn reducer and pure replay contract;
- [`docs/STATION_ZERO_V3_P2.md`](docs/STATION_ZERO_V3_P2.md): durable SQLite execution, Embedded Host lifecycle, crash recovery, and bounded Mission Control projection;
- [`docs/STATION_ZERO_V3_P3.md`](docs/STATION_ZERO_V3_P3.md): Commander Orders, bounded Agent planning, policy expansion, sealed three-faction Preview, explicit Commit, and browser first-playable.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
Target form: three-faction deterministic turn-based tactical encounter
P1: reducer and pure replay complete
P2: durable Turn authority and recovery complete
P3: isolated playable planning layer and /v3 browser complete
Optional exact Agent Action admission: implemented in the unregistered v3 path
```

The v3 preview is available through a separate API namespace, SQLite database, and browser surface. It is still absent from `src/registry.ts` and does not replace the current root product. Replacement is deferred until repeated human playtesting and live-Provider evaluation justify deleting the v2 approval loop.

## Run

Requirements:

- Node.js 26 or newer;
- pnpm 10.33.2.

```bash
pnpm install --frozen-lockfile
pnpm check
pnpm start
```

Open:

```text
Current product: http://127.0.0.1:4173/
Station Zero v3 preview: http://127.0.0.1:4173/v3
```

Browser acceptance journeys:

```bash
pnpm e2e
pnpm e2e:v3
```

## Product API

### Current product

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

### Station Zero v3 preview

```text
GET  /api/station-zero-v3/catalog
GET  /api/station-zero-v3/runs
POST /api/station-zero-v3/runs
POST /api/station-zero-v3/resume
GET  /api/station-zero-v3/state
POST /api/station-zero-v3/order
POST /api/station-zero-v3/preview
POST /api/station-zero-v3/commit
```

The v3 preview uses `data/station-zero-v3.sqlite3` by default and does not add v3 Runs to the current `/api/runs` contract.

## Repository map

```text
src/model.ts, scenario.ts, world.ts, facts.ts
    current authoritative World state, rules, facts, and verification

src/storage.ts, run.ts, registry.ts
    current contract identity, persistence, recovery, and replay source

src/team/
    current specialist Context, Messages, authority, Proposals, coordination, Providers

src/host-contract/
    shared Task/Effect/Dispatch/Observation/Verification authority

src/mission-control/
    current player-facing doctrine, forecast, intervention, and bounded read model

src/replay/, src/deployment/, src/comparison/
    current evidence projection, diagnosis, retained configuration, and Run comparison

src/server.ts, web/
    current product HTTP service and browser interface

src/station-zero-v3/
    v3 content, Genesis, deterministic reducer, Planning/Turn authority, Host execution, Agent Context and Candidate admission, policy expansion, Play Service, recovery, and bounded projections

web-v3/
    isolated Station Zero v3 first-playable browser

docs/STATION_ZERO_V3_P0.md through docs/STATION_ZERO_V3_P3.md
    v3 encounter, reducer, durable execution, and playable planning boundaries

test/, scripts/e2e-first-playable.ts, scripts/e2e-station-zero-v3.ts
    current-product verification plus v3 contract, reducer, persistence, planning, API, renderer, and real-browser journeys
```

See [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and [`docs/VISION.md`](docs/VISION.md).

## Project family

- [Public project directory](https://ordivon.com/projects) — current product, v3 preview status, project role, and next steps.
- [Cross-project map](https://github.com/zycxfyh/ordivon-computing/blob/main/projects/README.md) — stable roles, repository links, and authority entry points for the current project family.
- Related owners: Game owns authoritative game World state and player-facing rules; [Ordivon Host](https://github.com/zycxfyh/ordivon-host), [Harness](https://github.com/zycxfyh/ordivon-harness), and [Runtime](https://github.com/zycxfyh/ordivon-runtime) own their generic boundaries only when a Game path consumes them.

## License

Apache License 2.0.
