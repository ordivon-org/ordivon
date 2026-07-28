# Ordivon Game

**Agent-native games built on Ordivon Computing, Ordivon Host, and Ordivon Runtime semantics.**

Ordivon Game explores games in which autonomous Agents are not decorative dialogue systems. They hold persistent goals, receive bounded observations, act through explicit capabilities, communicate under world constraints, request authority, produce independently verified effects, fail, recover, and remain understandable to the player.

## Station Zero

Station Zero is a turn-based Agent Operations game:

- the player leads a remote mission-control team;
- Engineer, Medic, and Security operate inside a damaged space station;
- the player assigns Objectives, authority policy, Messages, and interventions;
- specialist Providers may differ or change during one Run;
- compatible specialist Intents execute in one atomic simulation Tick;
- every accepted Tick produces durable, replayable World and Host evidence.

```text
Agent Operations: delegation, authority, diagnosis, recovery
+
Agent Arena: bounded rules, team construction, scoring, replay
```

## Current executable: M3 multi-Agent team

M3 includes:

- 8 connected rooms and one deteriorating emergency;
- persistent Engineer, Medic, and Security identities;
- specialist-exclusive capabilities;
- one shared Mission Goal and Game Objective Graph;
- independent Host Tasks, actor-local Contexts, Proposals, and verification;
- typed local/radio Messages whose reachability can change the outcome;
- attribute-based `permit | require-human | deny` authority;
- exact, expiring, single-use player Grants;
- deterministic legal-subset selection for up to three specialist Proposals;
- one atomic Ruleset-v3 TickBatch with one environment advance;
- one Team Effect, Dispatch, TickEvent Observation, and per-Intent receipts;
- isolated Codex and Hermes cognition adapters;
- provider failure isolation and mid-Run Provider replacement;
- process recovery, immutable hash-chained journals, snapshots, and exact replay;
- synchronous Team APIs and a dependency-free browser mission-control panel.

M1, M1.5, M2, and M2.1 remain executable under their version-bound Scenario and Ruleset contracts.

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

The browser can create an M3 Run bound to:

```text
station-zero@2
station-zero-core@3
```

One SQLite database may hold several isolated Runs. Unknown Scenario or Ruleset versions fail closed.

Useful commands:

```bash
pnpm demo                  # deterministic M1 recovery policy
pnpm check                 # type check, browser syntax, tests, coverage gates
pnpm receipt               # frozen deterministic compatibility evidence
pnpm measure               # fixed-seed strategy measurements
pnpm m3:evaluate -- --mode fixture-security
pnpm m3:evaluate -- --mode fixture-engineer
pnpm m3:evaluate -- --mode codex
pnpm m3:evaluate -- --mode mixed
pnpm m3:evaluate -- --mode hermes
pnpm m3:evaluate -- --mode codex-hermes-switch
```

Runtime dependencies remain zero. TypeScript and Node type definitions are development-only checks.

## Authority boundary

```text
Player / Browser
        ↓ Messages, Objectives, approvals, pause, cancel
Host-conformant Team Coordinator
        ↓ actor Tasks, Contexts, Proposals, ABAC, legal subset
Replaceable specialist cognition
        ↓ exact Action candidate identity only
Team Tick Effect and stable Dispatch
        ↓ one atomic multi-Actor TickBatch
Deterministic Game World Kernel
        ↓ Facts, per-Intent Verification, terminal outcome
SQLite World + Host journals
        ↓ recovery, audit, exact replay
```

The authoritative World owns:

- maps, adjacency, actor location and health;
- simulation Tick and World revision;
- inventory and item conservation;
- battery-energy conservation;
- oxygen, heat, health, damage, and mission result;
- action legality and capability checks;
- atomic Tick conflict and shared-resource admission;
- success, failure, and final state transitions.

The Host layer owns continuity and coordination:

- Team Goal and actor Tasks;
- checked projections and short leases;
- bounded Context compilation;
- Provider invocation and exact Decision admission;
- typed Messages and delivery state;
- authority Decisions and Grants;
- Proposals, TickPlans, Effects, Dispatches, Observations, and waiting state.

A model cannot directly mutate World or Host state, invent an Actor, Action, target, Message delivery, Grant, or completion claim.

## API

M3 Team control:

```text
GET  /api/team/state
POST /api/team/initialize
POST /api/team/step
POST /api/team/run
POST /api/team/input
```

Player input actions:

```text
approve
deny
send-message
redirect-objective
pause
cancel
```

Verified replay reads:

```text
GET /api/replay/state?runId=...&revision=...
GET /api/replay/timeline?runId=...&beforeRevision=...&limit=...
GET /api/replay                                      # full verification compatibility API
```

Point-in-time replay selects the nearest retained Snapshot at or before the requested World revision, verifies Command/Event chains and identities, replays only the required tail, and writes no World or Host record. M2 single-Engineer endpoints remain available for older Runs.

## Repository map

### World

- [`src/model.ts`](src/model.ts) — state, primitive Commands, Team Tick, Events, Facts, and rejection contracts.
- [`src/scenario.ts`](src/scenario.ts) — versioned genesis, specialists, environment, mission evaluation, and invariants.
- [`src/world.ts`](src/world.ts) — parsing, admission, Ruleset reducers, atomic TickBatch, diffs, and available Actions.
- [`src/facts.ts`](src/facts.ts) — typed domain Facts and Verification receipts.
- [`src/registry.ts`](src/registry.ts) — Scenario and Ruleset version registry.
- [`src/storage.ts`](src/storage.ts) — multi-Run Command/Event hash chains, Snapshot caches, recovery, full verification, point-in-time reconstruction, and idempotency.
- [`src/replay/model.ts`](src/replay/model.ts) — read-only point-in-time replay result contract.

### Host and team

- [`src/host/`](src/host/) — M2 Goal, Task, Artifact, Journal, strategic Operation, Skill, Effect, Dispatch, and Observation path.
- [`src/team/model.ts`](src/team/model.ts) — M3 Team Goal, actor Task, Message, ABAC, Proposal, Round, TickPlan, and execution contracts.
- [`src/team/store.ts`](src/team/store.ts) — Host-conformant Team projections, leases, Messages, Decisions, and Grants.
- [`src/team/context.ts`](src/team/context.ts) — actor-visible knowledge and token-budget Context Blocks.
- [`src/team/authority.ts`](src/team/authority.ts) — attribute-based authority evaluation.
- [`src/team/providers.ts`](src/team/providers.ts) — strict Team Provider contract and deterministic Fixture policies.
- [`src/team/codex-cli.ts`](src/team/codex-cli.ts) — ephemeral read-only Codex cognition.
- [`src/team/hermes-cli.ts`](src/team/hermes-cli.ts) — isolated Hermes/DeepSeek cognition.
- [`src/team/execution-store.ts`](src/team/execution-store.ts) — Rounds, Context references, Proposals, TickPlans, Effects, Dispatches, and Observations.
- [`src/team/engine.ts`](src/team/engine.ts) — durable Team step/run loop, conflict selection, reconciliation, and verification.

### Product and evidence

- [`src/mission-control/`](src/mission-control/) — bounded product read model, deterministic intervention rules, and player-semantic execution service.
- [`src/server.ts`](src/server.ts) — local HTTP service, Mission Control API, and retained engineering APIs.
- [`web/`](web/) — dependency-free playable Mission Control product plus explicit `/debug.html` engineering surface.
- [`test/`](test/) — world, persistence, Host, provider, Team, Mission Control, HTTP, Web, fault, property, and evidence conformance.
- [`docs/M4-RECEIPT.md`](docs/M4-RECEIPT.md) — M4 implementation and acceptance evidence.
- [`docs/M4-EVALUATION.json`](docs/M4-EVALUATION.json) — frozen machine-readable Mission Control, recovery, intervention, and Web evidence.
- [`docs/M3-RECEIPT.md`](docs/M3-RECEIPT.md) and [`docs/M3-EVALUATION.json`](docs/M3-EVALUATION.json) — canonical multi-Agent and live Provider evidence.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — milestone dependency graph.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — architectural decisions and supersessions.

## Current status

**M4 is complete. M5 implementation is in progress; M5.0 and PR2A verified point-in-time replay are complete.**

M4 turns the verified M3 Team system into a bounded playable Mission Control product. The Fixture team wins in 18 verified Ticks through Mission Control APIs, the terminal view remains 16,465 bytes, player controls and pending review survive process replacement, intervention changes the admitted path, and the main product contains no primitive World controls or raw Host logs.

M5 closes the remaining play → replay → diagnose → compare → reconfigure → release loop. M5.0 provides deterministic Scenario Cases, truthful Run/evaluated-input identity, one backend product catalog, and complete revision paging. PR2A now reconstructs and verifies every retained World revision through a read-only API while preserving Snapshot-as-cache semantics. The typed Run Evidence Graph and Replay Frames remain the next implementation frontier.

See [`docs/M5-DESIGN.md`](docs/M5-DESIGN.md), [`docs/M5-PLAN.md`](docs/M5-PLAN.md), and [`docs/M1-M4-DEBT-AUDIT.md`](docs/M1-M4-DEBT-AUDIT.md). M3 remains the canonical live Codex/Hermes evaluation unless a future M5 study explicitly changes cognition semantics and receives a separate budget.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
