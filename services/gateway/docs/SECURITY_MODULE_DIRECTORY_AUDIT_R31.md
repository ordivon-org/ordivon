# Gateway Security R31 — directory-first, file-by-file audit

Source: services/gateway/src/ordivon_gateway at SourceCut
6e3e3ca59fc1af5c948fba16d88d8cb4303d9298.
Scope: code ownership and static behavior, **not** installed service status.

## Actual original root source inventory

| Original module | Original responsibility | R31 action |
|---|---|---|
| __init__.py | Public API | Retain in business root |
| access_auth.py | Cloudflare JWT/JWKS/issuer/audience authentication and loopback credential | Move to security/access_auth.py |
| audit.py | Correlation of authenticated Principal, trace and Owner result | Move to security/audit.py; keep original logger name |
| authorization_targets.py | Host and Runtime operation-to-resource selectors and digest | Move to security/authorization_targets.py |
| authzen_authorizer.py | AuthZEN PDP transport and response validation | Move to security/authzen_authorizer.py |
| capability_authz.py | Permission-enforcement middleware and fail-closed decision binding | Move to security/capability_authz.py |
| capability_catalog.py | Capability discovery against Owner | Keep business |
| capability_projection.py | Typed capability descriptions | Keep business |
| contracts.py | Typed external MCP schema | Keep business |
| execution_commands.py | Runtime submit and cancel forwarding | Keep business |
| execution_observations.py | Runtime resolve, get and artifact forwarding | Keep business |
| execution_refs.py | Native execution reference parsing | Keep as canonical contract input for Security |
| host_attention_tools.py | Host attention tool surface | Keep business |
| host_social_tools.py | Host message/topic tool surface | Keep business |
| host_tool_contracts.py | Host public tool set and byte-budget contracts | Keep, consumed by Security without duplicate catalog |
| host_tools.py | Host MCP surface composition | Keep business |
| host_work_tools.py | Work tool surface and Owner error projection | Keep business; consume Security façade for OwnerCallError |
| http_ingress_guard.py | Verified HTTP Principal fence | Move to security/http_ingress_guard.py |
| ingress_identity.py | Trusted request-state identity reader | Move to security/ingress_identity.py |
| mcp_server.py | Tool registration, HTTP transport, previously mixed credential config, PEP setup, request-id scoping | Remove inline security functions; call the security façade |
| owner_protocol.py | Owner call interface and routing configuration | Keep business |
| research_resolution.py | Research capability mapping | Keep business |
| research_routes.py | Research Owner route catalog | Keep business |
| routing.py | Core owner capability route definitions | Keep business |
| runtime_release.py | Typed Runtime release forwarding | Keep business; do not duplicate admission |
| service.py | Gateway service, Host reads and writes, no data-policy ownership | Keep business |
| upstream.py | Owner MCP transport, pool, network call mechanics | Keep business; import credential/identity utilities via Security façade |
| upstream_identity.py | Owner endpoint credential identity and POSIX/Windows private-file protection | Move to security/owner_identity.py |

## Security package after R31

| New source file | Responsibility |
|---|---|
| security/__init__.py | One explicitly named public façade for callers |
| security/access_auth.py | Cloudflare and loopback ingress verification |
| security/audit.py | Authenticated entry audit; logger name preserved |
| security/authorization_targets.py | Canonical domain coordinate to authorization target |
| security/authzen_authorizer.py | Configurable existing AuthZEN client |
| security/capability_authz.py | AuthZEN decision validation and deny/allow enforcement |
| security/entrypoint.py | Environment configuration and middleware composition |
| security/execution_access.py | Verified Principal-scoped idempotency and Runtime operation qualification |
| security/http_ingress_guard.py | Deny protected HTTP tools without verified ingress |
| security/ingress_identity.py | Request-local trusted identity read |
| security/owner_identity.py | Owner endpoint identity, private credential reading, native Windows ACL |

Dependency direction: business MCP/Owner transport -> Security public façade
-> Security implementation. Security may consume canonical domain tool names
and execution reference types; it never performs a Host mutation or Runtime Job.

This is a mechanical architectural refactor. It does not remove AuthZEN,
grant any new access, change Cloudflare policy, deploy a Gateway version,
or claim approval by the legacy release checker.

## Concrete findings

1. The actual mixed-auth entrypoint was mcp_server.py: imported six policy/
   identity modules and inlined Security policy setup, credential environment
   parsing and Principal-scoped Runtime Request IDs.
2. Upstream credential loading and its Windows ACL checks were outside the
   Security package: upstream_identity.py. They now live in owner_identity.py.
3. The audit middleware consumed verified identity but lived at the business
   root. It now lives in the package without changing its existing logger name.
4. Authorization resource construction legitimately depends on canonical
   business schemas in execution_refs.py and host_tool_contracts.py. These
   are one-way read-only contracts, not authorizing business code.
5. The old packaging/check_live_host_admission.py imported the deleted root
   upstream_identity path. R31 corrected this import rather than weakening its
   previous behavior.
6. Authentication vs authorization are distinct: Cloudflare JWT verify and
   AuthZEN PDP continue under current config, without creating a new PEP.

New tests/test_security_module_architecture.py checks file ownership and
that root business modules cannot import private Security internals or directly
construct PEP, CF middleware or private credential readers.

Run: uv sync --offline --group dev, then python -m pytest tests,
ruff check src tests packaging and git diff --check. Live installation,
Cloudflare access configuration and maintenance downtime are out of this
source-only refactor's scope.
