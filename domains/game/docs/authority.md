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
updated: 2026-08-14
summary: Decision separating the registered Station Zero product, the stable G4-admitted v3 product target, its exact P0-P3 contracts, long-range Game vision, machine truth, and historical evidence.
evidence_status: not_applicable
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.start
  - game.product.station-zero
  - game.product.station-zero-v3
  - game.architecture
  - game.vision
  - game.station-zero-v3.encounter
  - game.station-zero-v3.reducer
  - game.station-zero-v3.execution
  - game.station-zero-v3.planning
---
# Game Content Authority

## Context

Game simultaneously contains one registered executable, one broader product vision, and an implemented but unregistered v3 replacement path. Treating the newest phase file as the whole product would confuse deployed behavior, target design, and future possibility.

## Decision

[`../README.md`](../README.md) is the canonical repository entry and must state which Scenario and Ruleset are registered. [`PRODUCT.md`](PRODUCT.md) owns the current Station Zero player experience and acceptance. [`ARCHITECTURE.md`](ARCHITECTURE.md) owns the registered executable architecture and state ownership. [`VISION.md`](VISION.md) owns long-range principles and possibilities but creates no feature commitment. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) owns the cross-game development process: game classification, the Agentic Consequence Loop, stage gates, and the Game↔Studio production boundary. It does not register a product, define a current World transition, or make Station Zero mechanisms universal.

[`STATION_ZERO_V3_PRODUCT.md`](STATION_ZERO_V3_PRODUCT.md) owns the stable human-facing definition of the accepted unregistered v3 target: player fantasy, game form, Agent participation, core loop, product pillars, G-stage, G3 strategic/live-Agent evidence, production profile, and replacement boundary. It does not register v3 or define exact World transitions.

[`STATION_ZERO_V3_VERTICAL_SLICE.md`](STATION_ZERO_V3_VERTICAL_SLICE.md) owns the accepted G4 production claim set, calibration evidence, and G4 exit judgment. It may define media/UX production requirements and record browser/Studio integration evidence, but it does not supersede product identity, World rules, or P0–P3 execution contracts. Human-specific preference and market claims remain unproven without blocking bounded G5 Production under the cross-game G4 exit criteria.

[`STATION_ZERO_V3_PRODUCT_VALUE.md`](STATION_ZERO_V3_PRODUCT_VALUE.md) owns the G4 comparative product-value lane: mature analogue decomposition, transferable design laws, same-state/relevant-state product experiments, surfaced-control subtraction, and Content Grammar v0. It may narrow what the player is shown when evidence proves a control has no value, but it does not invent World mechanics merely to justify existing schema fields.

The exact v3 target contracts remain [`STATION_ZERO_V3_P0.md`](STATION_ZERO_V3_P0.md) for encounter and content decisions, [`STATION_ZERO_V3_P1.md`](STATION_ZERO_V3_P1.md) for the pure deterministic reducer contract, [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md) for durable Planning, execution, evidence, and recovery, and [`STATION_ZERO_V3_P3.md`](STATION_ZERO_V3_P3.md) for Commander Orders, bounded Agent planning, Plan Preview/Commit, the dedicated v3 API, and the separate `/v3` first-playable. These documents do not register v3 or replace the current root browser and HTTP product.

`src/registry.ts`, source code, SQLite schema, deterministic tests, generated or retained receipts, replay verification, product acceptance scripts, and the running service remain stronger owners for exact executable registration, fields, transitions, and observed behavior. `AGENTS.md` governs repository work rather than product truth.

For the unregistered v3 target, Agent cognition evidence and Game action authority remain separate. When exact Agent Action admission is enabled for one Planning Head, Game owns the normalized binding from Subject + Cognition + source-evidence identity to the exact Game Run, Planning, World revision/digest, Actor, and Intent digest. The upstream `sourceEvidenceDigest` is opaque provenance: Game does not parse Harness/World-private evidence schemas, and possession of that evidence alone does not authorize an Actor Intent. Game also does not acquire a global Embodiment, Presence, Subject, or Cognition registry.

## Consequences

The current executable and v3 target can evolve without pretending they are already the same system. `STATION_ZERO_V3_PRODUCT.md` now supersedes phase-coded files only for stable human-facing product identity; P0/P1/P2/P3 remain canonical for their exact owner-local contracts. Research labels such as R/GX/AF remain evidence/history rather than product stages. Older evidence is preserved through Git and bounded evaluation tools instead of competing product authorities.

## Status

Accepted and active. Reopen when v3 is registered, the current executable is removed, a second world is admitted, or stable human-oriented specifications replace the phase-coded target set.
