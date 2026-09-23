# Ordivon Gateway

Thin, non-authoritative northbound MCP adapter over Ordivon natural owners.

Gateway owns only:
- stable public action names;
- capability projection;
- owner routing;
- request/response compatibility;
- correlation/reference normalization.

Gateway never owns Runtime Job/Attempt truth, Host continuity truth, Harness run truth, OAuth/credential authority, Plugin/Skill semantics, or domain completion.

B01 is intentionally small. The public schema avoids fast-moving closed enums such as Runtime execution-context values; capability-specific validation/lowering happens server-side.


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
