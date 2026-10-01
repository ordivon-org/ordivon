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

For `execution.windows`, Gateway 0.4 accepts either the legacy provider-defined string context or a provider-defined JSON object. A string is forwarded as Runtime `windowsAuthority`; an object is forwarded unchanged as Runtime `windowsContext`. Capability projection prefers Runtime `windowsContexts` when the owner advertises them, so identity/privilege composition remains Runtime-owned rather than duplicated in Gateway.


## Host northbound boundary

The default external Plugin connects only to Gateway. Gateway exposes normal Host continuity and collaboration actions through stable northbound names while Host remains the semantic owner.

- continuity get/list/observe and adopt/checkpoint/attention (compatibility)
- continuity find/changes (preferred discovery/change vocabulary; mechanical recency only)
- collaboration list/search/post (compatibility)
- collaboration publish (preferred write vocabulary; explicit global or continuity scope)

Gateway intentionally does not expose host.status; owner administration and Doctor remain direct-owner recovery/admin concerns.

Checkpoint payloads are opaque objects at the Gateway boundary. Host validates the current WorkingCheckpoint schema; Gateway does not maintain a second Host checkpoint ontology.

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

## Capability observation lifecycle

Independent read-only Runtime and Host capability observations run concurrently, once per required owner per request. Projection ordering stays deterministic, and observations are not cached across requests. A failed or timed-out owner observation remains UNKNOWN through the existing observation error; healthy owners remain visible.

The default per-probe cooperative cancellation budget is five seconds. Cancellation waits for transport cleanup: legacy MCP session DELETE cleanup may extend that budget, so it is not a hard end-to-end latency deadline. Cancellation of the enclosing request drains its child probes. Gateway does not parallelize effects or retry upstream effects.

### Windows local service identity

The Windows candidate can optionally bind `LocalServiceBearerTokenFile` while preserving
`TrustCfAccess`. Keep the candidate stopped, materialize all configured owner credentials
together with `CreateLocalServiceBearer`, and activate using the resulting receipt.
The generated local identity is separate from upstream Runtime credentials, protected
for SYSTEM, Administrators and the Gateway service SID, and accepted only on loopback.
Never print token contents or credential receipt digests. Existing profiles without the
optional field retain their activation contract. This local acceptance lane does not
qualify the public Cloudflare principal, Linux/Skills bindings or public promotion.

Native Windows identity tests require an installed, stopped
`OrdivonGatewayCandidateR5` service so its service SID can be resolved. Linux runs
skip these Windows-only checks; those skips are not native Windows qualification.

Windows release dependencies use uv `--link-mode copy`: each release owns its file ACLs independently of the shared package cache. Existing releases are not rewritten by reinstall; repair a qualified stopped release separately and retain its recovery backup.
