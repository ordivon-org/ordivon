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
updated: 2026-08-15
summary: Decision separating registered Station Zero execution, the current G-Series product-stage reset, the v3 reference experiment and its historical stage evidence, exact P0-P3 contracts, long-range Game vision, and machine truth.
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

[`../README.md`](../README.md) is the canonical repository entry and must state which Scenario and Ruleset are registered. [`PRODUCT.md`](PRODUCT.md) owns the registered Station Zero player experience and acceptance. [`ARCHITECTURE.md`](ARCHITECTURE.md) owns the registered executable architecture and state ownership. [`VISION.md`](VISION.md) owns long-range principles and possibilities but creates no feature commitment. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) owns the cross-game development process. [`G_SERIES_RESET.md`](G_SERIES_RESET.md) owns the post-dogfood stage rules; [`G_SERIES_PRODUCT_SEARCH.md`](G_SERIES_PRODUCT_SEARCH.md) owns G1–G4 candidate search/falsifiers; [`G_SERIES_SELECTION.md`](G_SERIES_SELECTION.md) owns the G5 selection; [`G_SERIES_G6_CASEFILE.md`](G_SERIES_G6_CASEFILE.md) owns current Casefile G6 candidate status and its open exit boundary. These records do not register Station Zero v3 or make Casefile a shipped product.

[`STATION_ZERO_V3_CONTRACTION.md`](STATION_ZERO_V3_CONTRACTION.md) owns only current Game-local contraction verdicts, negative regions, and reopen conditions. Ordivon Computing owns the cross-project synthesis that informed them. This record does not register v3, define World transitions, or make historical rejections permanent law.

[`STATION_ZERO_V3_PRODUCT.md`](STATION_ZERO_V3_PRODUCT.md) owns the stable human-facing definition of the unregistered v3 **reference target**: player fantasy, game form, Agent participation, core loop, product pillars, historical G3/G4/G5 evidence, production profile, and replacement boundary. It does not own the current cross-game product stage after the G-Series reset.

[`STATION_ZERO_V3_VERTICAL_SLICE.md`](STATION_ZERO_V3_VERTICAL_SLICE.md) owns the historical production/calibration claim set produced by the v3 programme and its then-current G4 exit judgment. Those receipts remain valid for what they measured, but `G_SERIES_RESET.md` supersedes their interpretation as current player-product stage authority.

[`STATION_ZERO_V3_PRODUCT_VALUE.md`](STATION_ZERO_V3_PRODUCT_VALUE.md) owns the G4 comparative product-value lane: mature analogue decomposition, transferable design laws, same-state/relevant-state product experiments, surfaced-control subtraction, and Content Grammar v0. It may narrow what the player is shown when evidence proves a control has no value, but it does not invent World mechanics merely to justify existing schema fields.

The exact v3 target contracts remain [`STATION_ZERO_V3_P0.md`](STATION_ZERO_V3_P0.md) for encounter and content decisions, [`STATION_ZERO_V3_P1.md`](STATION_ZERO_V3_P1.md) for the pure deterministic reducer contract, [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md) for durable Planning, execution, evidence, and recovery, and [`STATION_ZERO_V3_P3.md`](STATION_ZERO_V3_P3.md) for Commander Orders, bounded Agent planning, Plan Preview/Commit, the dedicated v3 API, and the separate `/v3` first-playable. These documents do not register v3 or replace the current root browser and HTTP product.

`src/registry.ts`, source code, SQLite schema, deterministic tests, generated or retained receipts, replay verification, product acceptance scripts, and the running service remain stronger owners for exact executable registration, fields, transitions, and observed behavior. `AGENTS.md` governs repository work rather than product truth.

For the unregistered v3 target, Agent cognition and Game action authority remain separate through Game-owned Candidate admission, exact Faction Plans, canonical Turn Batch admission, and authoritative World resolution. Historical P3 research also proved a stronger `Subject × Cognition × Actor × Intent` binding without importing Harness/World-private schemas; GC1 removed that dormant optional mechanism after confirming that no production caller enabled it and current product/recovery behavior was unchanged. The law remains; the unused binding machinery does not. Game still acquires no global Embodiment, Presence, Subject, or Cognition registry.

## Consequences

The registered Station Zero executable, v3 reference experiment, disposable Concept Lab, and selected Casefile candidate are deliberately separate. `G_SERIES_G6_CASEFILE.md` is the current frontier: G0–G5 are complete for this search, Casefile is the active G6 candidate, human G6 exit is open, and G7/G8 are not admitted. `STATION_ZERO_V3_PRODUCT.md` preserves v3 reference identity and historical programme evidence; P0/P1/P2/P3 remain canonical for their exact owner-local contracts.

## Status

Accepted and active. Reopen when v3 is registered, the current executable is removed, a second world is admitted, or stable human-oriented specifications replace the phase-coded target set.
