# M1.5 architecture hardening

M1.5 strengthens the deterministic foundation before M2. It is delivered as five reviewable pull requests.

1. **Run and version identity** — frozen M1 fixture, multi-Run storage, scenario/ruleset registry.
2. **Time model** — command sequence, world revision, simulation tick, and explicit tick batch.
3. **Replay and storage** — recovery/verification modes, sparse snapshots, hash chains, busy handling.
4. **Typed facts** — domain facts, verification receipts, retained raw state diff.
5. **Testing and measurement** — property/model tests, fault injection, coverage gates, policy-space report.

## PR1 status

Implemented:

- frozen `fixtures/m1-v1` compatibility corpus;
- `RunMetadata` and version registries;
- multi-Run SQLite schema;
- per-Run command identity, events, snapshots, recovery, and replay;
- Run list/create HTTP endpoints;
- exact version rejection tests.

The M1 winning and failing world digests remain unchanged.

## PR2 status

Implemented:

- typed `TickBatch` and `TickIntent`;
- separate command sequence, world revision, and simulation tick coordinates;
- journal envelopes retaining Tick identity around the unchanged M1 domain event;
- storage and replay through the versioned Ruleset Tick API;
- fail-closed multi-intent batches until M3 conflict semantics exist;
- compatibility parsing for PR1-era raw Event rows.

The frozen M1 v1 WorldEvent and terminal state digests remain byte-stable.

## PR3 status

Implemented:

- Genesis / interval-8 / terminal Snapshot policy;
- Recovery Replay from the newest Snapshot and Verify Replay from Genesis;
- independent Command and Event hash chains;
- PR2 database migration, hash backfill, and Snapshot pruning;
- typed `storage_busy`, `storage_corrupt`, and `storage_constraint` errors;
- SQLite busy timeout and HTTP error mapping;
- indexed recent-event tail reads;
- tamper, Snapshot deletion, and writer-contention tests.

A PR2 database with 26 Snapshots migrated to 5 Snapshots and retained the exact terminal digest.

## PR4 status

Implemented:

- `station-zero-core@2` with state-equivalent evidence enrichment;
- typed action, resource, hazard, health, and terminal Facts;
- command-specific Verification checks;
- retained raw state diff for low-level audit;
- readable browser Evidence rendering from Facts;
- v1/v2 state-digest equivalence tests;
- successful and failing v2 Fact coverage.

New Runs default to ruleset v2. Existing v1 Runs and the frozen M1 Fixture remain unchanged.

## PR5 status

Implemented:

- `fast-check` property tests over arbitrary legal and stale command sequences;
- independent model-based movement and environment validation;
- pure / persisted / recovered / verified execution equivalence;
- nine transaction fault-injection boundaries;
- explicit SQLite constraint, corruption, busy, legacy, and stream-divergence tests;
- 95% line / 90% branch / 95% function CI coverage gates;
- read-only mission scoring;
- fixed-seed random-policy and recovery-path perturbation measurement;
- final M1.5 receipt and clean-checkout evidence.

M1.5 is complete. The deterministic world can now be treated as the stable lower boundary for M2.
