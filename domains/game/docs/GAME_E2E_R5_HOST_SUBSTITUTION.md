---
schema_version: 1
id: game.e2e.r5.host-substitution
title: Ordivon Game E2E R5 — Host Substitution Decision
profile: engineering
lifecycle: active
source_role: migration-decision
visibility: public
owners:
  - ordivon-game
updated: 2026-09-10
evidence_status: source-current-plus-regression
readiness: PARTIAL
---
# Game E2E R5 — Host Substitution Decision

## 0. Current verdict

```text
DIRECT_GAME_IMPORTS_OF_LEGACY_HOSTSTORE = REMOVED
LEGACY_HOSTSTORE = QUARANTINED_COMPATIBILITY_IMPLEMENTATION
FULL_EXTERNAL_SUBSTITUTION = NOT_ADMITTED
```

This is a substitution-failure result, not permission to keep generic Game-owned Host infrastructure indefinitely.

## 1. Why direct substitution is not currently lossless

The current public Host surface observed by R5 is a continuity/control-plane surface: Task re-entry, Board collaboration, bounded Host status and external-news continuity. It validates its own Journal internally, but it does not expose a generic Game data-plane API for:

- writing an arbitrary Game-local retained Artifact;
- appending a Game-local journal event;
- opening one transaction that simultaneously mutates the Station Zero Game projection and the Host journal row in the same SQLite database;
- reading the exact Game-local artifact/journal representation currently retained by historical Runs.

Station Zero currently has evidence that depends on exactly that local atomic boundary. Examples include Team task projection CAS + journal head, authority grant consumption + journal evidence, prepared Round persistence, and interruption recovery. Replacing these with an unrelated remote write would create a dual-write window and invalidate existing response-loss and recovery evidence.

Therefore the current external Host is not a lossless replacement for the local transaction-coupled compatibility carrier.

## 2. M3a quarantine

R5 introduces:

```text
src/integration/game-evidence.ts
```

Game/domain consumers depend on the narrow `GameEvidencePort` rather than `HostStore`.

Current topology:

```text
Team / Deployment / Comparison / Replay / Mission Control
                    ↓
             GameEvidencePort
                    ↓
   LegacyEmbeddedHostEvidenceAdapter
                    ↓
        src/host-contract/journal.ts
```

`HostStore` is no longer imported by Game consumer modules. Compatibility internals under `src/host-contract/*` may still use it while the migration is incomplete.

The port does not grant persistence any Game semantic authority. Game World, Team, Deployment and player-facing meanings remain with their existing owners.

## 3. Required properties of a future replacement

A replacement must preserve all of the following before deletion is admitted:

```text
A. exact idempotent event identity;
B. immutable content-addressed artifact identity;
C. ordered retained event observation;
D. tamper/divergence detection;
E. transaction-safe relation to local Game authoritative state;
F. response-loss observation before redelivery;
G. restart/recovery replay;
H. historical retained-run readability;
I. no upgrade of technical evidence into Human, rights or product standing.
```

A remote API that has A-D but loses E-H is not a substitute.

## 4. Mature migration pattern under consideration

The strongest current candidate for cross-owner decoupling is a **transactional outbox / local commit + idempotent relay** pattern, not a synchronous dual write.

Potential topology:

```text
Game authoritative local transaction
  → Game projection/state
  → durable outbox row with stable effect/event identity
COMMIT
  ↓
relay observes committed outbox
  ↓
Host accepts idempotently
  ↓
Host receipt / observed identity
  ↓
local delivery status projection
```

The outbox row must be written in the same local transaction as the Game state it describes. Relay delivery may be at-least-once; the receiver therefore needs stable identity and idempotent admission. Ordering requirements must be explicit per Run.

External anchors:

- AWS Prescriptive Guidance, Transactional Outbox Pattern: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
- CloudEvents specification repository, stable 1.0.x line: https://github.com/cloudevents/spec

CloudEvents may be useful only as an external event-envelope vocabulary at the cross-owner boundary. It does not solve atomicity, Game authority, replay standing or Human evidence by itself.

## 5. Why R5 does not implement the outbox yet

An outbox changes the historical persistence topology. It must first be falsified against:

- pre-commit rollback;
- commit-success / response-loss;
- relay crash after Host acceptance but before local acknowledgement;
- duplicate relay;
- reordered relay;
- Host unavailability;
- process restart with pending outbox;
- local DB tamper/divergence;
- exact historical Run replay;
- comparison metrics that currently derive from retained event types.

Until those cases prove no judgment loss, `LegacyEmbeddedHostEvidenceAdapter` remains the compatibility implementation.

## 6. Human / rights boundary

Changing Host persistence or event transport cannot upgrade:

```text
Human UNKNOWN
rights INCONCLUSIVE
candidate NOT_YET_NOMINATED
```

for Veilwild, or equivalent Human/product standing for another Game. A transport receipt proves transport/retention only.

## 7. Next admitted engineering experiment

The next M3b experiment should be a **shadow outbox** with no authority to delete or replace the existing journal:

1. add an outbox row in the same transaction as one carefully selected Game event class;
2. relay to a fake/in-memory idempotent Host receiver first;
3. inject response loss, duplicates, reorder and restart;
4. prove existing Station Zero Game/journal results remain byte/semantic-equivalent;
5. only then bind a source-current external Host receiver if its interface actually supports the required idempotent identity and observation semantics.

The shadow experiment must not introduce a second Game truth store or change current release/product standing.

## 8. M3b shadow-outbox falsification result

R5 implemented a non-authoritative experiment at:

```text
experiments/game-e2e-r5/host-outbox-shadow.ts
```

It is deliberately not connected to Station Zero production authority. Its purpose is to test whether the migration shape can survive the failure classes that motivated the existing local Host journal.

Current falsification results:

```text
before-commit failure                         → state + outbox both rollback
commit-success / caller response-loss         → stable event identity recovers without state re-apply
Host accepts / local ack response-loss         → retry is idempotent; one Host effect
out-of-order delivery                          → receiver rejects
Host unavailable                               → Game state stays committed; outbox remains pending
process-style reopen                           → pending delivery resumes
retained payload tamper                        → digest verification fails closed
```

Test carrier:

```text
test/game-e2e-r5-host-outbox-shadow.test.ts
7/7 PASS on first R5 execution
```

This result only supports the **shape** of a future decoupling. It does not prove that the current external Host can serve as the receiver, because its present public surface still lacks the exact domain-event admission/observation contract required for this experiment.

The next M3c step, if admitted, is to define a receiver contract from current Host capabilities rather than from the legacy Game journal schema. No historical Host object is to be mirrored merely for compatibility convenience.
