# Ordivon Game

**Agent-native games built on Ordivon Computing, Ordivon Host, and Ordivon Runtime.**

Ordivon Game explores games in which autonomous Agents are not decorative dialogue systems. They hold persistent goals, receive bounded observations, act through explicit capabilities, produce verifiable world effects, cooperate, fail, recover, and remain understandable to the player.

## Station Zero

The first product is a turn-based Agent Operations game with Arena-style constraints:

- the player leads a remote mission-control team;
- specialists operate inside a damaged space station;
- the player assigns goals, tools, authority, and risk limits;
- Agents eventually plan and act autonomously inside a deterministic world;
- every accepted action produces durable, replayable evidence.

```text
Agent Operations: delegation, authority, diagnosis, recovery
+
Agent Arena: bounded rules, team construction, scoring, replay
```

## Current executable: M1 deterministic scenario

M1 is a complete deterministic mission without model calls. It contains:

- 8 connected rooms;
- one Engineer with location, health, capabilities, and inventory;
- one deteriorating crew casualty;
- reactor cooling, life support, and communications systems;
- a hull breach;
- finite battery energy, oxygen, reactor heat, tools, spare parts, sealant, and a medkit;
- 8 typed command kinds;
- linked environmental escalation after every accepted action;
- explicit victory and failure conditions;
- one winning scripted policy and one strategically plausible failing policy;
- SQLite persistence, process recovery, immutable events, snapshots, and deterministic replay.

The current winning path restores cooling, collects supplies, seals the breach, restores life support, stabilizes the casualty, repairs communications, manages limited power, and sends a verified rescue signal in 25 turns.

## Run

Requirements:

- Node.js 26 or newer;
- pnpm 10.33.2.

```bash
pnpm install --frozen-lockfile
pnpm check
pnpm receipt
pnpm start
```

Open `http://127.0.0.1:4173`.

M1 uses world schema version 2. A database created by the M0 spike intentionally fails closed; remove `data/station-zero.sqlite3` before starting M1.

Useful commands:

```bash
pnpm demo      # run and persist the deterministic recovery policy
pnpm check     # strict type check, browser syntax check, and conformance tests
pnpm receipt   # compare winning, failing, persisted, recovered, and replayed paths
```

Runtime dependencies remain zero. TypeScript and Node type definitions are development-only checks.

Each persisted execution is an independent `Run` bound to an explicit scenario version, ruleset version, state schema, seed, and creating build. One SQLite database can hold several isolated Runs; unknown versions fail closed.

## Authority boundary

```text
Player and Web Client
        ↓ proposes one admitted command
Deterministic Game World Kernel
        ↓ resolves action + environmental tick
SQLite Event and Snapshot Journal
        ↓ supports restart and replay
Future Ordivon Host adapter
Goal / Task / Context / Decision admission
        ↓
Future model and Runtime adapters
```

The authoritative world owns:

- maps and adjacency;
- time and revision ordering;
- inventory and item conservation;
- battery-energy conservation;
- oxygen, heat, health, and damage;
- action legality and capability checks;
- success and failure;
- final state transitions.

A model may later select or propose actions. It never directly mutates this state. New Runs use `station-zero-core@2`, whose Events contain typed Facts and command-specific Verification while preserving the v1 WorldState trajectory.

## Repository map

- [`src/model.ts`](src/model.ts) — typed state, commands, events, and rejection contracts.
- [`src/scenario.ts`](src/scenario.ts) — Station Zero genesis, environmental progression, mission evaluation, and invariants.
- [`src/world.ts`](src/world.ts) — parsing, admission, atomic execution, state diffs, versioned Tick reducers, and available actions.
- [`src/facts.ts`](src/facts.ts) — typed domain Facts, Verification receipts, and readable evidence summaries.
- [`src/policies.ts`](src/policies.ts) — deterministic winning and failing policies.
- [`src/run.ts`](src/run.ts) — stable Run identity and version-bound execution metadata.
- [`src/registry.ts`](src/registry.ts) — scenario and ruleset version registry.
- [`src/storage.ts`](src/storage.ts) — multi-Run Command/Event hash chains, sparse Snapshots, recovery, verification replay, idempotency, and SQLite error mapping.
- [`src/host/model.ts`](src/host/model.ts) — durable Goal, Task, Attempt, Artifact, and Host Journal contracts.
- [`src/host/store.ts`](src/host/store.ts) — independent Host Journal, content-addressed Artifacts, and materialized projections.
- [`src/host/operations.ts`](src/host/operations.ts) — strategic Operation frontier and deterministic Skill compilation.
- [`src/host/context.ts`](src/host/context.ts) — canonical bounded Agent Context without transcript replay.
- [`src/host/execution-store.ts`](src/host/execution-store.ts) — durable Effects, Dispatches, and Observations.
- [`src/host/engine.ts`](src/host/engine.ts) — persistent Agent step/run loop, reconciliation, verification, and interruption recovery.
- [`src/providers/`](src/providers/) — exact Operation contracts, fixture baseline, ephemeral Codex, isolated Hermes, process limits, and technical fallback.
- [`src/provider.ts`](src/provider.ts) — bounded M1 candidate interface pending replacement by M2 Operation providers.
- [`src/server.ts`](src/server.ts) — local HTTP service and browser API.
- [`web/`](web/) — dependency-free mission-control surface.
- [`test/`](test/) — world, resource, policy, persistence, provider, and HTTP conformance.
- [`docs/M0-RECEIPT.md`](docs/M0-RECEIPT.md) — minimal executable-boundary evidence.
- [`docs/M1-RECEIPT.md`](docs/M1-RECEIPT.md) — deterministic scenario evidence.
- [`docs/M15-RECEIPT.md`](docs/M15-RECEIPT.md) — versioning, replay, evidence, fault, property-test, and measurement evidence.
- [`docs/M15-MEASUREMENT.json`](docs/M15-MEASUREMENT.json) — machine-readable fixed-seed strategy measurement.

## Current status

**M2 product loop is implemented.** The persistent Engineer can be initialized, stepped, run autonomously, inspected, and switched between Fixture, Codex, Hermes, or fallback Providers through HTTP and the browser. Live real-Provider evaluation and final receipts remain.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
