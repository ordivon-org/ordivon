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
