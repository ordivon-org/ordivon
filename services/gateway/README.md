# Ordivon Gateway

Thin, non-authoritative northbound MCP adapter over Ordivon natural owners.

Gateway owns only:
- stable public action names;
- capability projection;
- owner routing;
- request/response compatibility;
- correlation/reference normalization.

**Formal Gateway authorization boundary (B02, source-model proof):** the
protected `artifact.read` path is modeled by
[`formal/GatewayCapabilityAuthzR1.tla`](formal/GatewayCapabilityAuthzR1.tla).
It enumerates target validity, verified ingress identity, exact PDP binding,
qualification, delegated v2 evidence and interactive AuthZEN v3 evidence.
Safe forwarding requires all matching evidence; a decision mismatch,
STEP_UP/DENY, unsupported version, or incomplete evidence cannot forward.
The model is a **finite Owner-local transition abstraction**, not proof of
Gateway Python implementation refinement, PDP correctness, live authentication,
artifact bytes or installed behavior. No global registry or second PEP exists.

- **Human:** from repository root, run `mise run gateway:formal:verify`
  with a digest-verified TLA+ JAR; use the preinstalled shared Runtime JAR via
  `ORDIVON_TLA_TOOLS_JAR=/absolute/path/to/tla2tools-v1.7.4.jar` when
  the Workspace has no local cache. Inspect the four TLC invariants and the
  two expected counterexamples. For physical behavior run `mise run gateway:verify`.
- **Agent:** first pin the Git SourceCut, reuse
  `src/ordivon_gateway/capability_authz.py` and
  `tests/test_capability_authz_middleware.py` as the concrete
  producer/consumer contract, then invoke `gateway:formal:verify`.
  The safe model must complete exhaustive finite-state exploration; the
  reachability and deliberately unsafe model must each yield the **named**
  counterexample. Classify `MODEL_VERIFIED`, `SOURCE_CONSUMER_TESTED`,
  `IMPLEMENTATION_REFINEMENT_UNKNOWN`, and `INSTALLED_UNKNOWN`
  separately. Do not retire concrete auth tests until a real Python-to-model
  refinement proof exists.

R2.1 thought-LEGO B02 — SOURCE_CANDIDATE, not independently ADMITTED or CODE_REFINED:
`I` = protected-call tuple (Gateway-derived target, ingress evidence, PDP decision);
`O` = Forwarded | Rejected(reason), an abstract tagged result;
`S` = finite PEPPhase × target/ingress/binding/evidence flags;
`pre` = protected artifact.read call; Tool-supplied identity is nonauthoritative and PDP input may be invalid;
`post` = Forwarded implies exact qualified binding and either v2 admitted delegated evidence or v3 valid nondelegating AuthZEN proof;
`inv` = the four TLC safety properties;
`eff` = abstract downstream call_next transition; the Python implementation can perform external effects, unproved by this model;
`c` = UNKNOWN(real PDP/provider latency and cost; only finite TLC exploration measured);
`epsilon` = UNKNOWN(concrete Python-to-TLA abstraction/refinement error, PDP and installed effects);
`prov` = TLC v1.7.4 plus current Git and native Gateway consumer tests;
`unfold` = specification → TLC exploration/counterexamples → Python
implementation readset → live Gateway consumer qualification.

**Capability-routing LEGO (B01):** `routes=None` selects the default catalog,
whereas an explicitly supplied empty route map is an intentional no-capability
configuration. Every route entry must be a `CapabilityRoute` whose
`capability` exactly matches its map key. The adapter must reject mismatches,
rather than advertising one capability while dispatching another. Native
contract tests: `tests/test_gateway_service.py` route-identity and explicit
empty-routes cases. This is Gateway projection validation, not authorization to
execute any Runtime or Host effect.

Gateway never owns Runtime Job/Attempt truth, Host continuity truth, Harness run truth, OAuth/credential authority, Plugin/Skill semantics, or domain completion.


### Source boundaries

- **Capability Catalog** (src/ordivon_gateway/capability_catalog.py):
  read-only system description, capability description, search and resolution.
  Observes natural owners; never executes effects or claims domain completion.
  Reuses the canonical capability_projection.project_execution_capability operator.
- **Gateway application facade** (src/ordivon_gateway/service.py):
  stable public signatures, execution dispatch, artifact reads and Host delegation.
  Its discovery methods delegate rather than duplicating catalog rules.
- **Execution Coordinator** (src/ordivon_gateway/execution_coordinator.py):
  submit, resolve, observe, cancel and artifact forwarding to Runtime or
  natural Runtime owners only. Owns neither Job state nor terminal truth.
- **Owner protocol** (src/ordivon_gateway/owner_protocol.py):
  owner response validation and configuration probes. The canonical execution
  reference grammar stays in execution_refs.py; the service.py compatibility
  import of parse_execution_ref remains available.

Dependencies point from service to capability_catalog, execution_coordinator,
and execution_refs. Both specialized modules use owner_protocol for response
validation and reuse the existing execution_refs wire grammar; neither imports
service. Catalog inputs are the owner caller, copied route map and probe timeout. Extraction preserves the public route and JSON
contracts. Behavioral tests establish observed compatibility, not proof
of implementation-level semantic equivalence.

**Execution cancellation identity contract (Gateway B01 / Runtime owner):** the
`execution.cancel` adapter forwards the exact Runtime Job identity from the
northbound operation reference. Before returning an `ExecutionReceipt`, it
must reject a `job.cancel` response identifying any different Job. The same
rule applies to the Linux and Windows Runtime owners; see
`tests/test_gateway_service.py::test_execution_cancel_rejects_mismatched_runtime_job_identity`.
This validates result correlation, not physical process termination or a new
cancellation authority.

B01 is intentionally small. The public schema avoids fast-moving closed enums such as Runtime execution-context values. Provider-owned context data stays opaque at the Gateway boundary; Gateway only lowers the generic envelope into the owner field and leaves semantic validation to the owner.

For `execution.windows`, Gateway accepts either the legacy provider-defined string context or a provider-defined JSON object. A string is forwarded as Runtime `windowsAuthority`; an object is forwarded unchanged as Runtime `windowsContext`. Capability projection prefers Runtime `windowsContexts` when the owner advertises them, so identity/privilege composition remains Runtime-owned rather than duplicated in Gateway.


## Cloudflare Access machine identities

Gateway continues to validate the Cloudflare Access application JWT using
the configured issuer, audience, RS256 signature, trusted JWKS key and expiry.
Interactive Access JWTs retain the original v1 non-empty-sub Principal mapping,
so existing human grants do not change.

Official Cloudflare service-token application JWTs instead use an empty sub
and the signed common_name Client ID. Gateway now projects these through
a separate domain-separated SHA-256 input into the same existing AuthZEN
Principal format. Neither an empty anonymous subject, an unrelated org
token, nor a malformed Client ID qualifies; failed signature/issuer/audience
verification always denies. Service-token identity remains stable across
secret rotations that preserve its Client ID. Cloudflare documentation:
https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/application-token/

**Identity is not delegation.** A verified Cloudflare service token still
requires a trusted explicit Security AuthZEN Principal-to-Actor/tool/resource
grant. Multiple autonomous Agents using the same Client ID cannot be
independently distinguished by this mechanism; use separate Cloudflare
service-token credentials per workload before assigning separate Actors.
The existing shared local Harness Bearer similarly proves only one
machine Principal, not the identity of each calling Agent.

## HTTP Artifact Policy Enforcement — source contract, 2026-11-08

The normal CLI `main()` previously called `build_server(gateway)` without
installing the existing Security capability middleware even on authenticated
HTTP ingress. Merely having `AuthZenPrincipalAuthorizer` and unit tests did
**not** mean the actual CLI served a protected artifact PEP. The HTTP path now
sets `protect_artifact_reads=True` and installs
`GatewayCapabilityAuthorizationMiddleware` before protected Tool forwarding.

Set both optional environment keys for a live AuthZEN PDP:

- `ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT` — a complete HTTPS
  `/access/v1/evaluation` endpoint (validated by the existing AuthZEN adapter)
- `ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE` — absolute private
  credential-file path; the existing Owner private-file helper reads and checks
  its permissions per decision. No secret is logged or included in Tool output.

If both are absent, HTTP starts without a PDP but denies **qualified
`artifact.read`** with `CAPABILITY_AUTHZ_UNAVAILABLE` rather than silently
calling its owner. An incomplete pair fails at startup. An unverified ingress
identity fails before PDP; target validation and principal/resource binding
remain server-derived. The accepted v3 AuthZEN decision is not an Agent Grant
or proof of physical bytes. The existing stdio lane has a different local OS
trust boundary and is **not** claimed to use HTTP ingress/PDP authentication.

**Original Host read/write PEP (compatibility release):** Reuses the same
Security AuthZEN middleware for the 16 original Host read and 13 original
Host write tools on verified HTTP ingress, with canonical request binding,
actual Owner selectors and an explicit global-read distinction. For
message.post, the real author is authorActorRef; an ignored caller actorRef
never becomes writer authority. Without an installed Security PDP, all
qualified Host reads/writes DENY. A service bearer is not a grant to any
claimed Actor. Source coverage is checked against the real MCP SDK tool
surface. This release deliberately does not register Rust-only
work.engagement tools. They remain in the separate Rust Host draft PR.
The independent installed Security AuthZEN/OPA policy must provide
operator-provisioned Principal-to-Actor grants with exact tool/resource
scope before Gateway rollout, and actual allow/deny consumers must pass.

**Candidate version 0.10.10, Surface Epoch 11 (source-only):** message.get is a
single newly promoted Host read to preserve exact messageRef /
expectedDigest evidence readback when an authenticated Agent migrates off a
direct Host connector. It forwards to Host without persisting or reinterpreting
the message and uses the existing host.legacy-read AuthZEN selector plus
full-request binding. This is **not** an authorization grant or an installed
migration, and host.pool.stats remains an operator-local diagnostic rather
than a new Gateway surface. A source/PDP test cannot substitute for the
actual trusted Principal, Security Grant, Host Bearer pairing, and native
positive/negative Agent consumer before deployment.

This is **not a global Gateway security gate**. Execution submit/cancel,
Skills and other Owner capabilities remain separately qualified; STDIO
uses the existing local OS trust boundary rather than HTTP Principal/PDP.
The installed Gateway SourceCut and downstream Owner authorization remain
separate acceptance obligations. Native consumers include the original
capability middleware tests, scoped Host read tests, source-surface coverage
and real TCP ingress tests. The Gateway finite-state model is not a proof
of Python implementation or installed production behavior.

## HTTP execution identity cannot downgrade to STDIO (2026-11-08)

The normal HTTP CLI server sets `require_http_execution_identity=True`
for `execution.submit`, `execution.resolve`, `execution.get`,
`execution.cancel` and `artifact.read`. Each of those tools now requires
verified ingress Principal and issuer from the trusted HTTP request state
**before** calling Runtime. Missing or malformed MCP `Context` must not
downgrade a public HTTP operation into legacy, unscoped `requestId`
or skip operation-reference qualification.

This composes two already-existing facts, without another authorization
registry: Gateway derives a Principal-bound owner request ID; for observe,
cancel and Artifact bytes it also resolves the exact operationRef using
that same original requestId and capability. The Runtime Owner remains
responsible for admission, Job/Attempt and physical effects. This does
**not** prove that every authenticated Principal may run an arbitrary
workspace/capability: those scopes and actual Grant/PEP coverage still
require natural Owner evidence.

STDIO is an explicitly separate local OS trust boundary. Its legacy
unqualified request IDs remain supported for local callers; they are not
proof of remote authenticated identity. Native consumer regression:
`tests/test_execution_principal_request_namespace.py`, plus the actual
HTTP `main()` wiring check. Inspect the installed Gateway and Owner
readback before claiming this source refinement is deployed.

## Host northbound boundary

The default external Plugin connects only to Gateway. Gateway exposes normal Host continuity and collaboration actions through stable northbound names while Host remains the semantic owner.

- continuity get/list/observe and adopt/checkpoint/attention (compatibility)
- continuity find/changes (preferred discovery/change vocabulary; mechanical recency only)
- collaboration list/search/post (compatibility)
- collaboration publish (preferred write vocabulary; explicit global or continuity scope)

Gateway currently exposes `host.status` as a delegated, read-only Host status/integrity observation compatibility Tool. Host owns the returned status and evidence; Gateway does not become Host administration or Doctor/recovery authority. The released `mcp-surface.json` and installed MCP SDK surface determine current Tool availability; source registration alone does not prove deployment.

Checkpoint payloads are opaque objects at the Gateway boundary. Host validates the current WorkingCheckpoint schema; Gateway does not maintain a second Host checkpoint ontology.

## Retired external pull workers

The pre-PG external pull worker and its SQLite persistence are deleted.
Gateway startup rejects `ORDIVON_GATEWAY_EXTERNAL_WORKER_DB`; Runtime owns
Job/Attempt/Artifact and Host owns Work/Social continuity. No historical
worker data are imported, migrated or retained by this source retirement.

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

## Gateway B01 routing verification and evidence

Specification: forwarded requests must preserve exact map key, route capability
and owner identity. The finite TLA+ model is formal/GatewayRoutingR1.tla
(safe, reachable, deliberately unsafe configs). The bounded source checker is
formal/check_routing_conformance.py; it compares finite route-map proposals with
the actual GatewayService constructor and reference parser.

Evidence classes must remain separate: SPECIFIED, MODEL_VERIFIED,
BOUNDED_IMPLEMENTATION_CHECKED, SOURCE_CONSUMER_TESTED, INSTALLED_VERIFIED.
General Python-to-TLA refinement, PDP correctness, service identity and physical
effects remain UNKNOWN until independently established. See AGENTS.md and
.agents/skills/gateway-formal-routing/SKILL.md for Human/Agent procedures.

### Owner RPC transport lifecycle
Gateway pools HTTP connections by natural Owner using the upstream MCP SDK's
`httpx2.AsyncClient`; MCP SDK Client protocol sessions remain call-local.
The Gateway server lifespan closes owned HTTP pools. Credentials are resolved
and checked for every HTTP request instead of being frozen at pool creation.
No Gateway Job store, Owner effect retry or MCP protocol reimplementation is
introduced. On deadline cancellation, distinguish `sdk_client_call_cancelled`
from `session_close` in the read-only phase diagnostic: entering a Python
`finally` is not evidence that the SDK finished tools/call or started a
normal close. An interrupted call can still spend time unwinding the SDK
transport, so a Gateway timeout does not prove Owner failure.
An SDK Client.call_tool may issue a **second** tools/list HTTP request
after receiving the tools/call response for output-schema validation:
the SDK-call phase does not identify which underlying wire request timed out.
An isolated real-HTTP counterexample exercises a completed Owner tool followed
by a delayed schema listing (MCP Python SDK issue #3513). Keep the SDK's
validation and modern HEADER_MISMATCH recovery; use upstream OpenTelemetry
httpx2 instrumentation to attribute wire subrequests before changing pooling.
Run Gateway source tests plus native loopback and installed-Owner
readback to distinguish transport correctness from deployed availability.

### Verified Owner protocol pin (opt-in; MCP SDK native)

With upstream MCP Python SDK v2, `Client(mode="auto")` probes
`server/discover` and falls back to a legacy initialize handshake. For
**a specifically verified** Windows Runtime that supports the 2026-07-28
stateless MCP protocol, set `ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE=2026-07-28`
on the Gateway service. The SDK then sends the tool request directly,
without the per-call discovery round trip. The default remains `auto`
for every Owner, including Windows, and `legacy` remains available if
a confirmed Owner depends on handshake-era features. Invalid values
fail closed during Owner endpoint construction.

This is only an SDK connection-mode selection. It changes neither
access credentials, per-request Authorization headers, Endpoint identity,
Owner execution/admission authority, cancellation, nor HTTP connection
pooling. Version pinning must be tested with real Owner `runtime.describe`
under the Gateway service identity, including an unsupported-version
negative control. A future incompatible Owner upgrade must remove or
change the pin before deployment; the fixed modern mode does not silently
fall back to an older protocol. The upstream Client may perform the
spec-defined one-time re-list and resend after a `HEADER_MISMATCH` rejection,
which a conforming server rejects before dispatch; Gateway adds no
application-level retries. Validate that the actual Owner enforces the
header/body boundary, especially for effectful Tools, and preserves
idempotent request IDs. Avoid enabling the pin solely from the SDK
package version. Gateway cancellation warnings remain bounded by the
existing observation deadline. See the Gateway Owner R04/R05 guidance.

## MCP SDK typed Windows Runtime status read (0.10.7 candidate)

The verified Windows-only `2026-07-28` protocol opt-in has one narrow
read-only optimization: an exact `runtime.describe({"schemaVersion":1})`
uses the official SDK `ClientSession.send_request` with its typed MCP
`CallToolRequest`/`CallToolResult`. The SDK `Client.call_tool` driver
otherwise makes a `tools/list` request after each call to discover the
output schema in a fresh session. The typed path avoids that extra network
read but preserves SDK-managed transport, request headers and result typing.
The adapter checks the status response's literal schemaVersion=1, node identity
and targets-list envelope without claiming full output-schema equivalence.
The existing strict B03 projection validates the Runtime's configured and
available booleans; malformed values remain UNKNOWN.

This exception is **not** a general faster tools/call facility. It does
not implement automatic MRTR, output schema refresh, or HEADER_MISMATCH retry,
so its gate is one non-interactive, schema-versioned Owner observation
under an explicitly pinned modern Windows connection only. All other
Owner calls—including Runtime Job effects—continue through the high-level
SDK Client with its full validation and recovery behavior. No new cache,
persistent session, credential identity or effect retry is introduced.
On cancellation, `typed_readonly_call_cancelled` attributes only the SDK
request boundary, not the Runtime's physical availability. Measure
installed-service identity and live Owner observation independently before
enabling protocol opt-in on production.

## Contextual readiness projection (not a tool registry)

Each Gateway CapabilityDescriptor includes the computed `readiness_state`:
`ready` for observed positive provider readiness, `not_ready` for a
negative observation without diagnostic uncertainty, and `unknown` when an
Owner cannot be observed or returns invalid status. Local Gateway
`configured` is a separate fact and never implies Owner readiness. The
legacy `available` boolean remains for existing clients; consuming it alone
loses the critical unknown distinction. The discriminator is computed from
the existing fields and is **not** a second truth database or an admission
decision. In particular, an observation of execution-target readiness does
not prove that an individual Runtime workspace API or domain consumer can
perform a given operation. The Runtime's Job/Attempt and domain consumer own
those respective proofs. For an uncertainty, use direct Owner observation
under the actual intended execution identity; do not permanently blacklist
the capability based on a Gateway timeout.

## Search observation isolation and immutable route identity (0.10.3)

`capability.search` first matches capability names, descriptions and tags against the
in-process route table. Only matching routes may cause read-only Owner observations.
A Research-only query or unknown capability has zero Owner RPCs; querying
`execution.linux` does not preflight the Windows Runtime. This is an optimization
of *discovery*, not a bypass of the existing Owner authorization/admission checks.
The `includeUnavailable` filter is applied **after** matched Owner observations,
so unknown readiness is still returned under the existing compatibility rule.

`route_digest` is the canonical SHA-256 of the **entire immutable in-process**
route table, including identity, mappings and public descriptive metadata but
excluding credentials, endpoint addresses, and all live observations. It remains
stable when an Owner changes readiness. It is not a signed source/installed-release
attestation and says nothing about whether an operation is authorized or executable.
`system.describe`, `capability.describe`, and `capability.search` expose this
independent route identity. The pre-existing `projection_digest` remains a
**dynamic observation-content digest**. On a search, it now covers all metadata
matched candidates (before `includeUnavailable` and `limit` filtering), not
the entire catalog; it may change when an Owner status or timeout message changes.
Call `capability.describe` for an explicit live readiness observation, and use
`system.describe` for the fastest route-inventory read.

This follows MCP's deterministic discovery / cache hint semantics rather than
adding a Gateway cache, database, queue, or authority. The route map stays
process-scoped and must pass the standard SDK surface/SourceCut release gates.

## Agent tool exposure and transient owner observations

Gateway `capability.describe` is a bounded, *read-only current observation* of
the natural owner; it is not an installed-software inventory or a stable
readiness certificate. An `available=false` response accompanied by an
`observation_error` such as `TimeoutError` means the projection **failed to
observe owner availability**, not that Windows Runtime execution was proven
unavailable. Do not confuse it with `configured=false` or treat it as permission.

For a Windows mismatch: compare `execution.windows` via Gateway
`capability.describe` with direct Windows Runtime `runtime.describe`,
the service's listening socket and authenticated `runtime.describe` from
the Gateway service identity. Retry the read-only observation only when it
can change the selection; preserve failed observations rather than fabricating
an `available=true` cache. The Runtime owner remains the authority for Job,
Workspace, Target, executable and Windows execution context.

For tools installed on a node, see the [Workstation live inventory]
(../../platform/workstation/inventory/README.md). For procedure selection
use the [Capability Catalog](../../catalogs/capabilities/README.md) and
relevant Agent Skill. None changes Gateway routing or execution authority.

Research route discovery differs from executable provider discovery: its
configured=true means that the local composition resolver exists, while
available=false and an UNKNOWN observation explicitly mean that no live
scientific tool/provider readiness has been proved. Research remains queryable
through default capability.search and resolvable via capability.resolve;
includeUnavailable=false must not treat advisory routes as live-ready tools.
The existing search contract deliberately retains entries with an observation
error (UNKNOWN) even under includeUnavailable=false; consumers MUST inspect
each returned descriptor's available and observation_error fields rather than
assuming that search filtering proves a ready provider.

## Linux release: qualify the actual systemd service identity

The stable Gateway unit uses systemd DynamicUser and ProtectHome. The
release Python must be executable by that identity, including every parent
directory of its resolved interpreter path. An SDK/venv check run as root
cannot establish this. Do not use an interpreter beneath /root or /home for
the production service: systemd ProtectHome can make it inaccessible even
when its final binary has execute bits.

Use the existing qualified Python located inside the Gateway service
deployment prefix; the isolated Python 3.15.1 download path is not always
resolvable through the local uv release catalog. For real Linux promotion,
set ORDIVON_GATEWAY_RELEASE_SERVICE_USER=ordivon-gateway alongside the
existing ORDIVON_GATEWAY_RELEASE_PYTHON and
ORDIVON_GATEWAY_RELEASE_UV release settings. The native installer checks
both the installed Python package import and the exact
opentelemetry-instrument entrypoint via runuser under that service account
BEFORE moving the current pointer. If this preflight fails, the installed
service remains at the previous source cut. Keep a known-good release
directory for operational rollback; after a successful promotion, restart
the standard systemd unit and validate health, protected ingress and Owner
readback. On a disposable CI prefix without an installed service identity,
omit the release service user setting.

This is a service-account execution acceptance test, not a proof of all
systemd namespace isolation or production effect correctness. See the
upstream systemd.exec User, DynamicUser and ProtectHome contracts.

## Linux PG Runtime business delivery (temporary installed-schema adapter)

The actual production Linux Runtime has returned a successfully executed Job
and retained stdout Artifacts, but its installed MCP tool outputSchema still
omits the scheduling field present in the physical PostgreSQL Job projections.
The high-level MCP Python SDK correctly rejects this schema mismatch AFTER
the Owner has committed and completed a Job, so Gateway submission receipts,
request recovery, and Artifact reads are unusable through that route.

The Runtime source already contains exact PostgreSQL scheduling output schema
declarations. Until that source is published to the active Runtime service,
Gateway uses the upstream MCP SDK public ClientSession.send_request with typed
CallToolRequest and CallToolResult only for the six Linux Runtime operations
actually consumed here: workspace.exec, job.list, job.observe, job.get,
job.cancel, and artifact.read. The SDK still owns HTTP transport, credential
refresh, session negotiation, structured errors and result decoding. Gateway
keeps its strict Job/Workspace/Artifact identity checks. There is NO retry of
uncertain effects, no second Job registry and no homemade wire client.

This is deliberately not a permanent replacement for complete SDK
output-schema validation. Do not copy the exception to Host, Skills, or
Windows effect calls. Retire the limited Linux bridge when the installed
Runtime advertises conformant schemas AND a real Gateway submit -> resolve ->
observe -> artifact.read business workflow succeeds with high-level SDK calls.

Proof of business delivery requires the original owner Job identity, terminal
evidence, source-qualified output bytes, and an independently verified Artifact
digest. Gateway route readiness and HTTP /health alone do not prove it.


## Agent result-consumer and release admission Golden Road (2026-11-14)

For a typical Agent, the end-to-end chain is capability.describe/search/
resolve -> execution.submit -> execution.resolve/get -> artifact.read ->
the natural domain consumer. Gateway owns the public MCP contract,
caller/Owner reference qualification and faithful projection of the
native Runtime outcome. Runtime's PG Job/Attempt and retained Artifact
truth remain authoritative; terminal Job does not prove Research/Finance
domain completion. Reuse the existing GatewayService, native
ExecutionObservationMethods and HTTP/Owner MCP SDK, not another Scheduler.

**Critical result projection**: A Runtime Artifact chunk is a typed
bounded range, not free-form data. Gateway must reject a non-JSON-boolean
eof, wrong/ill-typed offset, nextOffset outside the requested range,
or non-string content; the string "false" cannot become EOF=True.
An artifact_projection_complete=True claim requires an actual
nonnegative JSON integer from job.get.artifacts.count corroborating
the observed Artifact IDs. If the authoritative total is absent or
malformed, completeness must remain UNKNOWN (None), not True or False.
Likewise exitCode=True cannot be treated as an integer code. Original
native consumers and negative tests:
src/ordivon_gateway/execution_observations.py and
tests/test_gateway_service.py. This is a wire result contract, not a
new Runtime state model.

**Installed release is an independent acceptance stage.** Compare
the exact running /opt/ordivon/gateway/current Git SourceCut, live
MCP SDK tools/list surface/epoch, ingress and natural Security PDP
operator data BEFORE promotion. Existing packaging/install_release.sh
performs native verify_tool_surface.py and MCP SDK verification.
For a staged dry-run, use an isolated PREFIX with its initial current
symlink pointing to the installed release. A private Runtime Workspace
is not traversable by the Gateway service account, so service-user
preflight must use a separate, traversable isolated prefix. Preserve
the existing ORDIVON_GATEWAY_RELEASE_SERVICE_USER check.

When the candidate activates Gateway's Host read/write AuthZEN PEP,
Security must already have **operator-provisioned current Principal
to Actor and tool/resource-scoped grants** and real read/write
allow/deny consumers must pass. Merely supporting host.legacy-read
and host.legacy-write in OPA Rego does not produce grants. An empty
live grant set is a **NO-GO** for a service-continuity-preserving
upgrade: the new correct fail-closed PEP would deny the existing
Host operations. Never fabricate Actor delegation from a Tool
actorRef, a shared local bearer, a Cloudflare Access JWT, or CI PASS,
and never bypass the PEP to make a release look ready.

Keep the source-qualified candidate if needed, but leave production
symlink/service unchanged until Security operator authorizes actual
delegations, the natural Host direct-channel migration is qualified
and a candidate service-account+Owner canary passes. Any promotion
must be followed by live Gateway/Host/Artifact readback rather than
just a source-manifest test.


### R3 production precondition: current Security credential, not a source file

The native Gateway installer now calls its read-only
packaging/check_live_host_admission.py **only** for the real
/opt/ordivon/gateway production prefix, before changing current.
It reuses the existing Gateway Host Tool registry and reads the
currently loaded Security PDP systemd credential from
/run/credentials/ordivon-security-gateway-authzen.service/trusted-issuer,
not the /etc source file that may not yet have been loaded by the
running PDP. It also checks that the Security PDP is active and that
the Gateway unit declares a Host Owner bearer credential.

A result of status=NO_GO (exit code 3) means that at least one
**necessary** installed continuity prerequisite is absent or cannot
be established. This is a release stop, not an excuse to bypass
Gateway's AuthZEN PEP. A result of
status=NECESSARY_PRECONDITIONS_PRESENT (exit 0) does **not** attest
that all existing Principals have correct Actor grants or that
the Owner credential is accepted. The output deliberately lists
remaining live authorization, direct Host and canary obligations.
It never prints Principal IDs, Actor references or credential data.

Read-only current-instance inspection can be performed with the
installed Gateway Python environment, for example:

    uv run --locked --project services/gateway python services/gateway/packaging/check_live_host_admission.py

Actual November 14 source investigation (NOT a universal future fact):
running Gateway=0.10.8, Host HTTP accepts anonymous local MCP
initialize (200) while Gateway rejects the same request (403);
the Security PDP is active and knows the Host authorization policy
but its active loaded operator credential contains no
gateway_host_actor_grants; Gateway's active systemd unit does not
declare ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE. Therefore candidate
0.10.9 deployment is **NO_GO** while existing Host Agent consumers
must keep working.

The correct cross-service sequence is to identify the **actual**
verified Agent Principals and their authorized Host Actors and
scopes; have the Security operator provision the corresponding
operator-controlled policy data; restart/reload the Security PDP so
the currently loaded credential reflects it; configure the same
Owner bearer through the native Host/Gateway systemd credential
facilities; qualify the original Agent read/write allow/deny
consumers; then stage the Gateway through the official installer
and install/authenticate Host without breaking any remaining direct
Host clients. Finally verify the running exact Gateway/Host versions,
real tools/call, Owner identity, expected denial and normal
Work/Topic/Message consumption. The ordering of the two service
switches must be tested with the current consumers, not guessed.

Do not infer cross-Agent Principal->Actor permission from successful
legacy Gateway message.post, use a shared Principal for every Actor,
manufacture test grants in the live operator policy, or treat an
isolated unit test's positive AuthZEN decision as an installed result.


### R4 direct Host MCP ingress: an independently observed release condition

The Gateway production release preflight must not infer that Host HTTP is
protected merely because a Host bearer setting or a Security Actor grant
exists. The running Host could still be an unauthenticated HTTP binary.
The preflight sends an unauthenticated, read-only MCP initialize request
to exact local Owner route http://127.0.0.1:8898/mcp using stdlib HTTP,
without redirects, HTTP proxies, cloud egress, Authorization or Actor
claims. Only HTTP 401/403 counts as the necessary negative property.
HTTP 200, redirects, other HTTP responses, timeout, connection failure or
a different installed Gateway Host route return NO_GO before production
symlink promotion. The fields anonymousHostInitializeDenied and
hostOwnerRouteQualified are not authority to act as any Principal.

The negative canary does NOT demonstrate a valid Gateway workload bearer.
Before any live release, reuse original MCP SDK HostServiceTokenVerifier
and Gateway McpOwnerCaller consumers with the same installed services:
(a) anonymous Host rejection, (b) authenticated Gateway-to-Host positive
host.status, (c) current Security PDP allow/deny for actual Agent Principal,
Actor and specific resource, (d) original Work/Topic/Message read/write
consumption, (e) migration of existing direct Host clients. Direct Host
callers do not silently inherit Gateway AuthZEN authorization.

Observed 2026-11-14 live result: NO_GO because loaded Actor grants=0,
Gateway Host bearer declaration missing, and Host anonymous MCP initialize
returned HTTP 200. This is local installed-service evidence, not a claim
about public Internet anonymous reachability.
