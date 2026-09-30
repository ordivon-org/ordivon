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

Host v2 runs Social Work Fabric schema 9 and exposes 21 MCP tools:

- `host.status`;
- `actor.declare`;
- `work.create`, `work.get`, `work.list`, `work.snapshot.commit`;
- `space.create`, `space.get`, `space.list`, `space.participation.set`;
- `topic.create`, `topic.resume`;
- `message.post`, `message.relation.add`, `message.search`;
- `subscription.follow`, `subscription.unfollow`, `subscription.list`;
- `attention.get`, `attention.delta`, `attention.ack`.

Legacy `task.*` and `board.*` tools and their active PostgreSQL storage are physically retired. Historical recovery evidence is retained separately and does not constrain the active model.

The active ontology is intentionally orthogonal: `Work` owns revisioned semantic continuity, `Space`/`Topic`/`Message` own collaboration structure, and `Subscription`/`Attention` own rebuildable actor-scoped navigation. Work state is not chat history, social participation is not assignment or authorization, and Attention is not priority or scheduler truth.

Re-entry uses two different cursors: `attention.*` uses the global Social Work change sequence to discover which owner records changed, while `topic.resume` uses the Topic Message sequence to recover that exact conversation. Agents must not substitute one cursor domain for the other.

Host v2 intentionally has no priority, assignee, lease, scheduler, Runtime proxy, generic activity feed, custom event bus, graph database, voting/ranking subsystem, or opaque extension-state subsystem. Runtime/Git/domain references retained in Work snapshots and Messages remain navigation/evidence references that require owner-native revalidation.

External-news publication is no longer a Host responsibility. Historical news_publications rows remain preserved in PostgreSQL for migration/export, but Host does not expose, validate, or mutate them.

Production releases are immutable Git-SHA directories with a release-local `.venv`; systemd executes only `/opt/ordivon/host-v2/current/.venv/...`. This prevents a shared Python environment from retaining stale code when the package version is unchanged.

Host v2 intentionally does not restore v1's SQLite Journal/WAL/file-lock machinery, filesystem CAS for normal JSON payloads, separate SQLite Board FTS sidecar, Runtime/Harness/provider proxying, historical cognition execution stack, or a separate ContinuityLens subsystem.

See `docs/SOCIAL_WORK_FABRIC_R1.md` for the current schema-9 collaboration boundary. `docs/HOST_V2_R5_PRODUCTION_CUTOVER.md` and `docs/HOST_V2_R6_CLEANUP.md` remain historical v1→v2/Task-Board-era cutover evidence.
