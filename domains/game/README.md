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

- [`docs/PRODUCT.md`](docs/PRODUCT.md) — player experience and first-slice scope.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — component boundaries and execution flow.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — milestone graph and acceptance criteria.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — initial architectural decisions.
- [`AGENTS.md`](AGENTS.md) — operating rules for contributors and coding Agents.

## Current status

The repository is in **incubation**. The immediate objective is not a reusable game platform; it is one small, verifiable, genuinely playable vertical slice.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
