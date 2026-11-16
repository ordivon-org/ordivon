# Gateway Owner — Human / Agent entrypoint

## Authority
Gateway is a thin non-authoritative northbound MCP adapter. It owns public action
names, capability projection, owner routing, wire compatibility and references.
Runtime owns Job/Attempt/physical Artifact, Host owns semantic continuity,
Harness owns Agent run, Security owns admission/PDP decisions.

## Native Runtime Job/Attempt truth
Runtime's `status` is a compatibility **Job summary**, not an alias for
`attemptState`: the native producer projects `accepted|starting` to `queued`
and `running|stopping|recovering` to `working`. Gateway validates both wire
fields when present but preserves the original Job summary as public `state`.
Never require equality between fields with different semantics; source-backed
producer cases must be included in execution submit/get/cancel consumer tests.
`executionTerminal` and `executionDisposition` remain separate explicit Owner
claims; status text alone never establishes physical or domain completion.
Gateway B03 capability readiness TLA+ does not verify Job state semantics.

## Official MCP SDK Owner transport
The Linux PG six-tool exception for `workspace.exec`, `job.list`,
`job.observe`, `job.get`, `job.cancel`, and `artifact.read` is retired in
source: the current installed Runtime supports the full official
`Client.call_tool` driver, verified by real Job/Artifact/Cancel consumer runs.
Do not restore the old `ClientSession.send_request` bypass merely because a
historical Owner version once published incomplete output schemas. Keep the
independent Windows `runtime.describe` typed read-only optimization. A source
passing high-level SDK tests does not qualify Gateway production rollout or
prove the Runtime UTF-8 subcharacter-page issue fixed at its natural Owner.

## Readset
1. README.md / mcp-surface.json — declared surface, not installed evidence.
2. src/ordivon_gateway/mcp_server.py / service.py — MCP and API facade.
3. routing.py / capability_catalog.py / capability_projection.py — discovery.
4. execution_* / execution_refs.py — Runtime delegation and correlation.
5. host_*_tools.py / upstream*.py — Host/Owner forwarding.
6. access_auth.py / ingress_identity.py — verified ingress identity and shared request coordinates.
7. authorization_targets.py / capability_authz.py — pure Owner request-target projection and Security PEP decision binding.

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
decisions. The existing Security PEP also covers Host read/write operations
and qualified Runtime release.apply; generic Runtime execution retains the
independent verified-ingress/Runtime authority boundary. A valid machine
bearer or Tool ActorRef is not a Security grant. The existing private token
loader and PDP adapter are reused.
The request target projection lives in `authorization_targets.py`; it derives
the original Host Tool read/write partition and Runtime/Artifact exact resources
without interpreting AuthZEN ALLOW. The PEP in `capability_authz.py` accepts
only integer Security schema v2/v3, rejects floating versions, and requires a
nonblank exactly echoed request ID for v3 interactive evidence. Source negative
tests intentionally proved the previous ALLOW gap; the B02 TLA model now
independently represents nonblank nonce qualification. This is NOT a proof
that installed Security grants exist.
Check `gateway:verify` and `gateway:formal:verify`, then inspect live
deployed middleware/configuration and downstream owner readback separately.

## Shared HTTP request identity (source contract)

`ingress_identity.py` is the only Gateway source reader of the request-local
`scope.state` Principal/Issuer pair. The Access middleware authenticates and
populates this state; the pure reader **does not** authenticate arbitrary dicts.
The HTTP guard, AuthZEN object PEP, audit correlation, and the MCP Tool execution
Context all use the same non-blank pair or independently fail closed.
`_HOST_READ_ONLY_TOOLS` derives from the canonical Host read-selector map,
not a second hand-maintained Tool list. Native source tests verify this read/
write partition against the existing `enforcement-surface.json` and Host
Dispatcher. This changes no Security grants, owner credential, or installed
authorization. Run `test_ingress_identity_contract.py` with the existing
HTTP/Host/AuthZEN tests before any installed consumer inference.

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
The B03 TLA+ model and original bounded Python consumer now additionally
require a list-valued target inventory, exactly one matching target identity
and list-valued explicitly provided context inventories before READY.
The checker covers 100 status pairs plus nine real Python inventory/Context
cases. Run both gateway:formal:verify and gateway:verify; neither establishes
live Runtime readiness or a universal Python-to-TLA+ refinement proof.

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


## R07 Gateway native Linux release interpreter preflight

**Human:** For production releases, prefer an already qualified Python
3.15.1 interpreter in the Gateway /opt deployment prefix. systemd
DynamicUser= and ProtectHome= mean a Python executable beneath /root is
not usable by the real service even if root can import the release.
Pass ORDIVON_GATEWAY_RELEASE_SERVICE_USER=ordivon-gateway to the existing
installer so it checks the installed interpreter and OpenTelemetry
entrypoint using native runuser before moving the release pointer.
Inspect actual systemd health and the installed source SHA after restart.
Do not loosen the service's home-directory protection to work around a
root-private interpreter.

**Agent:** Distinguish SDK source contract, real release service UID
execution, and running-service HTTP/Owner readback as separate evidence.
The service-user preflight is explicitly opted in for production; never
claim successful service admission from an unprivileged staging install.
On 203/EXEC investigate the interpreter shebang and complete parent path,
retain the last healthy release, and correct the interpreter location.

## Agent receipt type fidelity (2026-11-14)

Agent-facing `execution.submit` and `execution.cancel` only project
nonempty native JSON string `status`/`attemptState` and optional
`deliveryDisposition`. Do not convert malformed Owner values using
Python `str()` or treat unknown variants as success. Preserve future
nonempty string states as Owner-owned opaque vocabulary. Source TDD:
`tests/test_execution_receipt_types.py`; native Gateway verification
remains necessary. A typed receipt does not attest the physical effect.

For Agent-facing execution.get Artifact completeness, the Owner's qualified
job.get artifact count must match **distinct, nonblank Artifact IDs** from an
explicitly list-valued, fully qualified job.observe inventory, not merely the
number of rows. If an Owner response contains a malformed list, missing or
invalid entries, or duplicate IDs, the Gateway performs its existing one
bounded refresh; unresolved identity coverage stays incomplete even when the
Owner summary count is 0. Never fabricate a missing Owner Artifact or treat
an unqualified count as a success witness.

## R08 Linux PG Runtime business delivery — historical incident, closed

**Historical cause:** A former installed Runtime published an incomplete MCP
output schema for the PostgreSQL scheduling facet. An earlier Gateway release
therefore used a narrow typed SDK request workaround for six Linux business
tools. That workaround is **retired**, not a live design requirement. Do not
copy it into a new gateway/owner adapter or a new Agent Skill.

**Current contract:** Linux Runtime operations `workspace.exec`, `job.list`,
`job.observe`, `job.get`, `job.cancel` and `artifact.read` use the official
high-level MCP SDK `Client.call_tool`. Gateway retains exact Owner Job,
request and Artifact identity checks, with no second physical effect submission
after an ambiguous response. Source PR #2320 and production Gateway maintenance
0.10.12 have independently passed real Linux execute → resolve → observe →
UTF-8 Artifact/digest checks; Windows Session 1 Gateway readback passed as
a separate consumer. The installed Runtime also independently fixed the
previous UTF-8 subcharacter read zero-progress behavior.

**Release boundary:** This historical incident closure does **not** qualify
the separate mainline Gateway 0.10.13/41-tool Host/Security credential and
delegation migration. Preserve current `mcp-surface.json` and mandatory
Host/Security admission and physical consumer gates; a test or source merge
alone never proves a protected release is deployed.

## Host exact-message consumer continuity (candidate source)

message.get(messageRef, expectedDigest?) is a bounded-purpose
read-only Host proxy for Agent re-entry/evidence readback. Keep its output
on the Host's natural authority; bind messageRef and the *entire* requested
digest to the existing Gateway host.legacy-read AuthZEN policy, never use
an untrusted ActorRef as authorization. The existing message.search
and topic.resume are not substitutes for an exact digest-checked message.
Gateway sources/tests/mcp-surface.json describe a *candidate*, not the
installed tool list. First qualify the real Host bearer and authenticated
Principal/Actor consumer; do not bypass PEP to preserve old direct clients.

## Host upstream identity after Host HTTP hardening

Gateway Host requests use the existing `ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE`
operator credential, read from a private file on every request. Host verifies
the same service credential through the MCP SDK's native Bearer middleware.
Configure both ends before enabling the authenticated Host HTTP release.
The transport credential does **not** establish a caller's human or Agent
identity or grant object-level Host authorization.

## R12 native Linux Runtime structured release forwarding (source-only)

The Gateway may expose `runtime.release.apply` and `runtime.release.get` as a
fixed `runtime.linux`/`linux-pg` MCP Owner forwarding pair, **not** as general
`execution.submit` or a second deployer. Apply accepts only the original
requestId, Workspace, Runtime-owner Git commit, exact candidate manifest digest
and expected Tool count. The existing Gateway HTTP verified Principal scopes the
request ID; the existing Security AuthZEN PEP must explicitly allow the complete
`runtime.release.linux` request before forwarding. Unavailable PDP/unknown
authority stays DENY. Release GET reuses the original Principal-scoped key
without resubmitting any physical effect. Runtime keeps all ReleaseEffect,
operator installation, PostgreSQL, receipt, and rollback authority.

Run `gateway:verify`, `gateway:formal:verify` with the pinned TLA+ JAR,
`test_runtime_release_proxy.py`, then the exact native MCP `tools/list` surface
check. Source acceptance is not proof that the installed Gateway, its current
Security PDP, or the connected ChatGPT Gateway App exposes and authorizes these
Tools. Do not promote the currently divergent Gateway release without proving
all Host/Security consumers work under its AuthZEN credentials. Do not run
`ordivon-runtime-deploy` using `execution.submit` to bypass a missing
`runtime.release.apply` Tool: that lacks the caller's proper ReleaseEffect
admission and original-result recovery contract.

## R8 direct-Host connector migration evidence

The existing ChatGPT `ordivon-host` connector is a real **separate**
consumer of `host-mcp.ordivon.com`, not merely a Host subprocess.
Before changing its endpoint, run the original native MCP SDK
`python3 tools/repo/check_host_gateway_mcp_consumer_surface.py`
from the monorepo root. This reports source tool-set and argument
differences, never a deployment approval. The original Host exposes
31 tools, candidate Gateway 41 with 30 common on source
`682e4c00dad0f9a28792049a415bb236fb0135e3`; same input
property/required sets do not imply output schema or real Agent
permissions match. See
`docs/HOST_DIRECT_CONSUMER_GATE_R7.md` for full physical evidence,
compatibility obligation, and installed native Agent canaries.
Do not reimplement Host output models inside Gateway or assume a
Cloudflare DNS/ingress change migrates a connected ChatGPT Plugin.

## R9 native Host Tool coverage before migration

Run the existing `python3 tools/repo/check_host_gateway_mcp_consumer_surface.py`
and require `sourceConsumerSurfaceQualified=true` **only for the
source Tool name/required-argument baseline**. R9 now rejects any new
Host business Tool absent from Gateway, not only differing arguments on
Tools already shared. `host.pool.stats` is an original Host
operator-only exception that must NOT silently become an Agent Tool.
The comparison is native original Host+Gateway `tools/list`, not a new
hardcoded list of all 30 Host Tools. R10 extends this same source checker
to the original GatewayService `_SOCIAL_WORK_HOST_TOOLS` allowlist, observed
in the locked Gateway environment. Require
`sourceEndToEndSourceQualified=true` for Host business Tool public
registration **and** internal dispatch closure; an absent/extra dispatcher
name fails even when the two MCP Tool sets match. The original
`sourceConsumerSurfaceQualified` is only the earlier public-name/required
baseline, not the full dispatch proof. Input and output Schema differences
remain explicit separate results, and live Security/installed-Plugin
migration remains UNKNOWN until independently verified.

## R13 Runtime self-release discovery (read only, not admission)

The runtime.release.linux immutable route exposes existing native
runtime.release.apply/get functionality through Gateway capability metadata.
Discovery observes only runtime.describe on the fixed runtime.linux Owner;
it does not attempt a release, ask Security to create a grant or execute a
shell. Even if Runtime structuredReleaseConfigured=true, Gateway must keep
available=false with readiness UNKNOWN until deployed tool identity, Security
operator grant and Runtime ReleaseEffect qualification are independently
observed. Exact structuredReleaseConfigured=false is NOT_READY, not a
transport failure. Invalid node identity or boolean status is UNKNOWN.
The MCP source tool input/output contract does not change for a new metadata
route, but normal routeDigest and source package version do change.
Exercise test_runtime_release_discovery.py plus gateway:verify and true
post-deployment readback before claiming readiness. Ordinary execution
readiness must also be grounded in one unambiguous Runtime target with typed
context inventories: refer to README.md "Capability observation lifecycle"
and test_capability_projection.py; malformed Owner data is UNKNOWN rather
than a positive READY or a global discovery exception.
