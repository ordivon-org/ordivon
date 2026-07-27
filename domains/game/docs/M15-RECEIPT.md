# M1.5 architecture-hardening receipt

Date: 2026-07-27

## Claim

The M1 deterministic Station Zero prototype has been hardened into a versioned, multi-Run, recoverable, tamper-detecting and property-tested lower boundary suitable for M2 Host work.

M1.5 does not add real model cognition or more Agents. It removes ambiguity from identity, time, history, evidence and validation before those layers arrive.

## Delivery graph

```text
PR1 Run and version identity
  ↓
PR2 command / revision / Tick separation
  ↓
PR3 replay and storage integrity
  ↓
PR4 typed Facts and Verification
  ↓
PR5 property validation and measurement
```

Merged work before PR5:

| PR | Scope | Merge commit |
|---|---|---|
| #10 | Versioned multi-Run identity | `5ee4552de414a82a266586bf1e7d8dbc879dccfb` |
| #11 | Command, Revision and Tick semantics | `b374bdd0ad09441f1e1574f1f4b9c29546a14980` |
| #12 | Replay and storage integrity | `01f6b9895b084622c91b020d7155e144e09c7a92` |
| #13 | Typed Facts and Verification | `8b6cd2f8bae0e81658c9da7c02f2c252de9d5072` |

PR5 adds the final validation, coverage and measurement layer.

## Frozen compatibility evidence

`fixtures/m1-v1` retains:

- Genesis WorldState;
- 25-command winning journal;
- 10-command failing journal;
- exact v1 Events;
- every intermediate WorldState digest;
- a source-commit and version manifest.

The frozen terminal digests remain:

```text
victory
41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2

reactor_meltdown
4db74d8a1d2f4583031d5ba7f2fbe9310ef89ef3f57847d803eb70edab737ac1
```

Ruleset v2 adds Facts and Verification but produces the same WorldState digest after every v1 command.

## Durable identity and versions

One Run now binds:

```text
runId
scenarioId + scenarioVersion
rulesetId + rulesetVersion
stateSchemaVersion
seed
createdWithBuild
status
```

Commands, Events, Snapshots, idempotency and replay are scoped by Run. Several Runs may share one SQLite database and may reuse the same Command ID without collision.

Unknown scenario or ruleset versions fail closed.

## Time model

The former implicit equality has been replaced by separate contracts:

```text
commandSequence — accepted command order inside one Run
worldRevision   — optimistic-concurrency state version
simulationTick  — environmental time advancement
```

The kernel accepts a typed Tick Batch. Ruleset v1/v2 currently require exactly one Intent per Tick. Multi-Intent batches fail closed until M3 defines deterministic conflict semantics.

## Replay model

The replay source is:

```text
Run metadata
+ Genesis
+ accepted Command Journal
+ bound Ruleset
```

Journal Events are retained execution receipts. Snapshots are disposable recovery caches.

Two replay modes now exist:

| Mode | Start | Purpose |
|---|---|---|
| Recovery | newest valid Snapshot | restart and continuation |
| Verify | Genesis | full historical conformance |

The default Snapshot policy retains:

```text
Genesis
+ every 8 accepted revisions
+ terminal state
```

The 25-command winning Run therefore stores 5 Snapshots instead of 26.

A PR2 database containing 26 Snapshots migrated to 5 while preserving the exact terminal digest.

Deleting every non-Genesis Snapshot still allows full recovery from the Command Journal.

## Integrity and failure semantics

Commands and Journal Events maintain separate canonical hash chains:

```text
previousDigest → recordDigest
```

Verification detects:

- modified Command JSON;
- modified Event JSON;
- missing Event rows;
- equal-length but identity-misaligned streams;
- Snapshot digest corruption;
- a validly rehashed but historically incompatible Genesis;
- terminal digest divergence.

SQLite errors are mapped to:

```text
storage_busy
storage_corrupt
storage_constraint
```

Actual Node SQLite behavior required message-based classification in addition to error codes for:

- `database is locked`;
- `UNIQUE constraint failed`;
- `file is not a database`.

## Typed evidence

New Runs use `station-zero-core@2`.

Every accepted v2 Event contains:

```text
raw StateChange[]
+ typed WorldFact[]
+ VerificationReceipt
```

Facts cover:

- movement and waiting;
- pickup and consumption;
- system repair and power changes;
- hull sealing and crew stabilization;
- distress transmission;
- battery, oxygen, heat and health changes;
- mission success and failure.

Verification checks the action-specific observed result independently of any model claim.

## Transaction fault injection

Nine boundaries are exercised:

```text
before_begin
after_begin
before_command_insert
after_command_insert
after_event_insert
before_snapshot
after_snapshot
before_commit
after_commit
```

All eight pre-commit failures leave:

```text
0 Events
revision 0
Genesis Snapshot only
```

An `after_commit` uncertainty leaves exactly one committed effect. Reopening and retrying the same Command ID returns the existing result idempotently without consuming resources twice.

## Generated validation

`fast-check` adds:

- 200 arbitrary legal-sequence runs;
- 100 stale-command runs;
- 35 pure/persisted/recovered/verified equivalence runs;
- 100 independent model-based movement runs.

Properties include:

```text
listed actions are accepted
reducer input is immutable
accepted revision is monotonic
rejected stale input has no effect
resource and topology invariants always hold
pure = persisted = recovered = verified digest
```

The independent model reproduces movement, oxygen decline, heat rise, health damage and terminal ordering without reusing the production reducer.

## Automated verification

Current suite:

```text
52 tests
52 passed
0 failed
```

Coverage gate:

```text
lines     ≥ 95%
branches  ≥ 90%
functions ≥ 95%
```

Measured coverage:

| Scope | Lines | Branches | Functions |
|---|---:|---:|---:|
| All loaded source | 96.91% | 90.56% | 97.14% |
| `scenario.ts` | 100.00% | 99.12% | 100.00% |
| `world.ts` | 97.92% | 93.19% | 100.00% |
| `storage.ts` | 100.00% | 89.55% | 100.00% |

The CI gate applies globally; critical-module measurements are retained explicitly for review.

## Persistence receipt

Winning Run:

```text
Events: 25
Snapshots: 5
Recovery replayed commands: 0
Verify replayed commands: 25
Recovery digest = Verify digest = frozen victory digest
```

Representative local execution on Node v26.4.0 / linux-x64:

```text
25-command persisted execution: tens of milliseconds
terminal-Snapshot recovery: sub-millisecond to low-millisecond
Genesis verification replay: single-digit milliseconds
```

These are local conformance observations, not throughput claims.

## Read-only score

Scoring is an evaluation projection and does not alter WorldState, victory or replay.

| Baseline | Terminal result | Score |
|---|---|---:|
| Recovery | verified victory, turn 25 | 2203 |
| Communications first | reactor meltdown, turn 10 | 735 |

Components include verified victory, objective progress, health, oxygen, battery, reactor safety, operational systems and turn efficiency.

## Strategy-space measurement

Fixed-seed random measurement:

```text
1,000 Runs
992 reactor_meltdown
8 crew_lost
0 victory
score range 448–811
average score 565.067
```

Recovery-path single-action perturbation:

```text
103 alternative legal actions
64 recoverable victories
62.14% recoverable rate
```

The path is permissive early but tight late. From turn 19 onward, large action sets commonly contain only one alternative from which the recovery policy can still finish successfully.

Full machine-readable evidence is retained in `M15-MEASUREMENT.json`.

## What M1.5 proves

M1.5 establishes that:

1. world state does not depend on a Provider session;
2. old Runs bind exact executable semantics;
3. multiple Runs cannot contaminate one another;
4. Tick semantics are ready for a later multi-Intent conflict model;
5. restart is not equivalent to full historical verification;
6. Snapshots may be lost without losing the Run history;
7. retained history detects mutation and cross-stream divergence;
8. accepted effects produce typed, independently verified evidence;
9. transaction uncertainty converges through idempotency;
10. generated sequences agree across pure and persistent execution.

## Boundaries retained

M1.5 deliberately does not implement:

- durable Goal, Task, Attempt or Context state;
- real model calls;
- independent Agent observations;
- Agent memory;
- multi-Agent Intent ordering or conflict resolution;
- authority requests and approvals;
- production multi-process leadership;
- hosted authentication or tenancy;
- broad scenario content or balance changes.

These remain M2 and later work.

## M2 entry contract

M2 must build above, not through, this boundary:

```text
versioned Run
→ durable Goal and Task frontier
→ bounded persisted Context
→ external Provider call
→ retained Decision
→ fresh-world candidate admission
→ typed Effect / Dispatch
→ verified Facts
→ Task continuation after interruption
```

Model output remains outside authoritative state mutation and outside deterministic replay.
