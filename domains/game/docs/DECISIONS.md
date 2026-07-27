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

## D-019 — Command sequence, world revision, and simulation tick are distinct

`commandSequence` orders accepted commands inside one Run. `worldRevision` protects optimistic concurrency. `simulationTick` advances environmental time. M1.5 still admits exactly one intent per Tick, so their numeric values often coincide, but they are separate contracts and are persisted separately in the journal envelope.

## D-020 — Multi-intent Tick batches fail closed until conflict resolution exists

The kernel accepts a typed `TickBatch`, but station-zero-core v1 requires exactly one intent. This preserves the future multi-Agent shape without inventing ordering, collision, or shared-resource rules before M3.

## D-021 — Command Journal is the replay input

Run metadata, Genesis, the accepted Command Journal, and the bound Ruleset reproduce the world. Journal Events are execution receipts checked during verification. Snapshots are disposable recovery caches rather than an independent source of truth.

## D-022 — Recovery and verification replay are separate

Recovery starts from the newest valid Snapshot and replays only the command tail. Verification starts from Genesis and compares every reproduced Journal Event and digest with retained history.

## D-023 — Snapshot cadence is sparse and explicit

The default policy retains Genesis, every eighth accepted revision, and the terminal state. Old per-revision Snapshot databases are pruned during migration without deleting the Command/Event journal.

## D-024 — Command and Event streams are hash chained

Each retained Command and Journal Event records the previous record digest and its own canonical digest. Existing PR2 rows are backfilled only when integrity metadata is missing; already-populated hashes are never silently recomputed.

## D-025 — Ruleset v2 enriches evidence without changing world state

`station-zero-core@1` remains the frozen M1 compatibility reducer. `station-zero-core@2` wraps the same deterministic state transition and adds typed Facts plus a Verification receipt. New Runs default to v2; existing Runs replay with their bound version.

## D-026 — Raw state diff and domain facts coexist

`WorldEvent.changes` remains the low-level audit and replay diagnostic. `WorldEvent.facts` is the stable player/Host-facing semantic layer. `WorldEvent.verification` records command-specific checks and must succeed independently of model claims.

## D-027 — Generated tests protect the state machine

Example tests remain the readable contract, while `fast-check` properties exercise arbitrary legal sequences, stale decisions, pure/persisted/recovered equivalence, and an independent movement reference model. Generated failures must shrink to a reproducible counterexample.

## D-028 — Transaction fault points are explicit test seams

The storage adapter exposes development-only fault injection points around transaction begin, Command insert, Event insert, Snapshot write, and commit. Pre-commit faults must leave no effect. An after-commit uncertainty must converge through the same `runId + commandId` idempotency identity.

## D-029 — Mission score is a read-only evaluation projection

Mission scoring is derived from terminal WorldState and never participates in authoritative rules, victory, replay, or persistence. It exists to distinguish partial progress, resource quality, and safety outcomes before Agent evaluation begins.

## D-030 — Coverage thresholds protect the whole executable core

CI requires at least 95% line coverage, 90% branch coverage, and 95% function coverage across loaded source modules. Core achieved branch coverage is separately reviewed for `scenario.ts`, `world.ts`, and `storage.ts`; global coverage does not justify leaving a critical reducer untested.

## D-031 — Provider sessions do not identify the Engineer

The Engineer is represented by persistent Goal, Task, Attempt, semantic history, and current world binding. Codex and Hermes are replaceable cognitive calls. Their sessions, memories, tools, and transcripts never enter task continuity.

## D-032 — Host and World journals share SQLite but not authority

M2 stores Host state in the same SQLite database as the world for local atomicity and deployment simplicity. Host Journal, projections, and Artifacts use independent tables and an independent hash chain. Host records are not replay inputs for the deterministic World Kernel.

## D-033 — Models choose Operations, not primitive Commands

A Provider selects one exact strategic Operation. The Host compiles that Operation into deterministic movement, pickup, and action steps. This bounds model latency and cost while preserving the World Kernel as the only command authority.
