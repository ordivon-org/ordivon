# M0 executable receipt

Date: 2026-07-27

## Claim

A clean checkout can run one deterministic room-state transition, persist it in SQLite, close and reopen the process, reproduce the terminal state from retained commands, and display the recovered state through a browser-facing HTTP service.

## Selected stack

```text
Node.js 26
+ erasable TypeScript source
+ strict TypeScript 7 checker
+ node:sqlite
+ node:http
+ static HTML/CSS/JavaScript
+ pnpm lockfile
```

Runtime third-party dependency count: **0**.

Development dependencies:

- `typescript`;
- `@types/node`.

## Executed verification

```bash
pnpm check
pnpm receipt
pnpm demo
pnpm demo
```

A separate live-process test performed:

```text
start service
→ read browser page and initial API state
→ request structured provider proposal
→ submit restore_power
→ terminate service
→ restart with the same SQLite database
→ read recovered state
→ verify replay digest
```

## Test result

```text
7 tests
7 passed
0 failed
```

Covered properties:

1. deterministic `restore_power` transition;
2. stale revision rejection without partial mutation;
3. SQLite persistence and fresh-process recovery;
4. replay from genesis plus admitted commands;
5. idempotent command identity;
6. conflicting reuse of a command identity fails closed;
7. structured provider candidate admission;
8. invented provider actions and stale contexts are rejected;
9. static Web surface and HTTP action path.

## State receipt

Initial world digest:

```text
a68662fb3e09c94eeb114bace4800f059dda2329e14a666876ee705f097213fb
```

Terminal persisted, recovered, and replayed digest:

```text
78ca8fba39b065ee81fb1b574382ab567af0751c095cbb112cf247191335725a
```

The terminal digest remained identical after a full service stop and restart.

Representative isolated run on `linux/x64`, Node `v26.4.0`:

```text
admitted events: 1
apply status: accepted
replay verified: true
apply: sub-millisecond to low-millisecond local range
replay: sub-millisecond to low-millisecond local range
```

These timings are not a benchmark claim; they only establish that the selected local boundary adds negligible cost at M0 scale.

## Acceptance mapping

| M0 requirement | Evidence |
|---|---|
| Minimal Web UI | `web/`, static-page HTTP integration test, live page fetch |
| Deterministic world update | pure `applyWorldCommand`, stable terminal digest |
| SQLite persistence | `GameStore`, process restart recovery |
| Snapshot and replay | genesis snapshot + ordered commands + digest checks |
| Structured provider adapter | bounded context, exact candidate ID admission |
| Selected stack | D-011 and committed lockfile |
| Clean-checkout command | `pnpm install --frozen-lockfile && pnpm check` |

## Boundaries retained

M0 does not claim:

- a complete Station Zero scenario;
- a real model provider;
- durable Host Goal and Task state;
- multi-Agent scheduling;
- resource conservation across several systems;
- player-ready visual design;
- production concurrency semantics;
- general game-engine or platform status.

Those belong to M1 and later milestones.

## Next frontier

M1 should extend the same world authority rather than replace it:

- station graph and several rooms;
- power, oxygen, health, communications, inventory, and equipment integrity;
- several typed actions and explicit precondition failures;
- linked failure progression;
- resource conservation tests;
- scripted winning and failing policies;
- deterministic replay across a complete mission.
