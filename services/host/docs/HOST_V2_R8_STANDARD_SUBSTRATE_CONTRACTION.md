# Host v2 R8 — Standard-substrate contraction

## Result

Host is now treated as a thin semantic-continuity bounded context. The retained custom surface is limited to Host-local Task identity/revision, revisioned checkpoint claims, replay-safe Host mutations, durable collaboration records, and re-entry projections.

## External owners

- PostgreSQL owns transactions, MVCC, referential integrity, indexes, and full-text search.
- Alembic owns schema history. The legacy route-anchor data cleanup is a separate explicit SQL data migration.
- Pydantic owns validation and generated request schemas.
- RFC 8785 canonical JSON plus SHA-256 owns deterministic mechanical digest identity.
- The official MCP Python SDK owns MCP protocol and transport behavior.
- uv owns Python acquisition and environment synchronization. `.python-version` is the project Python request and `uv.lock` is the dependency lock.
- systemd owns process lifecycle and OS sandboxing; the service retains `DynamicUser` and `ProtectHome`.
- pytest/Hypothesis/Ruff/GitHub Actions own executable quality gates.

## Subtractions in R8

- removed runtime recognition of synthetic Board route anchors after `board_messages.task_id` became authoritative;
- removed duplicate hydrated `HostV2.list_tasks/list_tasks_page` paths; compact inventory is the only product list path;
- removed the release script's `/usr/bin/python3.14` assumption; uv-managed Python is installed under the operator prefix rather than a protected user home;
- kept MCP Tasks distinct from Host semantic Tasks: the protocol extension is an async-request execution mechanism, not a semantic-continuity store.

## Production evidence

On the 2026-09-20 production clone, schema 4 -> 5 materialized Task foreign keys for all legacy routes. There were 452 synthetic anchor rows and 4,042 direct children, with zero unrouted anchors and zero child/anchor Task mismatches. After cleanup, all 2,110 Tasks remained and the full test suite passed.

Production then cut over to source `fdc438be0a9afc39c158f5776c82454cc6ce909e`, schema 5, surfaceVersion 9, ten MCP tools. The same 452-anchor cleanup was executed transactionally on production and full Host history Doctor remained healthy.

## Boundary

`writerLabel` remains self-asserted provenance only. Authentication/authorization must be supplied by the MCP/OAuth ingress boundary rather than promoted into a Host-specific identity ontology.
