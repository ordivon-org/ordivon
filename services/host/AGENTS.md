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
- **Validation:** `mise run verify` for source gate, `mise run test:postgres:disposable` for isolated real PostgreSQL 18, and `mise run formal:reply-source` (Python PEP316 obligations) and `mise run formal:work-graph` (bounded Z3 DAG model and negative control); run `mise run formal:dag-theorem` for the axiom-free general Lean DAG theorem using the repo's pinned Lean toolchain for the scoped pure source obligations. For Unicode-gram candidate soundness, run `mise run formal:unicode-search` (axiom-free Lean theorem), then verify PostgreSQL `host_unicode_ngrams3` refinement with `mise run test:postgres:disposable`; neither proof alone proves installed behavior. A skip is not a database PASS.

## Agent re-entry and effects

Use `work.get → attention.reentry → topic.resume → owner-native reference readback → work.snapshot.commit → cursor acknowledgment` as needed. Attention change sequence and per-topic Message sequence differ. Host never grants authentication/authorization, assigns work, schedules Jobs, or proves domain completion; Runtime, Git, Security and domain Owners retain their own truths.

For a change or cleanup, inspect the *exact real consumers*, PostgreSQL dependencies, active Work/Topic/Subscription references, source cut and installed release. Do not delete business rows because they are old or appear redundant. Prefer an existing PostgreSQL/MCP/Alembic/Pydantic capability before implementing a custom one; add no duplicate registry or event bus. Keep code reshaping separate from contract changes, and publish verification outcomes accurately.

## HTTP Host workload identity (source boundary)

**Human:** Host's native Streamable HTTP endpoint now uses the official
MCP/Starlette bearer middleware. Configure
\`ORDIVON_HOST_V2_BEARER_TOKEN_FILE\` as a private absolute credential file;
configure Gateway's \`ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE\` with the
same credential bytes before activating the candidate. A systemd
\`LoadCredentialEncrypted\` source is preferred over copying a secret into a
repo or environment. The HTTP listener fails before bind when the Host
credential is absent or invalid. Never treat a loopback IP as authentication.
Run the real SDK consumer \`tests/test_http_identity.py\`, followed by
\`mise run host:verify\` and Gateway's native consumer tests. STDIO is a
different operator-local trust boundary and remains unchanged.

**Agent:** Authentication proves only the Gateway workload token; it
does not establish a human/agent Principal, a Host Actor delegation, or
resource-level policy authorization. Host remains the natural Owner of
Work/Space/Topic/Message state. Inspect Gateway upstream service credential
configuration, the actual installed Host HTTP app, and live rejected/accepted
request outcomes before promoting \`HTTP_AUTHENTICATED\`. Until a real
Security decision is bound to Host object/actor/effect, leave
\`HOST_OBJECT_AUTHORIZATION=UNKNOWN\`. Do not advertise a fictitious OAuth
issuer for the operator-local service token; for real federated OAuth use
the upstream SDK's \`AuthSettings\` and IdP-backed verifier.

## Host workload-credential FD continuity

**Human:** the Host HTTP bearer credential is acquired from the service-private
operator/systemd credential directory. Token verification re-reads the exact
opened file descriptor per request with POSIX no-follow and nonblocking flags;
regular-file mode, size and same-inode metadata continuity must hold before
the native MCP/Starlette bearer middleware authenticates the Gateway workload.
An unexpected FIFO or in-place mutation fails closed. This is M2M transport
authentication only, never Human/Agent identity or object-level Actor/Grant
authorization. The trusted credential directory is configured by the OS.

**Agent:** exercise test_http_identity.py with the actual TokenVerifier and
native Host HTTP app, then run host:verify. Rejection of substituted FIFO,
mutable credential bytes and wrong service bearer must not be downgraded by
an outer Gateway ALLOW. Distinguish Linux verified source behavior, unrun
Windows source behavior (Host HTTP remains POSIX only), installed service
credentials and authoritative Actor resource policy. Do not leak credential
values into evidence.
