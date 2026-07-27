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
