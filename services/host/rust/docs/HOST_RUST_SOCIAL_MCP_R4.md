# Host Rust R4: native Topic/Message MCP bridge

Status: source-only integration, disposable PostgreSQL 18 qualification; **not installed**, Python Host remains production authority.

## Source and ownership
Parent: C R3 `8ed0795a85bd4251136c8e463de4cd0d904f5466`, under the single existing Host owner at `services/host/rust/`.
C changed only Rust PG/MCP adapters, native protocol smokes, disposable verification harness and source audit. The B-owned `social.rs`, `attention.rs` and A-owned `work.rs` were not modified.

## Delivered native MCP consumers
- `topic.resume`: read-only, integrity-checked repeatable-read page, bounded by high sequence and byte budget; no invented event log.
- `topic.cursor.get`, `topic.cursor.ack`: Topic cursor separate from Attention cursor; ACK does not attest acceptance or actual client consumption.
- `topic.state.set`: same B-owned PostgreSQL row lock/CAS as concurrent `message.post`; state and expected message high water.
- `message.post`: B-owned immutable Message identity, digest, receipt and per-Topic sequence.
- `message.relation.add`: B-owned relation semantics (reply_to precedes source) and transactionally stable receipt.
- Each original MCP tool keeps its exact camelCase fields and applicable RFC 8785 request-identity prefix; `message.relation.add` deliberately hashes the original Python Pydantic snake_case model payload.

## Native verification contract
`tools/python_social_oracle.py` creates an actor-scoped Topic and first Message using original Python Host on disposable PG18; stdio Rust MCP reads it, posts another Message, adds reply_to, reads a second page, ACKs a monotone Topic cursor, closes the Topic using CAS, and rejects later posts/over-horizon ACK/stale CAS. Original Python Host then reads the same durable rows and verifies four exact canonical Command Receipts. A separate Rust HTTP MCP session re-reads both messages after closure.

The original `tools/verify_r2_integrated_pg18.sh` runs the existing Work and Social Rust PG tests, cross-language oracle, actual 18-tool MCP stdio/HTTP smoke and Python vs Rust source-registry differential. The R3 audit report remains immutable; the latest report is `planning/mcp_source_rust_r4.json`.

## Remaining boundaries
Rust MCP 18/31 names, still missing 13 (identity/Space inventories/Message reads+search/diagnostics and other tools). Rust tool `outputSchema` 0/18, explicitly **not** full wire parity. Original `host.status` full Doctor not ported. A/B independent code review, installed Gateway and connector discovery, 2026-era wire negotiation, source-to-install release/rollback, and production consumption are pending. The three historical Work continuity anomalies are not altered.

This migration avoids new infrastructure, a second Host Owner, custom tool router and generic magic MCP tool. It reuses official `rmcp`, `tokio-postgres`, `deadpool-postgres`, PostgreSQL 18 and the original Python Host as a differential oracle.
