# Host Rust R5 — 27 native MCP tools: B Social inventory adapters, Doctor and consumer parity

## Exact provenance and single-owner boundary
- Existing Draft PR #2088 A/B/C clean baseline: `85637f2d163382ce09cb97254a86b80f02b918af`.
- C's validated Doctor + indexed `message.get/search` commit `8d3412f3844ae7f5e4078c13e2e99c7a3796a2b8` cherry-picked onto that baseline as `bf2336f6d5ac4192d6c301bfb2f63c3cc6db7f87`.
- This R5 continuation reuses B's already independently accepted native PostgreSQL queries from B commit `27406698e118450f47ea8f98d9f8b122c1e303a0` present in A's 85637 source.
- C changes only official Rust rmcp/PG adapters and protocol/legacy-Python cross-consumer oracles; no edits to B's `services/host/rust/src/social.rs`, `social/relation_queries.rs`, `social/topic_queries.rs`, or A's `work.rs`. The only data authority is existing PostgreSQL 18 schema13. Production Python Host stays online.

## Additional logical LEGO mapped to the capability actually performing it
| Logic/consumer demand | Mature reused ability | Exact public contract |
| --- | --- | --- |
| Causal collaboration relations/opaque targets | B's existing `social::list_message_relations` with one PostgreSQL RepeatableRead read-only transaction, bounded canonical UTF-8 page | `message.relation.list(messageRef, direction?, relation?, afterChangeSequence?, limit?, maxBytes?)` |
| Topic inventory navigation | B's existing `social::list_topics` and native indexed lexical pagination, bounded read-only PostgreSQL snapshot | `topic.list(spaceRef, afterTopicRef?, limit?, maxBytes?)` |
| Diagnostic history integrity vs current pointer | Original Python Host Doctor differential + SQL aggregates + native `tokio-postgres` Portal of batches 128 | `host.status(summary/integrity/history)` |
| Exact durable message dereference and indexed Chinese search | B's native `get_message/search_messages` with current pg_trgm/GIN owner indexes | `message.get`, `message.search` |
| Typed error recovery contract | B's `MissingResource(kind,ref)` data, C's `structuredContent.error` projection | `NOT_FOUND.resourceKind/resourceRef`, `CONFLICT`, `INVALID_ARGUMENT`, etc. |

## Actual consumer acceptance
- Disposable Docker PostgreSQL18 with original Python Alembic0001..0013, Rust native Work/Actor/Attention/Social tests and original Python→Rust/ Rust→Python receipt replay, no production data touched.
- Python creates no fixture for R5 new Topic: Rust MCP creates a brand-new Actor/Space/Topic/participation, posts the Message and then `message.relation.add` creates both self-referential `references` and `about` (opaque target). Rust `message.relation.list` returns both once, tests inbound/outbound/both, cursor split with no omission, typed absence/invalid cursor; Python original `SocialStore.list_message_relations` reads exact JSON parity.
- Rust `topic.list` returns original TopicRef lexical inventory, advances afterTopicRef to the end; original Python `SocialStore.list_topics` reads exact JSON parity and another HTTP session repeats. Typed NOT_FOUND for missing Space, INVALID_ARGUMENT for limit 0.
- Python original `HostV2.status(summary/integrity/history)` is the oracle after a deliberately missing old Work revision and a separate old snapshot digest corruption while the **current** Work snapshot remains intact; Rust stdio and HTTP return exact health, detail and check order; byte-bounded portal avoids retaining historical JSONB collection in RAM.
- Rust official rmcp lists **27** tools and both stdio and loopback streamable HTTP actually call the new capabilities. Original Python MCP registry declares **31**, so names are not complete parity.

## Unresolved release blockers

The four remaining Python public MCP operations absent from Rust:
`host.pool.stats`, `space.list`, `space.participation.list`, `space.subject.list`.

The machine-readable differential in `planning/mcp_source_rust_r5.json` retains input default differences and `outputSchema` **Python31/31 vs Rust0/27**. These are real contract gaps; do not claim complete compatibility. Also verify installed Gateway and connector have the same tool epoch, bench connection/session overhead, and qualify cutover/rollback before any production migration. The observed production Doctor invalidWorks=3 is preserved, not repaired by writing fictional snapshots. Membership no-op swf_change_clock advances a horizon under old schema13; no fake no-gap guarantee.
