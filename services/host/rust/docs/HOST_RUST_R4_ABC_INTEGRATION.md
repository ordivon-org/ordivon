# Host Rust R4 — A/B/C MCP consumer integration

## Identity and release boundary

- Baseline A/B integrated SourceCut: `f6b5e142cd6b50e8a7b3f9299c275d6448058f15`.
- Cherry-pick of C's six Social MCP tools: `dc0ea3c67a63ae220e564a4b4eeeba0e0e8ed42b` (source: `d78da90116d7f311a7196d9d61f1a30f0dc5469c`).
- This candidate adds the MCP bridge for A's existing `work::declare_actor`, and activates A/B independent Python/Rust Oracles in the same disposable integration gate.
- All code is under one Host semantic Owner: `services/host/rust/`. Existing Python Host remains the only production installed writer. No production DSN, service, Gateway, connector, policy, or systemd changes.

## Consumer capability coverage

Rust's official `rmcp` advertises 19/31 original Host MCP operations. C exposed six existing B Social domain commands (`topic.resume`, `topic.cursor.get/ack`, `topic.state.set`, `message.post`, `message.relation.add`) and A's `actor.declare`. No new SQL state machine, event bus, parser, or independent Tool Registry was created. PostgreSQL remains authoritative for all effects.

Logical LEGO and mature capability composition:

| Consumer requirement | Real ability performing it |
| --- | --- |
| Actor label registration with replay | A Work PG transaction, actor_refs unique constraint, Command Receipt, JCS request ID |
| Ordered resumable discussion with integrity | B Social RR Postgres query, immutable Message digest, bounded pagination |
| Per-Topic consumed navigation | B Social PG cursor (distinct from Attention global change cursor), monotone ACK |
| CAS close vs concurrent message.post | B Social locking same Topic row and high-message sequence |
| Message and causal relation | B Social native transaction, PostgreSQL FK/CAS, persisted receipt |
| Stable discovery/errors | C official rmcp tools/list, Schemars, structuredContent.error and legacy error text |
| Cold startup/transport | C bounded deadpool-postgres, supported official stdio/loopback HTTP |
| Differential proof and no production writes | Original Python MCP registry + separate Docker PostgreSQL18 + Alembic0001..0013 |

The actorRef and participation records do not grant identity authentication, authorization, management power, execution, or physical-effect truth.

## Continuity proof, not just named tool count

- C `tools/python_social_oracle.py` seeds a Topic and Message via the original Python SocialStore; Rust MCP resumes, posts, relates, acknowledges, CAS-closes, proves rejected stale requests; original Python re-reads two messages, relation, exact cursor and all four JCS/PG receipts; HTTP MCP session separately observes the same durable Topic.
- C `tools/mcp_stdio_smoke.py` declares Actor via Rust MCP and replays same request; Python original WorkStore reuses the exact native receipt and `createdAt`; changed ActorKind returns `CONFLICT`.
- A `tests/actor_python_parity.py` runs after native Work PG tests.
- B `tests/social_native_python_replay.py` runs after native Social PG tests.
- B `tests/attention_mcp_cross_language.py` runs against the Rust binary after building, before the main consumer smoke.
- Python Host `485/485`, Rust Work `9/9`, Social `8/8`, status `1/1`, work Python/Rust `1/1`, Golden `3/3`, Rust lib `21/21`, native MCP stdio/HTTP 19-tool smoke, cargo fmt/clippy, Ruff, owner boundaries all form the native Host merge queue evidence.
- Cross-language `B_ATTENTION_ERROR_ENVELOPE_GAP` is an outdated text-only parser diagnostic in B's oracle: the current C tests independently verify `structuredContent.error.code=CONFLICT`, `retryable=false` and the legacy text. B has been asked to independently correct the oracle before considering this discrepancy closed.

## Remaining work — not accepted as complete

- 12/31 original Host tools still have no Rust MCP exposure. `outputSchema` remains 0/19; dynamic input metadata differs in some defaults. The generated `planning/mcp_source_rust_r4.json` records exact differences, not a false green parity score.
- End-to-end cold boot, client relist/resubscribe after gap, full Host Doctor `history/integrity`, retained history gaps in 3 production Works, installed/source/connector tool currentness, deployment/rollback, real Gateway consumer and 2026 protocol negotiation remain pending.
- B's observed desired-state no-op can advance the global change clock without mutating a row: independently assess its consumer cost before changing PG logic.
- Gateway has a persistent HTTP pool but still creates MCP sessions per Owner call; quantify SDK post-call `tools/list`, p95 latency and cancellations before optimizing.
- Old Python production Host stays online and retains PostgreSQL authority; this is a staging Rust migration candidate, not a cutover.

This document is an engineering qualification boundary, not an authorization to switch installed services or delete original schemas.
