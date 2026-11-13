# Host Owner — Agent navigation

This file is a **scoped navigation pointer**, not a new policy registry, database authority, MCP tool surface, or release gate. Follow the repository-level `AGENTS.md` and the current Host source.

## Start with current facts

- Actual interface inventory: [mcp-surface.json](mcp-surface.json). Discover the installed MCP `tools/list` before use; a source manifest does not prove installed currentness.
- Current Host contract and operator guidance: [README](README.md) and [Human/Agent Owner Guide](docs/HOST_OWNER_GUIDE.md).
- Formal scope: [Social Work Fabric R2 Specification](docs/SOCIAL_WORK_FABRIC_R2_SPEC.md) and [implementation receipts](docs/SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md).
- Owner decomposition: [LEGO R3 plan](planning/lego-plan-r3.json); repository graph verifier currently also consumes [R1 graph carrier](planning/lego-plan-r1.json). The plan is source evidence, not installed truth.

## Locate the actual owner

- **Work semantic state:** `src/ordivon_host_v2/work_store.py` (CAS), `work_queries.py` (reads), `work_relation_commands.py` (internal DAG relation mutation).
- **Message search:** Native GIN array_ops on Unicode codepoint 3-grams for 3+ CJK, with exact strpos post-filter; short CJK still uses strpos and other terms FTS. See migrations/versions/0013_unicode_substring_gin.py and the Owner Guide.
- **Collaboration:** `social_store.py` composes `social_space_*`, `social_topic_*`, `social_message_*` and `coordination_intent_commands.py`.
- **Attention:** `attention_store.py` (subscriptions/acks), `attention_projections.py` and `attention_sql.py` (rebuildable navigation).
- **MCP:** `mcp_server.py`, `mcp_tool_registration.py`, `mcp_*_tools.py`; do not invent additional northbound tools.
- **Schema/release:** `migrations/versions/` via Alembic; `packaging/` handles immutable release and systemd.
- **Agent consumer composite:** the one existing `services/gateway/tests/native_rust_host_consumer_smoke.py` checks Work Engagement → Topic Message → Attention re-entry → independent Topic/Attention ACK → Work review through actual Gateway HTTP to Rust Host and isolated PostgreSQL 18. Run `bash services/host/rust/tools/verify_r2_integrated_pg18.sh`. Its exact Actor/Work allow/deny fixture is **test-only**: production Principal→Actor grants and installed currentness remain separate.
- **Engagement formal abstraction:** `mise run formal:engagement` runs the axiom-free Lean phase/epoch/evidence theorem and fabricated-acceptance counterexample. The native Rust PG CAS, official MCP client and real Gateway consumer tests remain required refinement/effect checks; do not delete them on the strength of an abstract theorem.
- **Validation:** `mise run verify` for source gate, `mise run test:postgres:disposable` for isolated real PostgreSQL 18, and `mise run formal:reply-source` (Python PEP316 obligations) and `mise run formal:work-graph` (bounded Z3 DAG model and negative control); run `mise run formal:dag-theorem` for the axiom-free general Lean DAG theorem using the repo's pinned Lean toolchain for the scoped pure source obligations. For Unicode-gram candidate soundness, run `mise run formal:unicode-search` (axiom-free Lean theorem), then verify PostgreSQL `host_unicode_ngrams3` refinement with `mise run test:postgres:disposable`; neither proof alone proves installed behavior. A skip is not a database PASS.

## Agent re-entry and effects

Use `work.get → attention.reentry → topic.resume → owner-native reference readback → work.snapshot.commit → cursor acknowledgment` as needed. Attention change sequence and per-topic Message sequence differ. Host never grants authentication/authorization, assigns work, schedules Jobs, or proves domain completion; Runtime, Git, Security and domain Owners retain their own truths.

For a change or cleanup, inspect the *exact real consumers*, PostgreSQL dependencies, active Work/Topic/Subscription references, source cut and installed release. Do not delete business rows because they are old or appear redundant. Prefer an existing PostgreSQL/MCP/Alembic/Pydantic capability before implementing a custom one; add no duplicate registry or event bus. Keep code reshaping separate from contract changes, and publish verification outcomes accurately.
