# Initial decisions

## D-001 — Repository name

Use `ordivon-game` as the product and experimentation repository. Do not create a generic `ordivon-games` platform before one playable game exists.

## D-002 — License

Use Apache License 2.0 for source code and repository-authored documentation unless a path explicitly declares different third-party terms.

Reason: the project is intended to remain permissively reusable while preserving patent-grant and notice obligations appropriate for infrastructure-oriented work.

## D-003 — First product form

Build an Agent Operations game with Arena-style bounded missions, construction choices, scoring, and replay.

Do not begin with a persistent Agent Society. Society remains the long-horizon direction after small-team autonomy is stable and understandable.

## D-004 — Web first

Use a browser-based 2D or graph interface for the first playable. Avoid Unity, Unreal, and asset-heavy pipelines until the core loop proves itself.

## D-005 — Deterministic world before cognition

The first executable milestone contains no LLM. The game world, typed actions, failure semantics, resource constraints, and replay must work with scripted policies first.

## D-006 — Model outside authoritative state

Models may propose plans and candidate actions. They never directly own or mutate authoritative game state.

## D-007 — Reuse concepts, not accidental deployment topology

Reuse the semantics of Ordivon Computing, Host, and Runtime. Do not send every in-world action through a remote MCP boundary merely because that boundary exists in the current infrastructure.

## D-008 — One process before services

Start with modular packages in one local service and one database where practical. Split services only after measured requirements justify distributed boundaries.

## D-009 — Replay is a primary feature

Every admitted world command, relevant context identity, provider decision, result, and verification receipt must support inspection. Replay is required for gameplay mastery, debugging, research, and conformance.

## D-010 — No premature platform extraction

Do not create `ordivon-world`, a general workflow DSL, a modding SDK, or a universal multi-Agent scheduler before the first playable demonstrates repeated use.

## D-011 — M0 implementation stack

Use one Node.js 26 process for the first executable slice:

- TypeScript source executed through Node's native type stripping;
- strict TypeScript 7 static checking in development and CI;
- Node's built-in `node:http`, `node:test`, cryptography, and `node:sqlite` modules;
- one SQLite database for admitted commands, immutable events, and world snapshots;
- a dependency-free HTML, CSS, and browser JavaScript surface;
- one typed provider interface with a deterministic fixture implementation;
- source modules under `src/` rather than premature workspace packages or services.

The runtime has no third-party dependencies. `typescript` and `@types/node` are development-only dependencies.

The spike falsified unrestricted native TypeScript: Node's strip-only execution rejects syntax that requires transformation, such as constructor parameter properties. Production source therefore uses erasable TypeScript syntax and CI performs a separate strict type check.

React, a bundler, independent services, and reusable packages remain deferred until actual UI or deployment pressure requires them.

## D-012 — One controllable Agent in M1

M1 keeps one Engineer as the only acting Agent. The casualty is a world entity rather than an autonomous Agent.

Reason: M1 must establish deterministic gameplay, conservation, failure progression, and replay before M3 introduces independent observations, communication, authority conflict, and concurrent Agent intent.

## D-013 — Every accepted command advances the world

Movement, pickup, repair, switching power, medical stabilization, sealing, signalling, and waiting each consume one turn. Environmental hazards advance after every accepted command.

Reason: time becomes a common scarce resource across navigation, repair, rescue, and power management. Routine actions therefore participate in the strategy rather than existing outside the world clock.

## D-014 — Explicit conservation ledgers

Finite battery energy and consumable items use visible initial, remaining, and consumed quantities. World invariants check conservation after every accepted command and during recovery.

Reason: a deterministic strategy game requires stronger guarantees than narrative plausibility. Resources must not be created or erased by model output, UI behavior, retries, or replay.

## D-015 — Scripted policies are scenario proofs, not production AI

The recovery policy proves one feasible winning trajectory. The communications-first policy proves that an individually reasonable local objective can cause global failure through reactor escalation.

They are executable acceptance witnesses and regression tools. They are not intended to become the player's final autonomous team logic.

## D-016 — Run is the durable execution boundary

One `Run` identifies one independent game-world execution. Commands, events, snapshots, idempotency, recovery, and replay are scoped by `runId`. A database may contain several Runs without sharing command identity or world state.

## D-017 — Scenario, ruleset, and state-schema versions are distinct

Every Run binds `scenarioId + scenarioVersion`, `rulesetId + rulesetVersion`, `stateSchemaVersion`, seed, and creating build. Opening or replaying a Run resolves these exact versions through registries and fails closed when a version is unavailable.

## D-018 — M1 v1 is a frozen compatibility fixture

`fixtures/m1-v1` retains genesis, successful and failing command journals, events, per-step digests, and a manifest bound to the M1 source commit. Later architecture work must execute this fixture byte-for-byte or declare an explicit migration.
