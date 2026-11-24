# Gateway R32 — First-principles LEGO architecture and directory audit

Date: 2026-11-19. Source: Gateway R31 branch 4c8113c2d818b640945f807f8ff79540d469f641,
built from the actual services/gateway/src/ordivon_gateway package. This
is an implementation/source contract, not a claim about an installed release.
The currently observed Gateway system.describe reported 0.10.12 before this work.

## 1. Goal -> observed reality -> required change

**Goal.** A client discovers a capability, submits a typed MCP request to
its natural Owner through a stable Gateway interface, and receives the Owner's
result or evidence with its status preserved. Gateway cannot replace the Owner
of execution, Work, Artifact, credential or scholarly completion truth.

**Reality.** The original Gateway root had 28 Python modules / 5,599 lines:
routing metadata, projections, direct Owner calls, transport, permissions and
MCP tool registration all lived side by side. R31 physically separated Security
but its PR was not merged when this change began. This round found additional
real cross-module coupling: GatewayService implemented Host RPC directly;
MCP server implemented HTTP transport assembly; Source/CI consumers imported
private GatewayService tool allowlists and read source files from old paths.

**Required change.** Separate representations (logic) from Owner-backed
effects (capabilities), native HTTP/MCP transport, and the independent
Security boundary. Keep a small composition root. Relocate real consumers,
not just implementation files; enforce the dependency direction in tests.

### Thought LEGO guidance (not new runtime objects)

| Thought | Forward question | Reverse question | Architectural effect |
|---|---|---|---|
| T+ Forward purpose | What does the client want to do? | Which public contract expresses it? | Short capability -> route -> Owner path |
| T- Reverse evidence | What would constitute a result? | Which natural Owner can attest to it? | Never promote Gateway observation to Owner truth |
| T0 Representation first | Which distinctions are necessary? | Can UNKNOWN, FALSE and unavailable be distinguished? | Typed projections, stable references and explicit errors |
| T- Reduction | Which capability already exists? | Can a custom duplicate be deleted? | Use native MCP SDK, PostgreSQL Runtime and Host, not new Gateway state |
| T+/- Recovery | What does a client retry? | Can one request be resolved without a second effect? | Principal-scoped requestId, operationRef, read-before-retry |

These thoughts guide every logic transform; they are **not** Agent personas,
authorization proof, automatic approval conditions or a source of new tasks.

## 2. Logic LEGO -> Capability LEGO contract

| Logic | Input -> representation/output; important invariant | Source | Capability (effectful adapter) | Natural truth owner |
|---|---|---|---|---|
| L01 Capability taxonomy | Requested capability -> exact natural Owner/tool route; no overlapping route IDs | logic/routing.py and logic/research_routes.py | A01 capabilities/discovery.py | Runtime, Host, Skills or Research domain |
| L02 Readiness/uncertainty | Owner status/error -> configured/available/UNKNOWN; timeout is not FALSE | logic/capability_projection.py | A01 discovery obtains runtime.describe and host.status | Each observed Owner |
| L03 Invocation port | Typed owner call and response constraints; no hidden retries | contracts.py and logic/owner_protocol.py | A02 transport/upstream.py | The called Owner |
| L04 Operation identity | capability + operationRef -> exact Owner and native ID, reject wrong namespace | logic/execution_refs.py | A03 capabilities/execution/commands.py, observations.py | Runtime |
| L05 Host continuity | Canonical Host tool names and bounded contracts -> one Host operation | logic/host_tool_contracts.py | A04 capabilities/host/tools.py, work.py, social.py, attention.py, dispatch.py | Host |
| L06 Research composition | Study metadata -> advisory recipes and Skill references, never science completion | logic/research_routes.py + contracts.py | A05 capabilities/research.py; Skills exact resolution | Research Study/Skills |
| L07 Trust separation | Verified ingress identity + server-derived target -> allow/deny without mixing identity with Actor claims | security/authorization_targets.py + security/ingress_identity.py | A06 security/authzen_authorizer.py, access_auth.py, capability_authz.py, owner_identity.py | Cloudflare/Security/Owner |
| L08 Effect evidence/release | Request/receipt -> observed runtime state; SourceCut is not installed version | contracts.py + logic/execution_refs.py | A07 capabilities/execution/release.py; packaging/ and systemd/ | Runtime, systemd |
| L09 Protocol publication | Stable tool names/inputs -> native MCP SDK HTTP or stdio | Public contracts.py, mcp-surface.json | A08 transport/http.py, mcp_server.py, transport/upstream.py | Transport endpoint, never business truth |

Logical contracts have no Owner network effects. A capability may call another
capability only via the shared OwnerToolCaller port; it must not import the
concrete MCP transport implementation. Security may read canonical logical
tool names and execution references; business code must not decide JWT
validation, PDP results or private credential ACLs.

## 3. Actual post-refactor source tree

    src/ordivon_gateway/
      __init__.py                   existing public GatewayService API
      contracts.py                  stable external wire DTOs, not effect authority
      service.py                    small dependency-injection/compatibility facade
      mcp_server.py                 MCP tool declarations, middleware composition, entrypoint
      logic/
        routing.py                  exact capability-to-natural-Owner table
        research_routes.py          static study/skill recipe metadata
        capability_projection.py    pure Owner observation projection/search
        execution_refs.py           stable execution reference parser/formatter
        owner_protocol.py           abstract caller port / typed-result helpers
        host_tool_contracts.py      canonical Host tool names / byte constraints
      capabilities/
        discovery.py                request-scoped read-only Owner observation
        research.py                 research/Skill recipe resolution (advisory)
        execution/
          commands.py               Runtime submit/cancel forwarding
          observations.py           Runtime resolve/get/artifact forwarding
          release.py                Runtime native release apply/get proxy
        host/
          tools.py                  Host MCP tool registrar
          work.py                   Host Work methods
          social.py                 Space/Topic/Message methods
          attention.py              Host attention methods
          dispatch.py               exactly-one Host call; no synthetic success
      transport/
        http.py                     HTTP origin validation, MCP app, health
        upstream.py                 MCP SDK Owner clients/connection pooling
      security/
        __init__.py                 public Security facade (R31)
        access_auth.py              Cloudflare JWT and local service ingress
        ingress_identity.py         trusted Principal request state
        http_ingress_guard.py       protected tool access guard
        authorization_targets.py    requested target projection
        capability_authz.py         existing policy enforcement
        authzen_authorizer.py       existing optional AuthZEN transport
        owner_identity.py           secure upstream Owner credential/ACL
        entrypoint.py               Security middleware/env composition
        execution_access.py        principal-scoped Runtime request/lookup
        audit.py                    trace correlation, not authorization

The root contains only four Python files. Security is not duplicated under
logic or capabilities. Historical observations remain historical in
docs/architecture/evidence; do not rewrite their Git SourceCut evidence to
pretend a later relocation already happened.

## 4. Concrete dependency graph

    Client
      -> mcp_server.py (stable external tool contract)
      -> Security ingress/PEP boundary
      -> GatewayService composition
           -> logic/ (pure representations, no Owner execution)
           -> capabilities/discovery (Owner status reads)
           -> capabilities/execution (Owner execution and artifacts)
           -> capabilities/host (Host-owned semantic continuity)
           -> capabilities/research (advisory Skill composition)
      -> transport/upstream.py (official MCP client)
      -> Runtime / Host / Skills (natural owners)

No Gateway PG Job store, second workflow scheduler, new approval actor or
replacement Host database was introduced. HTTP/Cloudflare ingress and Owner
credentials are independently enforced by Security; Runtime still owns native
Job lifecycle. A short Gateway maintenance stop remains acceptable, subject to
preserving native Job, data, idempotency and client readback semantics.

## 5. Original file -> new owned module (source evidence)

- capability_catalog.py -> capabilities/discovery.py
- capability_projection.py -> logic/capability_projection.py
- execution_commands.py -> capabilities/execution/commands.py
- execution_observations.py -> capabilities/execution/observations.py
- execution_refs.py -> logic/execution_refs.py
- host_attention_tools.py -> capabilities/host/attention.py
- host_social_tools.py -> capabilities/host/social.py
- host_tool_contracts.py -> logic/host_tool_contracts.py
- host_tools.py -> capabilities/host/tools.py
- host_work_tools.py -> capabilities/host/work.py
- owner_protocol.py -> logic/owner_protocol.py
- research_resolution.py -> capabilities/research.py
- research_routes.py -> logic/research_routes.py
- routing.py -> logic/routing.py
- runtime_release.py -> capabilities/execution/release.py
- upstream.py -> transport/upstream.py
- inline HTTP app body in mcp_server.py -> transport/http.py
- inline Host RPC in GatewayService -> capabilities/host/dispatch.py
- All R31 Security file moves retained; no Security policy behavior change.

## 6. Validation and open truth boundaries

- tests/test_lego_architecture_boundaries.py protects dependency direction
  and tests the positive one-call Host path and negative unknown-tool path.
- Existing full Gateway tests cover stable MCP surface, Runtime command/result
  truth, typed Host tools, Principal binding, Security, Linux and Windows
  transport and SourceCut release checks.
- Root repository consumers of former routing.py/host_tools.py and former
  GatewayService allowlist must inspect the moved canonical code, **not** a
  duplicated compatibility allowlist.
- No deployment or Cloudflare/Host/Security grants were changed by this
  architecture refactor. Whether a new Gateway release is installed is an
  independent observed fact. R31 is a parent PR until merged.
- Residual complexity is intentionally explicit: discovery.py still contains
  owner observation and projection orchestration, upstream.py contains the
  native MCP client lifecycle; separate them only if new tests expose a
  second concrete responsibility, not to manufacture more LEGO files.
