# Host v2 R3 Direct Migration

Status: integrated candidate.

R3 directly migrates the currently useful Host product surfaces onto the external-first v2 substrate.
The migration carries product semantics, not the v1 persistence implementation.

## Public MCP surface

The official MCP Python SDK v2 server now exposes the same current 13 Host tool names:

- `host.status`
- `attention.delta`
- `board.list`
- `board.search`
- `board.post`
- `news.list`
- `news.read`
- `news.publish`
- `task.observe`
- `task.list`
- `task.resume`
- `task.adopt`
- `task.checkpoint`

## Migrated product responsibilities

- Task identity, goal identity, revision fencing, terminality, semantic checkpoints and handoff projection.
- Durable Board messages, replies, exact client-message identity and PostgreSQL-native search.
- Durable News publication revisions with expected-revision fencing.
- Opaque Task-scoped extension state with revision provenance.
- Global Host activity sequence for `attention.delta` navigation.

## Intentionally not migrated from v1 implementation

- SQLite Journal/WAL/file-lock machinery.
- filesystem CAS for ordinary Host JSON payloads.
- separate SQLite Board FTS sidecar.
- Host-specific lease objects for normal PostgreSQL revision arbitration.
- old cognition execution ownership.
- Runtime/Harness/provider proxying.
- ContinuityLens implementation as a separate subsystem.

PostgreSQL is the authority substrate. MCP remains transport. Foreign Runtime/Git/domain references inside
checkpoint payloads remain semantic claims/navigation hints and never become Host-owned current truth.

## Current compatibility note

R3 accepts the v1 public task/board/news parameter vocabulary. Historical opaque cursor bytes from v1 are not
reused; a caller holding an old v1 cursor must restart the bounded `task.list` or `news.list` query against v2.
This prevents old persistence-specific cursor encoding from becoming a v2 architecture constraint.
