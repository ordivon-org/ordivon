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
        ↓ doctrine, commands, Mission Control authorizations
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

Current authority escalation is product-role-specific: new decisions use `require-mission-control`, meaning the selected Station Zero doctrine requires authorization from the player's Mission Control role. Historical retained records may contain the superseded token `require-human`; it is accepted only as compatibility vocabulary for exact replay/recovery and must not be emitted by new decisions or generalized into a Human-over-Agent authority rule.

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

Historical `host_*` table or event names may remain only as retained-schema compatibility vocabulary. Their names do not establish a generic Host subsystem or Big Game ownership. Current retained identifiers include `host_artifacts`, `host_journal`, `host-event:*`, and replay kind `host-contract`; they may be read/written only to preserve the already-retained Station Zero evidence contract. New generic Host modules, `HostStore`, or new Host-owned lifecycle semantics are forbidden. Renaming these durable identifiers requires a versioned, lossless migration with replay/recovery equivalence; cosmetic churn alone is not sufficient reason to migrate retained data.

The active Station Zero coordination implementation is `StationZeroTeamCoordinator` under `products/station-zero-v2/src/team/coordinator.ts`. It is a three-specialist product component, not a reusable Team/Host framework.

## HTTP carrier

Station Zero v2 product code and its default HTTP/browser carrier are enclosed under `products/station-zero-v2/`. Retained research apparatus is enclosed under `experiments/`, with `experiments/research-preview/server.ts` available only as an explicit local research/E2E preview harness. Big Game owns no shared application server and has no root runtime source tree. Repository-mechanical hashing lives under `tools/`; product build identity stays with the product.

## Verification

The current product architecture is verified by deterministic reducer/persistence tests, hash-chain/replay checks, product hardening tests, `pnpm check`, and browser acceptance journeys. Infrastructure graduation never implies fresh-player Human-experience standing, rights standing, or release standing.

## Repository constraint

No new module is admitted to Big Game merely because several files need somewhere to live. Product semantics remain with the product; generic mechanics go to mature external owners; historical compatibility is deleted or quarantined. Promotion to cross-game shared code requires the evidence test in [`GAME_E2E_OWNERSHIP_BOUNDARY.md`](GAME_E2E_OWNERSHIP_BOUNDARY.md).
