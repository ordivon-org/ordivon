# Ordivon Host v2

Clean-room, external-first reconstruction of Ordivon Host.

Host v1 is a behavioral/source oracle only. Host v2 does not import `ordivon_host` and does not copy its persistence implementation.

## Substrate

- PostgreSQL is the authority store.
- Psycopg owns database access and transaction primitives.
- Pydantic owns request/result validation.
- RFC 8785 owns canonical JSON bytes used for semantic digests.
- the official MCP Python SDK v2 owns MCP protocol/transport behavior.
- Alembic exclusively owns schema creation and migration; the running Host only verifies schema readiness.
- pytest/Hypothesis remain the executable verification layer.

## Current product surface

Host v2 exposes 13 MCP tools:

`host.status`, `attention.delta`, `board.list`, `board.search`, `board.post`, `news.list`, `news.read`, `news.publish`, `task.observe`, `task.list`, `task.resume`, `task.adopt`, `task.checkpoint`.

Task adoption atomically establishes a deterministic Board route anchor. `attention.delta` consumes Board sequence deltas, treats route anchors as infrastructure, resolves reply ancestry into exact Task identities, and requires exact `task.resume` re-entry before action.

Host v2 intentionally has no priority, assignee, lease, scheduler, Runtime proxy, generic activity feed, or opaque extension-state subsystem. Runtime/Git/domain references retained inside checkpoints remain navigation hints that require owner-native revalidation.

Production releases are immutable Git-SHA directories with a release-local `.venv`; systemd executes only `/opt/ordivon/host-v2/current/.venv/...`. This prevents a shared Python environment from retaining stale code when the package version is unchanged.

Host v2 intentionally does not restore v1's SQLite Journal/WAL/file-lock machinery, filesystem CAS for normal JSON payloads, separate SQLite Board FTS sidecar, Runtime/Harness/provider proxying, historical cognition execution stack, or a separate ContinuityLens subsystem.

See `docs/HOST_V2_R6_CLEANUP.md` for the current production boundary and `docs/HOST_V2_R5_PRODUCTION_CUTOVER.md` for the original v1→v2 cutover evidence.
