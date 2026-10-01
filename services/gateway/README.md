# Ordivon Gateway

Thin, non-authoritative northbound MCP adapter over Ordivon natural owners.

Gateway owns only:
- stable public action names;
- capability projection;
- owner routing;
- request/response compatibility;
- correlation/reference normalization.

Gateway never owns Runtime Job/Attempt truth, Host continuity truth, Harness run truth, OAuth/credential authority, Plugin/Skill semantics, or domain completion.

B01 is intentionally small. The public schema avoids fast-moving closed enums such as Runtime execution-context values. Provider-owned context data stays opaque at the Gateway boundary; Gateway only lowers the generic envelope into the owner field and leaves semantic validation to the owner.

For `execution.windows`, Gateway accepts either the legacy provider-defined string context or a provider-defined JSON object. A string is forwarded as Runtime `windowsAuthority`; an object is forwarded unchanged as Runtime `windowsContext`. Capability projection prefers Runtime `windowsContexts` when the owner advertises them, so identity/privilege composition remains Runtime-owned rather than duplicated in Gateway.


## Host northbound boundary

The external Plugin connects to Gateway. Gateway forwards the current
Host-owned Social Work Fabric surface: `actor.*`, `work.*`, `space.*`,
`topic.*`, `message.*`, `subscription.*`, and `attention.*`.
Host remains the semantic owner. Snapshot payloads remain opaque objects;
Host validates its own current contract.

`host.status` forwards the Host owner's bounded status projection. It does
not certify Runtime, Git, Security, provider effects, or domain completion.
Direct-owner recovery and administration remain available independently of
the Gateway carrier.

The exact released northbound vocabulary is bound by `mcp-surface.json`
(package 0.8.0, surface epoch 5, 37 tools). A client-visible catalog is a
separate observation; package version alone does not establish catalog,
carrier, configuration, or authenticated-route equivalence.

## Capability observation

Capability discovery is a non-authoritative, point-in-time projection.
Independent required Runtime and Host read-only probes run concurrently,
with at most one observation of each Runtime owner per request. A selected
capability probes only its required owners. There is no cross-request cache;
the next request observes current owner state again.

`GatewayService(projection_timeout_seconds=5.0)` bounds each cooperative
owner observation. A transport failure or timeout yields `available=false`
with `observation_error`: consumers must preserve UNKNOWN rather than infer
that the owner is proven down. Explicit missing endpoint or authentication
configuration is reported separately as a configuration observation.
Healthy owners remain visible when another observation fails. Cancelling
discovery cancels and awaits its observation tasks. This is a cancellation
budget, not a hard wall-clock deadline: legacy MCP session DELETE cleanup
can extend response latency beyond it. Real SDK mock-transport regressions
cover timeout/cancellation cleanup; live transport cleanup and production
latency still require environment-specific qualification.

Discovery neither authorizes execution nor retries effects. Execution
admission and response-loss reconciliation remain bound to the natural owner
and its explicit request/operation identities.

## External pull workers (candidate R3)

Gateway can optionally enable the provider-neutral external pull-worker transport by setting
ORDIVON_GATEWAY_EXTERNAL_WORKER_DB to a durable SQLite path. When enabled, enrolled workers
contribute their current operator-bounded capabilities to the normal Gateway capability
projection and execution.submit/get/cancel plus artifact.read remain the northbound API.

Worker HTTP routes live under /v1/workers/* and /v1/operations/*. Runtime requests are
Ed25519 signed and replay-fenced. Enrollment is disabled unless
ORDIVON_GATEWAY_WORKER_ENROLLMENT_TOKEN_FILE is configured.

This transport is execution-delivery mechanics only. It does not close Admission Fabric
AF-S2 capability authorization, does not establish domain EffectAuthority, and does not
grant shell workers browser authority.

### Windows local service identity

The Windows candidate can optionally bind `LocalServiceBearerTokenFile` while preserving
`TrustCfAccess`. Keep the candidate stopped, materialize all configured owner credentials
together with `CreateLocalServiceBearer`, and activate using the resulting receipt.
The generated local identity is separate from upstream Runtime credentials, protected
for SYSTEM, Administrators and the Gateway service SID, and accepted only on loopback.
Never print token contents or credential receipt digests. Existing profiles without the
optional field retain their activation contract. This local acceptance lane does not
qualify the public Cloudflare principal, Linux/Skills bindings or public promotion.
