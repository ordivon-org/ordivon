---
schema_version: 1
id: game.authority
title: Game Content Authority
type: decision
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - maintainer
  - player
  - designer
  - builder
  - agent
updated: 2026-08-03
summary: Decision separating the registered Station Zero product, the unregistered v3 target specifications, long-range Game vision, machine truth, and historical evidence.
evidence_status: not_applicable
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.start
  - game.product.station-zero
  - game.architecture
  - game.vision
  - game.station-zero-v3.encounter
  - game.station-zero-v3.reducer
  - game.station-zero-v3.execution
---
# Game Content Authority

## Context

Game simultaneously contains one registered executable, one broader product vision, and an implemented but unregistered v3 replacement path. Treating the newest phase file as the whole product would confuse deployed behavior, target design, and future possibility.

## Decision

[`../README.md`](../README.md) is the canonical repository entry and must state which Scenario and Ruleset are registered. [`PRODUCT.md`](PRODUCT.md) owns the current Station Zero player experience and acceptance. [`ARCHITECTURE.md`](ARCHITECTURE.md) owns the registered executable architecture and state ownership. [`VISION.md`](VISION.md) owns long-range principles and possibilities but creates no feature commitment.

The accepted unregistered v3 target is jointly defined by [`STATION_ZERO_V3_P0.md`](STATION_ZERO_V3_P0.md) for encounter and content decisions, [`STATION_ZERO_V3_P1.md`](STATION_ZERO_V3_P1.md) for the pure deterministic reducer contract, and [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md) for durable Planning, execution, evidence, and recovery. These documents do not register v3 or replace the current browser and HTTP product.

`src/registry.ts`, source code, SQLite schema, deterministic tests, generated or retained receipts, replay verification, product acceptance scripts, and the running service remain stronger owners for exact executable registration, fields, transitions, and observed behavior. `AGENTS.md` governs repository work rather than product truth.

## Consequences

The current executable and v3 target can evolve without pretending they are already the same system. P0/P1/P2 phase-coded paths remain temporarily canonical because they contain active target contracts; later human-centered stable documents should supersede them explicitly after registration or redesign. Older milestones and evidence will be handled only after the higher-priority authority and implementation work is complete.

## Status

Accepted and active. Reopen when v3 is registered, the current executable is removed, a second world is admitted, or stable human-oriented specifications replace the phase-coded target set.
