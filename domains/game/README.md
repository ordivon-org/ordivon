# Ordivon Game

**Agent-native games built on Ordivon Computing, Ordivon Host, and Ordivon Runtime.**

Ordivon Game explores games in which autonomous Agents are not decorative dialogue systems. They hold persistent goals, receive bounded observations, act through explicit capabilities, produce verifiable world effects, cooperate, fail, recover, and remain understandable to the player.

## First playable: Station Zero

The first vertical slice is a small, turn-based mission game:

- the player leads a remote mission-control team;
- three specialist Agents operate inside a damaged space station;
- the player assigns goals, tools, authority, and risk limits;
- Agents plan and act autonomously inside a deterministic world;
- the player approves dangerous actions, changes priorities, or cancels work;
- the mission ends with an evidence-backed outcome and a complete replay.

The intended experience combines:

```text
Agent Operations: delegation, authority, diagnosis, recovery
+
Agent Arena: bounded rules, team construction, scoring, replay
```

## M0 executable slice

The repository now contains the first executable boundary:

```text
browser
→ local HTTP service
→ typed restore_power command
→ deterministic world transition
→ SQLite event and snapshot commit
→ process restart
→ digest-verified replay
```

The current slice has one room and one Engineer. A fixture cognition adapter may select only an action already admitted by the current world context; it cannot mutate world state.

### Run

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

Useful commands:

```bash
pnpm demo      # persist, close, reopen, and replay one transition
pnpm check     # strict type check, browser syntax check, and tests
pnpm receipt   # isolated executable evidence receipt
```

Runtime dependencies remain zero; TypeScript and Node type definitions are development-only checks.

## System boundary

```text
Player and Web Client
        ↓
Deterministic Game World Kernel
        ↓
Ordivon Host adapter
Goal / Task / Context / Decision admission
        ↓
Ordivon semantic boundary
Effect / Dispatch / Observation / Verification / Fact
        ↓
Runtime and provider adapters
long work / model calls / artifacts / recovery
```

The model proposes high-level decisions. The authoritative world kernel owns maps, time, inventory, resources, movement, equipment requirements, damage, success conditions, and all final state transitions.

## Repository map

- [`src/world.ts`](src/world.ts) — authoritative deterministic transition.
- [`src/storage.ts`](src/storage.ts) — SQLite events, snapshots, recovery, and replay.
- [`src/provider.ts`](src/provider.ts) — structured cognition boundary and candidate admission.
- [`src/server.ts`](src/server.ts) — one local HTTP process and API.
- [`web/`](web/) — dependency-free browser control surface.
- [`test/`](test/) — world, persistence, provider, and HTTP conformance tests.
- [`docs/PRODUCT.md`](docs/PRODUCT.md) — player experience and first-slice scope.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — component boundaries and execution flow.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — milestone graph and acceptance criteria.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — architectural decisions.
- [`docs/M0-RECEIPT.md`](docs/M0-RECEIPT.md) — executable M0 evidence.
- [`AGENTS.md`](AGENTS.md) — operating rules for contributors and coding Agents.

## Current status

**M0 is implemented and under review.** The next milestone is M1: expand the one-room proof into a deterministic station scenario with resource trade-offs, additional actions, immutable event semantics, and scripted winning and failing policies—still without an LLM in the authoritative loop.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
