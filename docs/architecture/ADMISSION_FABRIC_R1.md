# Admission Fabric R1 — Ingress Composition Boundary

Date: 2026-09-22
Status: **R1 BOUNDARY IMPLEMENTATION / LIVE CAPABILITY AUTHZ OPEN**

## Decision

Ordivon does not need a new OAuth server, credential vault, identity database, or universal admission protocol.

R1 defines the composition boundary between mature identity/authentication providers, Security-owned authorization semantics, Gateway routing, and natural owners:

```text
caller
  -> transport route
  -> external identity/authentication owner
  -> trusted ingress verification
  -> capability authorization decision
  -> non-authoritative Gateway routing
  -> natural owner
```

The current H2 OAuth/browser flow is retained as an **interactive admission reference circuit**, not as the universal admission architecture.

## Current repository facts

### Public Gateway ingress

`services/gateway/src/ordivon_gateway/access_auth.py` verifies the Cloudflare Access assertion signature, issuer, audience, expiry and subject, then derives a stable pseudonymous principal.

The middleware places only the verified principal and issuer into trusted request state. Tool arguments are not identity.

`docs/architecture/E02_AUTHENTICATED_PRINCIPAL_BOUNDARY_R2.md` correctly classifies this as authenticated ingress attribution, not owner authorization.

### Gateway

Gateway remains a non-authoritative routing projection. It owns stable public action names, capability projection, owner routing, compatibility, and correlation. It does not own OAuth, credential material, Runtime/Host truth, or domain completion.

The HTTP server is already configured with a stateless HTTP transport mode. Protocol-version conformance remains a separate interface-currentness concern; this document does not infer wire-version support from that configuration alone.

### Security

`platform/security` already owns the relevant semantic waist:

- Principal / Agent / Grant / Effect identity separation;
- verified protocol evidence -> normalized policy input;
- OPA/Rego admission decisions;
- ALLOW / STEP_UP / DENY;
- explicit statement that authorization is not effect truth.

Therefore Admission Fabric must compose Security rather than recreate it in Gateway or Harness.

## The real open gap

The current public Gateway has a verified authenticated principal, but its public routing layer does not yet expose a capability-scoped authorization contract between ingress authentication and high-authority actions such as `execution.linux` or `execution.windows`.

R1 therefore records:

```text
AuthN = implemented
principal attribution = implemented
owner routing = implemented

capability-scoped AuthZ at Gateway seam = OPEN
```

Cloudflare application admission may currently provide a coarse outer policy boundary. R1 does not upgrade that coarse ingress decision into per-capability authorization.

## Admission profiles

### H2 — Interactive profile

Purpose: unknown or user-operated external MCP clients.

```text
client
  -> route
  -> OAuth/provider-native interactive authorization
  -> trusted assertion/token verification
  -> Principal projection
  -> capability AuthZ
  -> Gateway route
```

PKCE, browser presentation, loopback callback, CIMD/DCR and refresh-token mechanics belong to the selected OAuth/client implementation or provider. They are adapters, not Ordivon truth owners.

The fixed callback port used during H2 debugging is a regression fixture, not architectural identity. The invariant is transaction isolation.

### H3 — Workload profile

Purpose: first-party unattended software workloads.

```text
workload
  -> provider-native workload identity
  -> trusted workload verification
  -> Agent/workload projection
  -> capability AuthZ
  -> Gateway route
```

H3 MUST NOT require browser presentation or a Human callback during normal operation.

R1 does not select a final production workload-identity provider. SPIFFE/SVID remains a future mature option when deployment topology justifies it; it is not admitted merely for architectural symmetry.

### Managed profile

Enterprise Managed Authorization remains an extension slot only. No EMA implementation is justified by current deployment pressure.

## Registration

Client registration is not a Gateway-owned semantic.

For modern MCP/OAuth clients the preferred resolution order is:

1. pre-registered client relationship;
2. Client ID Metadata Document when supported;
3. DCR only as compatibility fallback.

R1 therefore treats DCR as a compatibility adapter, not a core LEGO.

## Transport

Network v2 / sing-box / VPN is one route adapter. OAuth and authorization semantics MUST NOT depend on whether transport was DIRECT, SYSTEM_PROXY, or NETWORK_V2.

## Human control transfer

Human interaction is required only when the authority semantics require Principal action, consent, step-up, or an intentionally retained root boundary.

Browser launch is presentation. Browser launch failure must not be reclassified as authentication-protocol failure.

## Admission projection

`AdmissionContext` is a conceptual composition waist, not a new public wire schema or persistent identity store.

A trusted adapter may project only evidence it has actually verified, such as:

- principal / workload identity;
- issuer;
- resource/audience;
- client identity when verified;
- granted scope or equivalent authority evidence when verified;
- authentication method;
- expiry/currentness evidence.

Public callers may never self-assert these fields.

## Anti-growth laws

Admission Fabric R1 MUST NOT become:

- a second OAuth authorization server;
- a credential store;
- a global identity database;
- a second policy engine beside Security;
- a session/workflow database;
- an owner-truth proxy;
- a browser automation framework;
- a universal Human gate;
- a reason to deploy SPIFFE/SPIRE, EMA, or PKI before real topology requires them.

## R1 gates

R1 is mechanically acceptable only when:

1. interactive admission and workload admission are represented as separate circuits;
2. both converge on the same Gateway/Security owner boundaries without sharing browser requirements;
3. authenticated Principal attribution remains distinct from capability authorization;
4. Gateway remains non-authoritative routing only;
5. H2 callback-port choice is not modeled as transaction identity;
6. DCR is modeled as compatibility, not core;
7. unresolved capability AuthZ and workload-provider choices remain explicitly OPEN rather than silently inferred.

## Next executable slices

- **AF-S1** freeze these boundaries with task-local Cognitive Circuit manifests and regression tests;
- **AF-S2** close Gateway capability AuthZ for one narrow capability before generalization;
- **AF-S3** bind one non-browser H3 workload identity provider and prove unattended read-only access first;
- **AF-S4** re-run H2 as an interactive reference witness with transaction-isolated callback;
- **AF-S5** migrate/verify the Gateway wire surface against MCP 2026-07-28 independently of authorization semantics.

No later slice may claim domain/effect success from authentication or authorization alone.
