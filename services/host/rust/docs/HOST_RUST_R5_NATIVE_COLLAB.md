# Host Rust R5 — Native collaboration bootstrap without Python seeding

## Source cut and delivery scope
- Parent/authoritative prior Host Rust source: `baf2a6e8277dc619e10ff665edbb8209f0b23ab5`.
- The deployed Python Host remains the production writer, and PostgreSQL schema13 is unchanged.
- C changes only `services/host/rust/src/{mcp,pg}.rs`, native MCP smokes, one Python differential oracle, the isolated PG18 verifier, and its generated R5 contract ledger. No B `social.rs`, A `work.rs`, PG migrations, or Gateway implementation is forked.

## Why these four tools, rather than another framework
A consumer could previously **resume and post to an existing** Rust-accessible Topic but could not establish a new discussion realm from a clean ActorRef over the same MCP entry. The authoritative Python Host offered these commands; B had already implemented their exact transactional behavior in Rust, while C's public rmcp adapter had not exposed them. A new tool router/SQL state machine would duplicate an existing natural Owner. Use `rmcp` + Schemars for schema, `deadpool-postgres` for bounded connections, and B's original Social domain functions for mutations and projections.

| Logical LEGO | Real capability and enforceable invariant | Rust MCP command |
| --- | --- | --- |
| Social Space first creation | PostgreSQL unique SpaceRef and receipt, serialized subjects, conflict on changed initial semantics, JSON canonical identity = Python `SpaceInput.model_dump(mode=json)` | `space.create` |
| Bounded Space current-state read | One Repeatable Read PG snapshot, bounded participant/topic lists and byte envelope, never infer IAM | `space.get` |
| Asynchronous Topic creation | PostgreSQL TopicRef first-writer and receipt; parent Space and actor existence; same exact snake_case Python `TopicInput` identity | `topic.create` |
| Participation desired state | One B-owned upsert, transitions joined→left→joined, **no immutable receipt** for a natural-key desired-state command; joining is not authorization | `space.participation.set` |

The actual consumer trajectory is:

`actor.declare` → `space.create` → `space.get` → `topic.create` → `space.participation.set` → `message.post` → `topic.resume` → original Python SocialStore readback and exact Command Receipt verification.

### Executed invariants and negative cases

- Rust stdio MCP creates a fresh Actor/Space with unsorted subjectRefs; durable Space subject projection comes back sorted, while Python command receipt retains the original list order in its RFC8785 identity.
- Rust Topic, membership joined→left→joined, message post, resumed one-page conversation and `space.get` count/preview all operate against one isolated PostgreSQL18 created by original Alembic 0001..0013, not mock storage.
- `space.create` repeated same request returns existing with stable createdAt; `topic.create` same; changed purpose and changed Topic title must CONFLICT; invalid trimmed Space and duplicate subject refs INVALID_ARGUMENT; unknown actor NOT_FOUND.
- New `tools/python_native_collaboration_oracle.py` uses the original Python WorkStore+SocialStore against that *same* temporary database: exact read-after-Rust, replay of Actor/Space/Topic/Message, JCS digests and corresponding four immutable receipts. Original message.post stores a **reference marker**, not a full `admission` payload, and the oracle verifies this distinction rather than inventing another receipt scheme. Current membership has no immutable receipt.
- A second HTTP MCP session subsequently re-reads the R5 Space after the Rust stdio session, proving durable transport-independent state.
- Prior cross-language Work9, Social8, Attention tests and original Python consumer oracles are kept in the same single disposable verifier.

## Explicit unfinished contract, not synthetic success

Source Python MCP surface has 31 tools; R5 Rust has 23. The generated `planning/mcp_source_rust_r5.json` records the remaining eight, all schema-differential status, and response `outputSchema` remaining unexposed (0/23). A list_all success does not make the Rust implementation a production replacement. B's previous desired-state `swf_change_clock` no-op advance is observable and should be assessed by its Attention consumers independently; no SQL tuning is performed here.

Other pending work: bounded Space/topic/message inventories, full Host Doctor/history with three historic invalid Works, Gateway and connector installed surface and retry/timeout costs, live cutover/rollback verification. These are future consumer-backed capabilities, not reasons to block or declare this R5 isolated integration failed.
