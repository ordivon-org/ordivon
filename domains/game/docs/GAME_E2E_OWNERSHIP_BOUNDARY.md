---
schema_version: 1
id: game.ownership-boundary
title: Game E2E Ownership Boundary
type: authority
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-09-12
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.start
  - game.architecture
  - game.development-model
  - game.authority
---
# Game E2E Ownership Boundary

## Rule

Ordivon Game is a game-domain development, research, and evaluation environment. It is **not** a reusable Game Framework and does not own generic runtime infrastructure merely because one current product needs it.

## Big Game owns

- Game-specific lifecycle semantics and the G0–G8 stage projection;
- Game Development Core responsibilities and evidence semantics;
- player/game evaluation semantics and evidence boundaries;
- Game-domain research, foundations, reference analysis, and reusable design knowledge;
- product-selection and Game-specific interpretation rules.

These are semantic and evaluative responsibilities. They do not imply a service, database, scheduler, engine, or runtime library.

## Big Game does not own

- game engines or generic world engines;
- generic persistence, event stores, or databases;
- generic Team/Agent frameworks or schedulers;
- provider process/transport execution;
- durable workflow execution;
- generic replay frameworks;
- generic deployment frameworks;
- generic comparison engines;
- generic HTTP/application servers;
- telemetry/observability infrastructure;
- multiplayer/backend infrastructure;
- asset-production pipelines;
- release/distribution infrastructure.

Those concerns belong to the concrete product or to mature external owners such as the selected engine/platform, SQLite/PostgreSQL when appropriate, Runtime, Temporal, Operations/observability systems, Artifact/Engineering, and Distribution.

## Product enclosure rule

A concrete game owns the implementation required to realize that game. Station Zero-specific World state, specialist coordination, Mission Control, replay/diagnosis, deployment profiles, comparison logic, persistence semantics, and evidence projection are therefore Station Zero product implementation unless independently proven otherwise.

A future game is allowed to use none of those mechanisms.

## Anti-speculative-abstraction rule

A capability may be promoted from a product into Big Game shared code only when all of the following are true:

1. at least two materially different real games independently require the same irreducible Game-domain semantic;
2. the commonality is demonstrated by production/evidence rather than anticipated future reuse;
3. a mature external owner cannot already satisfy the mechanical responsibility;
4. extracting the capability does not erase product-specific semantics or create a second source of truth;
5. the abstraction survives deletion of either contributing product.

Two products are only minimum evidence, not automatic admission.

## Acceptance falsifier

Big Game violates this boundary if adding a materially different game requires that game to adopt Station Zero's Team, Mission Control, replay, SQLite persistence, Agent/provider, or server architecture.

Deleting Station Zero must leave the Game development/research/evaluation environment coherent.
