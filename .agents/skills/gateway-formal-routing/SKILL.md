---
name: gateway-formal-routing
description: Verify and refactor Ordivon Gateway as a thin Owner-routing MCP adapter through route identity, TLA+ safety properties, Python conformance, and native consumer evidence.
compatibility: Needs Ordivon checkout and Gateway Python dependencies. TLC needs Java 11+ and a digest-verified pinned JAR.
license: MIT
---

# Gateway Routing Formal Verification — R2.1 thought/ability LEGO

Use for Gateway routing changes, capability discovery, execution forwarding,
SourceCut/Owner boundary, formal-verification migration and obsolete-worker cleanup.

## Contract
I: operator route map, requested capability and verified ingress.
O: exact routed Owner operation or rejection.
S: lookup, validate, route and reject.
pre: each map key equals the CapabilityRoute.capability of its value.
post: forwarded capability identity equals the declared route identity;
the selected Owner equals the exact route Owner.
inv: ForwardedImpliesExactRoute and RejectedNeverForwards.
eff: owner RPC is outside the routing model; Job/Host authority never moves.
c: finite explored state count; real runtime resource cost UNKNOWN.
epsilon: full model-to-Python refinement UNKNOWN; installed behavior UNKNOWN
without exact installed consumer evidence.
prov: pinned Git commit, TLC output, bounded Python check, native readback.
unfold: specification -> TLA+ model -> model check/negative controls ->
source conformance -> real consumer -> installed candidate proof.

## Agent procedure
1. Bind exact Git SourceCut; inspect services/gateway/AGENTS.md, README.md,
   mcp-surface.json and the routing/consumer source graph.
2. Run mise run gateway:formal:verify using an exact digest-checked TLA+ JAR.
   Positive model passes; reachability intentionally violates NeverForward;
   unsafe routing intentionally violates ForwardedImpliesExactRoute.
3. Run Python finite implementation checker at
   services/gateway/formal/check_routing_conformance.py. This is bounded
   exploration, never a universal theorem.
4. Run mise run gateway:verify and Gateway -> Runtime/Host native
   readback for operations with physical effects. Compare package/tool
   surface to the actually installed candidate.
5. Record SPECIFIED, MODEL_VERIFIED, BOUNDED_IMPLEMENTATION_CHECKED,
   SOURCE_CONSUMER_TESTED and INSTALLED_VERIFIED separately. UNKNOWN is
   never FALSE and never PROVEN.
6. Retire sample tests only when the exact property has sufficiently strong
   refinement evidence. Preserve native network, auth, deployment and Owner
   effect verification where abstract models are insufficient.

## Human
Review the claim/evidence ledger before using a candidate release. Reuse
TLA+, CrossHair (pure Python only), static typing and existing release scripts.
Do not invent a second policy decision or rollout framework.

## B03 Owner observation: strict truth contract

Pure Owner observation contract: Runtime status fields configured and available
must be literal booleans. available=True requires configured=True. A truthy
string, integer, missing field, or contradictory pair is not positive evidence
and must carry an observation error. Gateway retains its non-authoritative
boundary; malformed observations are UNKNOWN, not proof Runtime is down.

Agents: run uv run python formal/check_owner_status_contract.py through the
existing Gateway verification target. The checker enumerates 100 adversarial
status pairs through execution and Artifact projections. Compare with live
runtime.describe and Gateway capability.describe; synthetic enumeration is
not a physical RPC success.

Humans: inspect capability_projection.py and capability_catalog.py for the
implementation; read observation errors before classifying Runtime unavailable.
Retain real MCP consumer readback and native Windows identity and PG integration
checks where appropriate.

## R04 Transport composition LEGO (capability + reasoning)
Gateway upstream transport owns only HTTP sockets and is explicitly scoped to
McpOwnerCaller. Prefer upstream MCP SDK Client protocol negotiation and
httpx2 connection pooling; do not replace SDK with a custom JSON-RPC client.
Auth material is read on each request through OwnerEndpointAuth, including
when a connection is reused. MCPServer lifespan must close pooled clients.
Validate exact Owner semantics through independent real loopback RPCs, not
only mocked connector calls; do not infer production latency from loopback.
Preserve long-running Runtime Jobs on HTTP cancellation; never blindly replay
an execution submission after uncertain delivery.
