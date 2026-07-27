# M1 deterministic world receipt

Date: 2026-07-27

## Claim

Station Zero is now a complete deterministic mission with meaningful resource and timing trade-offs before any real model provider is introduced.

A clean checkout can:

- execute all eight command kinds;
- reach a verified victory through one policy;
- reach a causally understandable failure through another policy;
- conserve energy and item quantities after every accepted command;
- persist a 25-event mission;
- stop and restart the service;
- replay the complete mission to the identical terminal digest.

## Scenario

```text
8 rooms
1 Engineer
1 injured crew member
3 damaged systems
1 hull breach
56 battery units
3 spare parts
1 sealant
1 medkit
28-turn limit
```

Environmental effects advance after every accepted action:

```text
powered-system battery draw
→ oxygen change
→ reactor heat change
→ health change
→ terminal evaluation
```

## Command surface

```text
move
pickup_item
repair_system
set_power
seal_hull
stabilize_crew
send_distress
wait
```

Both scripted trajectories together execute every command kind.

## Verification commands

```bash
pnpm install --frozen-lockfile
pnpm check
pnpm receipt
rm -rf data
pnpm demo
pnpm demo
```

A separate live HTTP test executed the full recovery policy through `/api/state` and `/api/actions`, terminated the server, restarted it with the same SQLite database, and verified `/api/replay`.

## Test result

```text
14 tests
14 passed
0 failed
```

Covered properties include:

1. symmetric and connected station graph;
2. fixed world seed and deterministic pathfinding;
3. stale-revision rejection without mutation;
4. non-adjacent movement rejection without mutation;
5. damaged systems cannot be powered;
6. typed item transfer and consumption;
7. item conservation ledger;
8. battery-energy conservation ledger;
9. all eight M1 command kinds;
10. winning policy and terminal objectives;
11. linked reactor-meltdown failure policy;
12. identical repeated-policy events and digests;
13. full SQLite mission persistence and process recovery;
14. command identity idempotency and conflicting reuse rejection;
15. browser HTTP action and replay path;
16. provider candidate-set containment retained for M2.

## Successful trajectory

```text
status: victory
reason: rescue_signal_verified
turn: 25 / 28
battery remaining: 6 / 56
oxygen: 70
reactor heat: 66
terminal digest:
41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2
```

The path:

1. repairs and powers reactor cooling;
2. retrieves the remaining parts and sealant;
3. seals the hull breach;
4. repairs and powers life support;
5. disables cooling after heat is controlled to preserve power;
6. retrieves the medkit and stabilizes the casualty;
7. repairs and powers communications;
8. transmits the distress signal.

## Failing trajectory

```text
status: failure
reason: reactor_meltdown
turn: 10
terminal digest:
4db74d8a1d2f4583031d5ba7f2fbe9310ef89ef3f57847d803eb70edab737ac1
```

The communications-first policy repairs and powers communications and sends a signal, but ignores cooling. The reactor reaches 100 heat and the mission fails. This establishes a visible local-versus-global prioritization failure.

## Persistence and replay

The successful mission retained 25 canonical commands, events, and snapshots.

```text
pure-policy digest
= persisted terminal digest
= recovered digest after process restart
= replay digest
= 41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2
```

The live HTTP run produced the same result after a full service stop and restart.

## Determinism batch

A Runtime-executed batch performed 1,000 successful-policy runs and 1,000 failing-policy runs:

```text
2,000 total runs
1 unique successful digest
1 unique failing digest
```

This is a deterministic conformance result for the fixed scenario and policies, not a performance benchmark.

## Acceptance mapping

| M1 requirement | Evidence |
|---|---|
| Station graph and clock | 8-room symmetric graph; one turn/revision per command |
| Position and inventory | Engineer location and conserved room/Agent inventories |
| Power and oxygen | finite battery ledger; life-support and breach progression |
| Health | Engineer and casualty health progression |
| Communications | damaged, repairable, power-gated distress system |
| Equipment integrity | three systems move from 0.35 to 0.90 through repairs |
| Typed atomic actions | eight discriminated commands and explicit rejection codes |
| Linked emergency | heat, oxygen, health, and power advance together |
| Immutable events and snapshots | canonical SQLite event/snapshot journal |
| Deterministic replay | 25-event digest equality after restart |
| Winning policy | turn-25 verified rescue |
| Failing policy | turn-10 reactor meltdown |
| Resource conservation | checked after every accepted state |
| Meaningful trade-offs | hazard priority and cooling-versus-remaining-power decisions |

## Boundaries retained

M1 does not claim:

- durable Host Goal or Task state;
- real model cognition;
- independent Agent observations;
- multiple autonomous Agents;
- authority requests or player approval;
- hidden information;
- production concurrency;
- content-complete game status.

Those remain M2–M5 work.

## Next frontier

M2 should preserve the exact world contract while adding:

```text
durable Goal
→ Task frontier
→ persisted bounded Context
→ replaceable provider call
→ current-world candidate admission
→ typed Effect and Dispatch identity
→ verified Task outcome
→ fresh-process continuation
```
