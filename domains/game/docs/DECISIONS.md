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
