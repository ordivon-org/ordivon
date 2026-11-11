# Host Rust R5 — consumer parity: Doctor and Message read/search

## Source boundary
- Upstream A/B clean joint baseline `301b3fef60d08bdeefc6e732c28da0a6fff3356c`.
- Cherry-picked C's completed R5 first collaboration loop `3d02a87efcde8c8036478eb0f673ab1c3c2b5d1f` as `a782354bb7e54f2bc1e9c4bb48660e5eab535cba`.
- All new implementation is in C adapter `services/host/rust/src/mcp.rs`, `pg.rs`, and C-owned test/oracle/verifier; B's existing `social/message_queries.rs` (get/search), A's `work.rs`, and the production PostgreSQL schema remain untouched.

## What the consumer actually needs

| Logical LEGO | Mature capability used | Observable contract |
| --- | --- | --- |
| Work/Host current pointer health | One PostgreSQL read-only Repeatable Read transaction | `host.status(integrity)` contains the seven legacy Host checks with exact labels/ordering/details |
| Historical record continuity | PostgreSQL `GROUP BY` with revision count/min/max | `work.snapshot_history_contiguous` can be false even when `work.current_snapshot` is true |
| Historical digest verification | PostgreSQL server Portal, `query_portal(128)`, RFC8785 canonical SHA256 | `host.status(history)` adds digest scan; no unbounded `fetchall()` retained payload list, no fabricated old revision |
| Structured error identity | Existing B-typed `MissingResource(kind,ref)` | `NOT_FOUND` includes `resourceKind/resourceRef`; no parsing human-readable `Display` |
| Exact message dereference | B Social immutable get in RR PG snapshot | `message.get(messageRef,expectedDigest?)`, digest verification and typed CONFLICT/NOT_FOUND |
| CJK/message recall | B Social indexed CJK literal/Unicode ngrams plus native PostgreSQL full-text | `message.search(query,spaceRef?,topicRef?,beforeSequence?,limit?,maxBytes?)` with no invented relevance score, stable descending cursor, byte-budget bounds |

## Independent falsification, not paper parity

On a fresh disposable Docker PostgreSQL 18 and *original* Python Alembic migrations 0001–0013, `python_status_doctor_oracle.py` uses original Python WorkStore to seed two revision-2 Works and then **deletes revision 1** from one and **corrupts the noncurrent revision-1 digest** in the other. Both current snapshot pointers stay valid. Original Python `HostV2.status(summary/integrity/history)` is the full JSON differential oracle (except observedAtMs), and Rust official stdio MCP returns exact equivalent results. The alternate HTTP MCP session repeats the negative state check. Expected: CURRENT=ok, CONTIGUOUS=error invalidWorks=1, HISTORY_DIGEST=error invalid=1. The clean disposable Rust `status_pg` test additionally verifies seven checks healthy under integrity and eight under history.

A separate exact cross-language consumer traverses `actor.declare`→`space.create`→`topic.create`→`space.participation.set`→`message.post`→`message.get`/CJK `message.search`→`topic.resume`, and compares the **actual Rust stdio tool structured JSON** with original Python `SocialStore.get_message/search_messages` on identical durable PG rows. Negative cases: wrong expectedDigest CONFLICT, missing message NOT_FOUND typed message ref, blank query INVALID_ARGUMENT, absent Topic NOT_FOUND typed topic ref, `beforeSequence` bounded empty page. Independent HTTP session repeats CJK search.

All prior A/B native Work+Social+Attention tests, their original Python receipt/consumer parity, and the C original Python native-collaboration oracle still run within the same fresh temporary database and exit-trap cleanup.

## Known incomplete migration status

- Native MCP `tools/list` now 25 of 31 original Python Host operations, with six queries/diagnostics remaining. Naming parity is **not** output-schema parity: Python has outputSchema for 31 tools, Rust has **0 of 25**. The generated `planning/mcp_source_rust_r5.json` exposes the actual default/shape differences rather than hiding them.
- Original production Python Host is still the installed service, and its three historical Work gaps remain; this code neither migrates missing snapshots nor reads/writes live production PG.
- Full installed Gateway/connector currentness, release/rollback, source↔binary operational equivalence, request/receipt latency, and the remaining Social inventory/relations need consumer evidence before any cutover.
- A controls the existing Draft PR #2088 and GitHub required checks; C hands off one fast-forwardable Git commit, not a second PR.
