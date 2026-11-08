# Gateway Owner — Human / Agent entrypoint

## Authority
Gateway is a thin non-authoritative northbound MCP adapter. It owns public action
names, capability projection, owner routing, wire compatibility and references.
Runtime owns Job/Attempt/physical Artifact, Host owns semantic continuity,
Harness owns Agent run, Security owns admission/PDP decisions.

## Readset
1. README.md / mcp-surface.json — declared surface, not installed evidence.
2. src/ordivon_gateway/mcp_server.py / service.py — MCP and API facade.
3. routing.py / capability_catalog.py / capability_projection.py — discovery.
4. execution_* / execution_refs.py — Runtime delegation and correlation.
5. host_*_tools.py / upstream*.py — Host/Owner forwarding.
6. access_auth.py / capability_authz.py — trusted ingress and protected calls.

## Human
Pin Git revision. Compare released tool surface with live system.describe and
the installed service. Run mise run gateway:formal:verify for TLC and the Python
bounded routing checker; run mise run gateway:verify for native consumers.
Do not interpret a model-check result as deployed authorization proof.

## Agent
Follow repository skill .agents/skills/gateway-formal-routing/SKILL.md.
Keep SPECIFIED, MODEL_VERIFIED, BOUNDED_IMPLEMENTATION_CHECKED,
SOURCE_CONSUMER_TESTED and INSTALLED_VERIFIED as distinct facts;
unexecuted or unqualified stages are UNKNOWN.

## HTTP Security PEP and actual CLI wiring

For human and Agent alike, do not infer Gateway capability protection from
the existence of `AuthZenPrincipalAuthorizer` or an injected test. The actual
`main()` now builds the HTTP server with
`protect_artifact_reads=True`. `artifact.read` without a configured PDP
does not forward; configure both
`ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT` and
`ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE` for authenticated AuthZEN
decisions. Only a Runtime Artifact read belongs to this PEP, not all MCP
effects. The existing private token loader and PDP adapter are reused.
Check `gateway:verify` and `gateway:formal:verify`, then inspect live
deployed middleware/configuration and downstream owner readback separately.

## HTTP execution Principal — separate from STDIO

**Human:** the HTTP CLI now requires verified request state for
`execution.submit/resolve/get/cancel` and `artifact.read`. If the
MCP request `Context` lacks a trusted Principal/issuer, a Tool error
must occur before an Owner RPC. Test the actual entrypoint and the
Principal-scoped requestId/operationRef consumers; do not equate this
identity binding with a PDP permit or Runtime effect realization.

**Agent:** compare the source `main() -> build_server` transport mode
with `_require_http_execution_identity` and natural Owner calls. Run
`gateway:verify` and `test_execution_principal_request_namespace.py`,
including the no-ingress and normal-STDIO cases. Keep HTTP-bound
source behavior, deployed Gateway configuration, live Runtime consumer
readback, and full Host Tool authorization distinct. Unsupported or
unobserved properties remain UNKNOWN.

## Cleanup and release
Search imports, CI, skills, releases, and live consumers before retiring a
module. The unserved SQLite external pull transport has been removed from
Gateway source in the cleanup branch; natural PG Owner state belongs to
Runtime/Host. Keep system directories and live service data intact. Use the
existing Gateway candidate install/verify/activate procedure only after
source build, locked formal checks and native consumer readback.

## B03 strict Owner observation
Runtime configured/available fields must be literal JSON booleans;
contradictory or malformed values are UNKNOWN, with an observation error.
Run the bounded formal/check_owner_status_contract.py in the locked Gateway
environment. Never treat a model result as proof of a live Runtime RPC.

## R04 Owner HTTP pool (MCP SDK native)
McpOwnerCaller uses a process-scoped per-Owner HTTP connection pool and a
request-scoped MCP SDK Client/transport. The pool does not own Owner Jobs or
MCP session identity. OwnerEndpointAuth rechecks exact credential files on
every HTTP request; never cache bearer material as a fixed pool header.
MCPServer lifespan closes the process-owned HTTP pools. Do not enable blind
retries for effectful Tool calls. For native evidence, exercise the real
Gateway->Owner SDK transport including cancellation, credential rotation,
long-lived sessions, and service stop.

## R04a SDK-native protocol mode (opt-in)

The SDK `Client(mode="auto")` remains the default for all Owners.
`ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE=2026-07-28` is a verified
Windows-only opt-in to skip `server/discover`; no bespoke negotiation,
handshake cache or Runtime authority. Test exact Window Runtime version
with the true Gateway service identity before enabling. Fail closed
on an unsupported fixed version; do not retry effectful tools to hide
protocol mismatches. The SDK also supports `legacy` for a confirmed
handshake-era Owner. The SDK may re-list and resend once only after
the protocol-defined HEADER_MISMATCH rejection; verify the Owner rejects
before executing an effect. Gateway itself must not retry an uncertain
effectful Tool call. Keep credentials refreshed per HTTP request.

## R05 Owner observation timeout diagnosis (cancellation phase)
The Gateway upstream adapter emits one warning when the MCP SDK task is
cancelled, with natural Owner ID, tool name, phase and monotonic elapsed
milliseconds. session_close includes possible SDK cleanup latency;
phase_before_cleanup_ms estimates time before cleanup, while total_ms covers
the entire call. Cancellation inside SDK `Client.call_tool` is
`sdk_client_call_cancelled`, which does NOT establish that wire
`tools/call` was interrupted: the SDK can finish the Owner tool, then
send `tools/list` to validate its result's schema. The before-cleanup
coordinate is measured at SDK-call cancellation; only a completed SDK call
reaches `session_close`. Preserve upstream output validation and
protocol-defined HEADER_MISMATCH recovery. SDK cleanup may still delay
propagation of the cancelled observation. Neither phase proves Runtime
availability or identifies the remote cause.
Do not log payloads, auth headers, credentials, or Owner response bodies.
Never interpret a projection timeout as a physical Owner outage. Compare
native Owner RPC, Gateway projection, Windows SCM source cut and Owner logs.

## HTTP MCP ingress security coverage (source cut)

**Human:** HTTP mode uses `GatewayHTTPIngressGuard` before the narrow Runtime
Artifact AuthZEN PEP. Only `system.describe`, `capability.describe`, and
`capability.search` are anonymous *metadata* tools. All other registered
(and newly introduced/unknown) Tools require the verified Principal and issuer
placed in request-local state by the configured ingress verifier; a forged
Tool argument or `_meta` is not an identity. The guard prevents unauthenticated
Owner calls; it is not resource authorization. Without a trusted HTTP credential
provider, protected calls intentionally fail closed.

**Agent:** Compare `enforcement-surface.json` with the *actual* MCP SDK
`tools/list` and `mcp-surface.json`; changes to a Tool require explicit
classification and tests. Run `uv run --offline --project services/gateway
pytest services/gateway/tests/test_http_ingress_coverage.py` from the repo
root. The source consumer verifies the finite HTTP ingress property, not every
downstream Owner PEP. All `downstreamAuthorization` entries are explicitly
`UNKNOWN` pending real Owner enforcement-path evidence. An AuthZEN ALLOW for
one Runtime Artifact does not authorize Host mutations or Runtime execution.
Before promoting a release, check the deployed HTTP entrypoint, real trusted
request state, and Owner-side authorization independently.

## R06 SDK typed Windows status read (bounded performance and correctness)

**Human:** The official MCP SDK v2 short-lived Client call currently follows
MCP tools/call with tools/list for output-schema discovery. On an explicitly
verified 2026-07-28 Windows Owner only, Gateway sends the exact read-only
runtime.describe schemaVersion=1 via the SDK public typed ClientSession.send_request,
removing the extra wire RTT. This does NOT claim complete SDK output-schema
validation: the adapter checks version/node/targets and B03 checks readiness
booleans. Malformed observations remain UNKNOWN. Lower RTT is not proof the
Owner can admit and execute physical work.

**Agent:** Run test_windows_runtime_typed_status_read.py on real TCP including
malformed envelope/status, cancellation and high-level fallback cases.
Effectful Owner calls and non-exact status requests MUST retain the SDK
high-level path (MRTR, schema checks, header mismatch handling). Preserve
credential-file identity per request; do not cache tokens, persist MCP sessions,
retry effects or interpret timeout as an Owner outage. Record exact package,
protocol mode, SourceCut, wire methods and installed consumer before opt-in.
