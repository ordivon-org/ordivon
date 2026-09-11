# Ordivon Host v2

Clean-room, external-first reconstruction of Ordivon Host.

Host v1 is a **behavioral oracle only**. Host v2 MUST NOT import `ordivon_host` or copy its implementation.
The first vertical slice is intentionally small:

- PostgreSQL is the only authority store;
- Psycopg owns database access;
- Pydantic owns request/result validation;
- RFC 8785 owns canonical JSON bytes used for digests;
- the official MCP Python SDK v2 owns MCP protocol/transport behavior;
- Alembic owns schema migration;
- pytest/Hypothesis own executable verification.

Initial product surface: `host.status`, `task.list`, `task.adopt`, `task.checkpoint`, `task.resume`.

No Board, News, Attention, CAS, Runtime proxy, scheduler, Agent loop, generic extension system, or copied
WorkingCheckpoint ontology is admitted in R1.
