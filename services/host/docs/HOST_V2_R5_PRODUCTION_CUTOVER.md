# Host v2 R5 production cutover

Host v2 keeps only durable Agent work continuity, collaboration records, and exact re-entry navigation. PostgreSQL is the authority substrate; Runtime, Git, providers and domain systems remain independent current-truth owners.

## Verified semantic boundary

R5 retains Task identity, revisioned WorkingCheckpoint history, exact-revision checkpoint writes, response-loss replay, terminality, Board collaboration, Board lexical search, deterministic Board-to-Task route anchors, Board-derived attention/re-entry navigation, News publication history, and opaque extension-state retention.

R5 does not restore the v1 SQLite Journal, filesystem CAS, Host leases, generic Event Store, HostKernel, Board FTS sidecar, ContinuityLens subsystem, Runtime/Harness proxying, scheduler/priority semantics, or Host-owned database backup machinery.

## Destructive hardening results

A fresh PostgreSQL 18 database upgraded through Alembic 0001→0002→0003 passes the complete Host v2 suite, including same-revision races, response-loss replay, rollback, terminality, MCP vertical slices, scope-bound pagination, filtered Board pagination, reserved route-anchor squatting rejection, exact Board→Task attention routing, immutable extension history, and input boundary checks.

`attention.delta.afterSequence` remains a Board sequence. It derives navigation only and requires exact `task.resume` re-entry before action. It is not an activity-log cursor, inbox, priority surface, assignment surface, or domain truth.

## v1 semantic migration

`scripts/migrate_v1_semantics.py` exports from one frozen SQLite snapshot plus its immutable CAS and imports only consumer-visible semantics into an empty Host v2 PostgreSQL database. Long-lived dual write is prohibited.

The full production-state rehearsal migrated:

- 2,025 Tasks;
- 14,412 recoverable WorkingCheckpoint revisions;
- 15,640 Board messages;
- 14 News publications;
- zero extension-state rows.

Five earliest v1 Task revision-1 rows were descriptor-only adoption seeds with no WorkingCheckpoint. They are intentionally not fabricated in v2. Those five Task lineages are compacted by one revision and each migrated record preserves its `sourceRevision`. The export manifest records the omission count explicitly.

Checkpoint semantic digests are directly compatible. Historical Board and News public digests are retained by reproducing the legacy canonical envelope digest contract in PostgreSQL; the filesystem CAS is not retained as a runtime dependency. Historical Board and News identities replay as `existing` with unchanged digests after migration.

The full rehearsal passed semantic equivalence verification and `host.status(detail=history)` with every PostgreSQL-native integrity check green.

## Operations

The running Host process does not create or migrate schema. Alembic is sole schema authority. Runtime and migration accept the same `ORDIVON_HOST_V2_DSN`; an explicit SQLAlchemy URL remains an optional override.

Host v2 HTTP deployment binds loopback only and uses MCP Streamable HTTP. External publication belongs to the existing Cloudflare Tunnel/Access layer. PostgreSQL durability, WAL archiving, backup and PITR remain owned by the workstation PostgreSQL/pgBackRest platform.

The v1 state root remains rollback/migration evidence and must not be deleted as part of cutover.
