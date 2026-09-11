# Ordivon Host v2

Clean-room, external-first reconstruction of Ordivon Host.

Host v1 is a behavioral/source oracle only. Host v2 does not import `ordivon_host` and does not copy its persistence implementation.

## Substrate

- PostgreSQL is the authority store.
- Psycopg owns database access and transaction primitives.
- Pydantic owns request/result validation.
- RFC 8785 owns canonical JSON bytes used for semantic digests.
- the official MCP Python SDK v2 owns MCP protocol/transport behavior.
- Alembic owns schema migration.
- pytest/Hypothesis remain the executable verification layer.

## Current product surface

R3 directly migrated the current Host product surface to PostgreSQL:

`host.status`, `attention.delta`, `board.list`, `board.search`, `board.post`, `news.list`, `news.read`, `news.publish`, `task.observe`, `task.list`, `task.resume`, `task.adopt`, `task.checkpoint`.

Opaque Task-scoped extension state is retained as an internal service primitive.

Host v2 intentionally does not restore v1's SQLite Journal/WAL/file-lock machinery, filesystem CAS for normal JSON payloads, separate SQLite Board FTS sidecar, Runtime/Harness/provider proxying, historical cognition execution stack, or a separate ContinuityLens subsystem.

See `docs/HOST_V2_R3_DIRECT_MIGRATION.md`.
