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

## R05 Owner observation timeout diagnosis (cancellation phase)
The Gateway upstream adapter emits one warning when the MCP SDK task is
cancelled, with natural Owner ID, tool name, phase and monotonic elapsed
milliseconds. session_close includes possible SDK cleanup latency;
phase_before_cleanup_ms estimates time before cleanup, while total_ms covers
the entire call. Neither is proof of Runtime availability.
Do not log payloads, auth headers, credentials, or Owner response bodies.
Never interpret a projection timeout as a physical Owner outage. Compare
native Owner RPC, Gateway projection, Windows SCM source cut and Owner logs.
