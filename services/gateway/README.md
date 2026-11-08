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

This PEP is **not a global Gateway security gate**: it qualifies only Runtime
Artifact reads. `capability.search`, Host collaboration, execution submit,
cancel and observations are not newly authorized by this specific PEP; their
natural Owner and verified-operation fences must be independently reviewed.
The real installed service profile, PDP availability and complete PEP coverage
are UNKNOWN until deployment observation. Native consumer:
`tests/test_capability_authz_middleware.py`. Abstract model:
`formal/GatewayCapabilityAuthzR1.tla`. Model safety, source-code
behavior and installed release remain separate evidence grades.

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
introduced. Run Gateway source tests plus native loopback and installed-Owner
readback to distinguish transport correctness from deployed availability.
