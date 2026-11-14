# Ordivon Host MCP capability audit R3

Status: source audit and disposable PG18 verification; NOT installed or consumed in production.

## Observed sources, 2026-11-11

- Python Host epoch-6 manifest: 31 tools. Python SDK's actual tool registry also returns 31.
- The original registry serializes to 45,453 UTF-8 compact JSON bytes, only 2/31 tools have a description, 31/31 have outputSchema.
- The ChatGPT Host connector currently exposes 28 tools; the omitted names are host.pool.stats, message.get, topic.state.set. This observation does not prove they are missing in the installed Host binary. The Gateway source explicitly forwards topic.state.set, but not the first two.
- Rust Host candidate serves 12 tools and defines descriptions for 12/12; it still has no outputSchema and 19 tools remain unported.
- The Gateway upstream reuses an HTTP connection pool while creating a fresh MCP Client session for each Owner call. Its code notes that high-level Client.call_tool can perform tools/list after the call for result schema validation. Measure real bytes, latency and resource costs before redesigning session ownership. Caching sockets alone cannot remove this step.
- Python outer MCP call parameters ignore unknown extras, but nested WorkSnapshotInput is strict. C's Rust MCP adapter now preserves both boundaries and models the three-valued host.status detail enum.
- B independently reproduced a real error mismatch: Python Host emits a structured domain error for an Attention afterSequence beyond the high-water mark; earlier Rust replied with plain text. The Rust adapter now uses rmcp CallToolResult::structured_error plus the legacy recognizable error text. Only expected typed domain rejections map to NOT_FOUND, CONFLICT, INVALID_ARGUMENT and bounded pool timeout. Database/commit ambiguity remains UNKNOWN.

## Logical LEGO -> mature implementation owner

| Need | Mature capability | Natural owner |
| --- | --- | --- |
| Deterministic discovery and stable tool list | rmcp tools/list, schemars | Host |
| Lazy schema loading | MCP client progressive discovery and existing capability search | Gateway / Harness |
| Input contracts | Original Python Pydantic registry, Rust Serde, differential check | Host |
| Output schema & structured success | Python outputSchema and eventual typed Rust replies | Host |
| Domain failure and recovery | Rust structured_error, Gateway error extraction | Host / Gateway |
| Session/protocol efficiency | Official MCP SDK, pooled HTTP, version negotiation | Gateway |
| Idempotent writes | PG transactions + Command Receipt + JCS request identity | Host |
| Paged bounded navigation | PG RR, stable cursors, size bounds | Host |
| Source/install/connector compatibility | Build manifest + installed tools/list + consumer catalog | Host / Gateway |
| Cold restart / migration | PG Schema 13, migration executor, systemd | Host release |

## Distinct capability groups (31)

- Identity: actor.declare (1).
- Work: work.create, work.get, work.list, work.snapshot.commit (4).
- Social: Space 6, Topic 6, Message 5 (17). message.get digest-qualified read and topic.state.set CAS are not equivalent to search/post.
- Attention: Subscription follow/list/unfollow (3), Attention get/delta/reentry/ack (4). These are current-state navigation capabilities, not a full event log.
- Diagnostics: host.status, host.pool.stats (2).

No arbitrary generic host.call: it would erase per-operation schema, recovery and effect semantics. Do not remove a documented tool without proven consumer retirement. Do not add brokers, distributed workflow engines or a second semantic database.

## Executed decisions and verification

1. The new differential tool compares the original Python SDK registry against real Rust MCP stdio tools/list, requires a deterministic unique Rust tool list, verifies Rust inputs have the same property names and required fields, measures schema sizes, and reports missing outputSchema, enums and defaults separately.
2. The machine report is generated to planning/mcp_source_rust_r3.json during the existing disposable-PG18 verifier; it contains metadata only, not credentials or response bodies.
3. The Rust adapter accepts Python-compatible top-level extras while keeping WorkSnapshot nested validation strict.
4. Expected domain errors use an explicit typed failure envelope with retryable and suggestedAction and legacy text. Unexpected PG, integrity or commit-ack problems never assert a business failure.
5. The current Rust verification uses protocol version 2025-06-18. The official MCP 2026-07-28 specification introduces deterministic/cacheable lists and stateless transport; the SDK supports newer versions, but current Host/Gateway behavior must be verified separately.
6. End-to-end PG18 verified in an isolated Docker container via original Host Alembic 0001-0013, domain tests, Python/Rust Work parity, stdio and HTTP tools/list, successful Work and Attention calls, and negative typed error tests. All are source tests, NOT installed/production cutover.

## Open gaps and role allocation

P0: 19 missing Rust MCP tools and typed outputSchema (0/12), full Host Doctor and existing history gaps in 3 Works. Need consumer-driven priority; no fictional feature coverage.

P0: Gateway fresh per-call MCP Client/session and possible post-call tools/list. Gateway owns measurement, timeouts, client lifecycle and safe cache design. Cannot bypass output validation or assume tool completion is effect success.

P1: installed Host vs Gateway vs ChatGPT connector differences (31 source vs 28 connector). Prove actual installed tools/list before diagnosing a fault.

P1: preserve readable read-only vs mutating and retry semantics in tool discovery. Never relabel historical UNKNOWN as completed or failed.

A independently reviews Work/replay, B independently reviews Social/Attention/wire, C owns this PG/MCP seam. A's proposal to move the Rust crate physically inside services/host/rust (one existing semantic Host Owner) remains a separate verified integration question; do not create another permanent Owner.

References:
- https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- https://github.com/modelcontextprotocol/rust-sdk
- https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices
