# R9 — Gateway to native Rust Host real-consumer qualification

**Authority**: one existing Host domain owner. Original Python Host stays installed
until separately qualified release/cutover. This is an isolated test of the
**current Gateway** Python SDK as a consumer of the new Host Rust HTTP endpoint.

## Representations and proof boundary

- Agent: genuine mcp.Client calls actual Gateway build_server().
- Gateway: existing GatewayService plus **production McpOwnerCaller**,
  not a test stub or hand-written HTTP proxy.
- Owner: actual Rust rmcp Streamable HTTP, bound only to 127.0.0.1.
- State: fresh disposable PostgreSQL 18 from Python Host's original Alembic
  0001→0013 and previously established Work/Social/Attention/Engagement test
  fixtures. Never pass a production DSN or installed Host URL.

The test compares direct owner JSON with Gateway agent-visible
structuredContent, field-for-field for Work.get, Space.list, Topic.resume.
For host.status it excludes **only observedAtMs** from the comparison:
two separate reads cannot legitimately claim the same observation timestamp.
Every other status, Doctor and PG-authority field must agree. It also
requires a typed NOT_FOUND (resourceKind/ref) to pass through the actual
Gateway error envelope. All observations take place over real MCP sessions.

This is different from merely comparing source tools/list manifests.
The separate tools/repo/check_host_gateway_refinement.py already checks the
29 input contracts; this test proves actual owner effects become unchanged
consumer observations for selected incumbent calls.

## Limitations / release blockers

The installed production Gateway and ChatGPT connector are **not** switched.
The Gateway does **not** expose the new work.engagement.advance/list tools;
this is intentional and checked, not counted as a successful installed consumer.
ActorRef is a stable domain reference, **not** authenticated identity.
Delivery evidence references are not live Artifact/Runtime attestation.
Current Work inbox is not a full event log. Neither source-only host.pool.stats
nor optional historical engagement feed is faked to inflate tool counts.

For a live cutover, independently prove configured Gateway endpoint, identity
binding, same-authority write admission, rollback, installed SDK catalog and
actual connected-client use. Passing this test does not claim any of those.

## Verification

From services/host/rust/tools/verify_r2_integrated_pg18.sh, after the
ordinary Rust stdio/HTTP and original Python oracle tests, the wrapper invokes
gateway_rust_owner_consumer_smoke.py with the Gateway's own locked uv
environment. The script rejects inherited Host URL and non-loopback/non-shared
test DSNs and terminates its temporary Rust HTTP child. The parent's Docker
trap deletes the disposable PostgreSQL18 server even on failure.

GATEWAY_REAL_RUST_OWNER_CONSUMER_PASS represents four verified
success payloads plus one typed missing-resource rejection — not 29-tool
installed live parity.
