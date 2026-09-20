# Host v2 External-First Engineering E2E — R1

Status: ACTIVE

## Direction

Host v1 is frozen as a behavioral oracle. Host v2 is built from mature external components first.
A v1 concept may enter v2 only after a real consumer or adversarial test fails without it and the failure
cannot be solved by the selected external substrate.

## R1 external substrate

- PostgreSQL 18.x: authority, transactionality, concurrency, JSONB, search when needed.
- Psycopg 3: database driver and transaction API.
- Pydantic v2: typed API validation and schema generation.
- RFC 8785/JCS: canonical JSON bytes for semantic digests.
- Alembic: database schema migration.
- official MCP Python SDK v2: MCP schemas, tool registration and transport.
- pytest + Hypothesis: deterministic and state/property verification.
- Testcontainers: admitted integration-test carrier once a container runtime is available.

## R1 preserved behavioral laws

These are black-box requirements, not implementation requirements:

1. A successful adoption leaves one immediately recoverable semantic checkpoint.
2. Repeating the same semantic adoption converges; a conflicting initial claim fails closed.
3. A checkpoint transition is fenced by exact expected revision.
4. Concurrent different transitions from the same expected revision have at most one committed winner.
5. Exact response-loss replay of a committed transition converges to EXISTING instead of committing twice.
6. A terminal task cannot be reopened by a later checkpoint.
7. Resume returns a revision-coherent task state and checkpoint; pinned historical resume does not mix revisions.
8. Writer labels are provenance metadata, not semantic checkpoint content or authenticated identity.
9. Foreign Runtime/Git/domain references inside checkpoint payload are opaque claims, never Host-owned current truth.
10. Database commit failure cannot expose a partial semantic transition.

## Explicit non-requirements from v1 implementation shape

- v1's adoption revision-1 seed followed by normal revision-2 checkpoint is NOT a v2 requirement.
- SQLite BEGIN IMMEDIATE, WAL/SHM, file locks and SQLite migration history are NOT requirements.
- filesystem CAS is NOT admitted in R1.
- Host-specific lease objects are NOT admitted unless PostgreSQL revision locking is falsified.
- ContinuityLens, CurrentAttention, Board, News and cognition/context are NOT admitted in R1.
- long-lived v1/v2 dual-write is prohibited; later cutover uses frozen snapshot -> import -> verify -> single writer.

## R1 graduation gate

The R1 foundation graduates only if a clean Host v2 can demonstrate:

`adopt -> checkpoint -> process/session replacement -> resume`

plus exact replay, conflicting replay rejection, same-revision race fencing, terminality, historical pinned
resume, and transaction rollback using PostgreSQL without importing v1.
