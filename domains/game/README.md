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
updated: 2026-08-17
summary: Canonical entry to Ordivon Game, its cross-game development model, current Station Zero executable, research treatments, and the R1–R18 foundations corpus without selecting a new product.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.product.station-zero
  - game.product.station-zero-v3
  - game.product.station-zero-v3.vertical-slice
  - game.architecture
  - game.vision
  - game.development-model
  - game.authority
---
# Ordivon Game

## Purpose

**Authoritative interactive worlds for people and Agents.**

Ordivon Game currently ships one executable world: **Station Zero**, a deterministic multi-Agent mission game. The player commands Engineer, Medic, and Security specialists through standing doctrine and consequential interventions rather than moving units directly.

## Current boundary

The registered executable remains Station Zero `station-zero@2` with Ruleset `station-zero-core@3`. Station Zero v3, Casefile, Last Light, and Echo Hunt are currently **Game Core research treatments**, not competing product stages. No new Ordivon Game product has been selected from the recent direction experiments. Canonical G0–G8 meanings remain exclusively those in `docs/DEVELOPMENT_MODEL.md`; research rounds do not redefine them.

## Start here

- [`docs/PRODUCT.md`](docs/PRODUCT.md) defines the current Station Zero product and player experience.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines the current executable architecture and state ownership.
- [`docs/VISION.md`](docs/VISION.md) defines the broader Game direction without turning possibilities into commitments.
- [`docs/DEVELOPMENT_MODEL.md`](docs/DEVELOPMENT_MODEL.md) defines how Ordivon classifies and develops games, where Agent-specific mechanisms fit inside the normal game lifecycle, and how Game consumes Studio production without taking over Studio authority.
- [`docs/STATION_ZERO_V3_CONTRACTION.md`](docs/STATION_ZERO_V3_CONTRACTION.md) records only Game-local contraction verdicts and reopen conditions; cross-project synthesis stays in Ordivon Computing.
- [`docs/GAME_CORE_RESEARCH_RESET.md`](docs/GAME_CORE_RESEARCH_RESET.md) reserves G0–G8 for the normal product lifecycle and defines Station Zero/Concept Lab/Casefile as research treatments rather than product-stage winners.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md) preserves the complete first seventeen foundation rounds across game form, mechanics, loops, player value, world, subjects, agency, time, economy, society, topology, and information without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R18.md`](docs/GAME_FOUNDATIONS_RESEARCH_R18.md) decomposes Need, Desire, Value, Preference, Utility, Goal and Commitment, defines minimum-sufficient motivational structures across game forms, and introduces Playable Motivation without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_MAP.md`](docs/GAME_FOUNDATIONS_RESEARCH_MAP.md) is the compact conceptual map for the R1–R18 foundations corpus and its cross-domain abstractions.
- [`docs/GAME_FOUNDATIONS_CONTINUATION.md`](docs/GAME_FOUNDATIONS_CONTINUATION.md) is the context-switch handoff; after R18 the next frontier is strategic interdependence in R19.
- [`docs/GAME_CORE_DIRECTION_SPACE.md`](docs/GAME_CORE_DIRECTION_SPACE.md) maps the early Core → Experience search space, missing dimensions, and experimental contract.
- [`docs/GAME_CORE_EXPERIMENT_FINDINGS.md`](docs/GAME_CORE_EXPERIMENT_FINDINGS.md) records what Station Zero, Casefile, Last Light, and Echo Hunt actually established without promoting a product winner.
- [`docs/GAME_CORE_EXPERIMENT_CASEFILE.md`](docs/GAME_CORE_EXPERIMENT_CASEFILE.md) retains exact Casefile engineering/blind-play evidence as an epistemic Game Core treatment.
- [`docs/STATION_ZERO_V3_PRODUCT.md`](docs/STATION_ZERO_V3_PRODUCT.md) preserves the stable human-facing v3 reference target and the historical G3/G4/G5 evidence produced by that programme.
- [`docs/STATION_ZERO_V3_VERTICAL_SLICE.md`](docs/STATION_ZERO_V3_VERTICAL_SLICE.md) preserves the historical machine/production slice, calibration evidence, and then-current G4 judgment; current product-stage meaning remains governed by the canonical Development Model and Game Core research reset.
- [`docs/STATION_ZERO_V3_PRODUCT_VALUE.md`](docs/STATION_ZERO_V3_PRODUCT_VALUE.md) owns G4 comparative product-design research, control/information/pressure/identity experiments, and Content Grammar v0.
- [`docs/STATION_ZERO_V3_DOMAIN_VALUE_GV.md`](docs/STATION_ZERO_V3_DOMAIN_VALUE_GV.md) owns the failure-driven GV consumer-validation lane, external failure transfer rules, live-vs-fixture ablation evidence, and the fresh-player boundary.
- [`docs/STATION_ZERO_V3_P0.md`](docs/STATION_ZERO_V3_P0.md), [`P1`](docs/STATION_ZERO_V3_P1.md), [`P2`](docs/STATION_ZERO_V3_P2.md), and [`P3`](docs/STATION_ZERO_V3_P3.md) define the exact encounter, reducer, durable execution, and planning/browser contracts beneath that target.
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

The next Station Zero form is retained under `src/station-zero-v3/`. Its stable product definition is [`docs/STATION_ZERO_V3_PRODUCT.md`](docs/STATION_ZERO_V3_PRODUCT.md); exact implementation contracts remain:

- [`docs/STATION_ZERO_V3_P0.md`](docs/STATION_ZERO_V3_P0.md): frozen encounter and content contract;
- [`docs/STATION_ZERO_V3_P1.md`](docs/STATION_ZERO_V3_P1.md): deterministic Turn reducer and pure replay contract;
- [`docs/STATION_ZERO_V3_P2.md`](docs/STATION_ZERO_V3_P2.md): durable SQLite Turn execution, exact receipt/recovery, and bounded Mission Control projection;
- [`docs/STATION_ZERO_V3_P3.md`](docs/STATION_ZERO_V3_P3.md): Commander Orders, bounded Agent planning, policy expansion, sealed three-faction Preview, explicit Commit, and browser first-playable.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
Target form: three-faction deterministic turn-based tactical encounter
P1: reducer and pure replay complete
P2: durable Turn authority and recovery complete
P3: isolated playable planning layer and /v3 browser complete
G3-era reference evidence: strategic viability, plurality, and bounded live-Agent realization accepted
Current research role: delegation / tactical Game Core reference experiment
New product selection: none
Canonical product stages: G0–G8 retain only DEVELOPMENT_MODEL meanings
Encounter budget: 20 Turns
```

The v3 reference experiment remains available through a separate API namespace, SQLite database, and browser surface. It is still absent from `src/registry.ts` and does not replace the current root product. Additional content is not implied by its technical maturity; changes should serve an explicit Game Core hypothesis or a later intentionally selected product.

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
Registered Station Zero: http://127.0.0.1:4173/
Station Zero v3 reference experiment: http://127.0.0.1:4173/v3
Game Core Concept Lab: http://127.0.0.1:4173/lab
Casefile epistemic experiment: http://127.0.0.1:4173/casefile
```

Browser acceptance journeys:

```bash
pnpm e2e
pnpm e2e:v3
pnpm e2e:lab
pnpm e2e:casefile
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

### Casefile research treatment

```text
GET  /api/casefile/catalog
GET  /api/casefile/runs
POST /api/casefile/runs
GET  /api/casefile/state
POST /api/casefile/action
```

Casefile is an executable epistemic/social-deduction research treatment with a separate SQLite store and exact state-derived action surface. Nonterminal public projections do not expose culprit, motive, reconstruction, or uninspected clue text. The current witness policy is deterministic; Casefile runtime makes no model calls. Its existence does not select a product or product stage.

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
    v3 content, Genesis, deterministic reducer, Planning/Turn authority, exact Game-owned execution evidence, Agent Context and Candidate admission, policy expansion, Play Service, recovery, and bounded projections

web-v3/
    isolated Station Zero v3 reference browser

src/casefile/, web-casefile/
    epistemic Game Core treatment: hidden incident content, deterministic witness policy, revision-fenced SQLite state, exact legal investigation actions, public projection and browser

web-lab/
    disposable Game Core direction treatments; not product authority or G-stage progression

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
