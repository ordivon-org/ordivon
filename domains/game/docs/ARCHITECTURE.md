---
schema_version: 1
id: game.architecture
title: Architecture
profile: engineering
type: architecture
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - operator
  - agent
updated: 2026-09-12
summary: Current Station Zero v2 product architecture, explicitly enclosed as product implementation rather than Big Game infrastructure.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero@2
  - station-zero-core@3
related:
  - game.start
  - game.product.station-zero
  - game.ownership-boundary
  - game.authority
---
# Architecture

## Scope

This document describes the **registered Station Zero v2 product architecture**. It does not define reusable Big Game infrastructure. Cross-game ownership is governed by [`GAME_E2E_OWNERSHIP_BOUNDARY.md`](GAME_E2E_OWNERSHIP_BOUNDARY.md).

## Product architecture

Station Zero is a deterministic intervention-driven mission game. Its product implementation contains:

- deterministic World state and legal transitions;
- Engineer, Medic, and Security product roles and coordination policy;
- player doctrine, authority, intervention, and Mission Control projection;
- SQLite-backed product history and recovery semantics;
- product-specific replay, diagnosis, deployment profiles, and run comparison;
- a bounded Provider contract whose real execution is injected from outside the product;
- an HTTP/browser carrier for the current product.

These responsibilities are retained because they express Station Zero behavior, not because Ordivon Game owns generic equivalents.

## Authority flow

```text
Player / Browser
        ↓ doctrine, commands, approvals
Station Zero Mission Control
        ↓ bounded product state and intervention rules
Station Zero specialist coordination
        ↓ Contexts, Messages, Proposals, authority, coordination
Deterministic Station Zero World
        ↓ legal atomic Tick and authoritative state transition
SQLite product evidence
        ↓ exact recovery and product projections
Replay / Diagnosis / Comparison
```

There is no embedded generic Host authority in the current architecture. The earlier `src/host-contract/` subsystem and Game-owned Codex/Hermes provider execution were physically removed. Durable workflow execution and generic Agent execution are external concerns.

## Product state authority

| State | Sole product authority |
|---|---|
| rooms, actors, crew, inventory, systems, hazards, resources | Station Zero World |
| World revision, simulation Tick, mission result | Station Zero World |
| retained Commands, Events, snapshots, hash chains | Station Zero product persistence |
| specialist tasks/messages/decisions/grants/proposals/rounds | Station Zero specialist coordination |
| cognition output | immutable Provider result admitted through product validation |
| player view and forecasts | Station Zero Mission Control projection |
| replay, diagnosis, comparison | derived product projections over retained evidence |

No projection may become a second source of truth.

## World transition

```text
WorldState(revision N)
+ TickBatch(expected revision N)
→ validate identities, capabilities, preconditions, and conflicts
→ reserve shared resources
→ apply compatible intents atomically
→ advance environment once
→ evaluate terminal state once
→ verify invariants
→ WorldState(revision N+1) + TickEvent
```

The three-specialist limit, role capabilities, objectives, Mission Fronts, deployment profiles, and diagnosis rules are Station Zero rules. They are not a generic scheduler or Team framework.

## Provider boundary

The product owns only the semantic contract needed to obtain and validate a candidate decision. The default fixture provider is deterministic test/product apparatus. Process spawning, model credentials, HTTP transport, retries, provider pools, cooldowns, fallbacks, and provider-specific execution are not owned by Game and are injected externally when needed.

## Persistence and replay

Station Zero currently uses `node:sqlite`. SQLite owns database mechanics such as transactions, locking, WAL, constraints, and file persistence. Station Zero owns only its product-level meaning of World revisions, Commands/Events, recovery, exact replay, and atomic product evidence.

Historical `host_*` table or event names may remain only as retained-schema compatibility vocabulary. Their names do not establish a generic Host subsystem or Big Game ownership and are subject to later bounded migration/removal.

## HTTP carrier

The current local HTTP carrier exists to serve Station Zero and retained research apparatus. It is not a Big Game server framework. Research surfaces are opt-in and will be physically separated from the current product carrier during the enclosure migration.

## Verification

The current product architecture is verified by deterministic reducer/persistence tests, hash-chain/replay checks, product hardening tests, `pnpm check`, and browser acceptance journeys. Infrastructure graduation never implies fresh-player, Human, rights, or release standing.

## Repository constraint

No new module is admitted to Big Game merely because several files need somewhere to live. Product semantics remain with the product; generic mechanics go to mature external owners; historical compatibility is deleted or quarantined. Promotion to cross-game shared code requires the evidence test in [`GAME_E2E_OWNERSHIP_BOUNDARY.md`](GAME_E2E_OWNERSHIP_BOUNDARY.md).
