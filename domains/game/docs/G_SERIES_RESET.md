---
schema_version: 1
id: game.g-series.reset
title: Ordivon Game G-Series Product Reset
type: decision
profile: product
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-16
summary: Current product-development authority for the post-dogfood reset: Station Zero is retained as a reference experiment, prior v3 G4/G5 stage labels are historical evidence rather than current product-stage authority, and the first true Ordivon Game product must re-earn stages from player value upward.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.development-model
  - game.vision
  - game.product.station-zero-v3
---
# Ordivon Game G-Series Product Reset

## Decision

Ordivon Game is reopening product development from the top of the game-design stack rather than continuing Station Zero content production by inertia.

```text
Station Zero
= retained executable reference experiment
+ strong Agent-game mechanism evidence
+ one candidate game form
!= presumed first true Ordivon Game product
```

Historical Station Zero v3 labels such as `G4 accepted` and `G5 admitted` remain useful records of the machine/runtime/production claims that were actually tested. They no longer define the current product-development stage for a player-facing game.

The current stage authority is this reset plus `DEVELOPMENT_MODEL.md`.

## Why the reset is required

The current development model says G3 exits only when independent play can reach meaningful success/failure and players can form a causal model of important decisions. Station Zero's historical G3/G4 advancement relied primarily on deterministic reachability, Agent strategy realization, browser E2E, machine UX calibration, comparative product analysis and production-pipeline evidence. Those are valuable, but they do not establish the missing player claims.

The repository therefore had a stage mismatch:

```text
engineering maturity: high
Agent-game mechanism maturity: high
player-value evidence: incomplete
```

The correction is stage re-earning, not code destruction.

## Station Zero status

Station Zero is retained because it proves real capabilities that future games may consume:

- authoritative World state and deterministic consequence;
- bounded observation / knowledge;
- cognition separated from admission and authority;
- mixed cognition tiers rather than one expensive model call per actor;
- simultaneous multi-actor consequence;
- durable persistence, replay and response-loss recovery;
- exact evidence and causal reconstruction;
- Game ↔ Studio ownership boundaries;
- the ability to falsify Agent behavior against cheaper policies.

Station Zero may continue to serve Game, Harness, Host, Runtime, Computing and Security research. Product work must not continue to add Station Zero missions, content axes, art scope or infrastructure merely because those mechanisms are mature.

## Reclassified stage

For current product-development purposes:

| Stage | Current judgment |
| --- | --- |
| G0 Define | **reopened** |
| G1 Preproduction / core design | **reopened** |
| G2 Kernel / graybox | Station Zero supplies strong reference evidence, but the selected product has not yet earned this stage |
| G3 Playable prototype | not currently exited for the selected product |
| G4 Vertical Slice | not currently admitted for the selected product |
| G5 Production | not currently admitted for the selected product |
| G6–G8 | not currently applicable |

No historical evidence is deleted by this reclassification.

## Current progression

As of the current round:

| G-Series step | State |
| --- | --- |
| G0 Reclassify and freeze | **complete** |
| G1 Product-space search | **complete** |
| G2 Experience foundations | **complete** |
| G3 Competing concepts | **complete** |
| G4 Cheap playable falsifiers | **complete** |
| G5 Select / kill | **complete — Casefile selected** |
| G6 True playable candidate | **active — implementation built; human exit open** |
| G7 True vertical slice | **not admitted** |
| G8 Production admission | **not admitted** |

Current detailed frontier is owned by `G_SERIES_G6_CASEFILE.md`.

## G-Series execution map

### G0 — Reclassify and freeze

- retain Station Zero as a reference experiment;
- remove current-stage authority from historical G4/G5 labels;
- freeze feature/content expansion during the product search;
- preserve exact mechanism evidence and executable behavior.

**Exit:** navigation and tests can distinguish reference-experiment maturity from current product maturity.

### G1 — Product-space search

Search materially different game forms by player value, not by installed technology. Study how mature games turn autonomous systems, incomplete information, relationships, persistence, systemic consequence and adaptive opposition into actual play.

**Exit:** several candidate experiences exist that would still make sense if the implementation stack were unknown.

### G2 — Experience foundations

Each candidate must state:

- player fantasy;
- desired emotional core;
- moment-to-moment verbs;
- anticipation/consequence loop;
- session arc;
- return motivation;
- why Agent participation earns complexity;
- cheapest baseline that could replace the Agent.

**Exit:** candidates can be compared as games rather than technologies.

### G3 — Competing concepts

Narrow to materially different concepts. Reject variants that are only Station Zero with different nouns.

**Exit:** each survivor has one small falsifiable game kernel and one explicit Agent-value ablation.

### G4 — Cheap playable falsifiers

Build the smallest player-operable treatment for each survivor. Keep presentation sufficient for comprehension but deliberately below vertical-slice fidelity.

**Exit:** every survivor can fail for a game reason, not only a technical reason.

### G5 — Select / kill

Compare real play traces, decision quality, immediate consequence, replay pressure, emotional/interpretive potential and Agent ablations. Sunk infrastructure is not a selection criterion.

**Exit:** one product candidate wins or all candidates are rejected. No selection is better than a false selection.

### G6 — True playable prototype

The selected product receives the first real G3-equivalent production effort. Independent players must complete the loop without developer intervention; technical execution must be quiet enough that gameplay findings dominate.

### G7 — True vertical slice

Only after G6 exits: representative near-final expression, content quality, Agent behavior, audio/visual language and repeatable Studio pipeline.

### G8 — Production admission

Only after the slice proves both player value and repeatable production. Content scaling begins here, not earlier.

## Product-selection rules

A candidate is favored when it creates a strong loop of:

```text
perceive something uncertain
→ make a meaningful choice
→ commit or act
→ receive legible consequence
→ update a model / relationship / plan
→ want another choice
```

Agent participation earns its place only when a cheaper scripted/policy baseline loses material player value in at least one of:

- strategic adaptation;
- believable independent behavior;
- social interpretation / trust;
- persistent character identity;
- adversarial variation;
- partial-information reasoning;
- creative collaboration;
- emergent histories that affect later play.

## Evidence boundary

Automated tests can prove:

- deterministic mechanics;
- distinct trajectories;
- legal action spaces;
- persistence/replay;
- presentation reachability;
- baseline-vs-Agent behavioral differences.

They cannot by themselves prove:

- delight;
- attachment;
- suspense;
- comprehension by a fresh player;
- desire to replay;
- market value.

Those claims remain `UNKNOWN` until appropriate player evidence exists.

## Current stop rule

Until G5 selection is complete, do not:

- register a new Station Zero version;
- expand Station Zero content breadth;
- start a campaign/meta progression system;
- migrate to 3D or a new engine;
- create a universal Game platform;
- scale Studio asset production;
- treat model latency/cost work as product progress unless a surviving concept needs live cognition.
