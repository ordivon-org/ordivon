# Gateway AuthZEN H2 Principal Authorization R1

Status: SOURCE CANDIDATE / LIVE ENABLEMENT FORBIDDEN UNTIL PDP + CREDENTIAL OWNER IS QUALIFIED
Date: 2026-09-28

## Decision

Gateway may use the OpenID AuthZEN Authorization API 1.0 Final as the PEP/PDP wire waist for the
H2 interactive-Principal profile. This does not replace Ordivon Agent Admission, Effect Admission,
or natural-owner effect truth.

The two admission profiles remain distinct:

```text
H2 interactive Principal
verified ingress Principal
  -> Gateway-derived capability + resource
  -> AuthZEN Evaluation API
  -> ALLOW / DENY
  -> natural owner

H3 delegated Agent
verified Agent/workload identity
  -> Principal delegation Grant
  -> exact Effect + optional effect-bound approval
  -> Security Agent Admission + Effect Admission
  -> natural-owner effect fence / receipt
```

An H2 AuthZEN ALLOW is capability permission for the already-authenticated Principal. It MUST NOT
be projected as Agent identity, Delegation Grant, effect admission, provider commit, Artifact-byte
truth, or domain success.

## Owner law

- Cloudflare Access / the selected external identity provider owns public authentication evidence.
- Gateway owns PEP composition, server-derived authorization target identity, routing, and
  correlation only.
- The selected AuthZEN-compatible PDP owns the authorization decision for the configured policy
  domain.
- Security owns Ordivon normalization and policy semantics where Ordivon-specific semantics are
  required.
- Delegation Grant, mutable budget, revocation, and effect-bound approval remain with their natural
  authority owner; Gateway MUST NOT persist them.
- Runtime/provider/domain owners remain authoritative for execution/effect/object truth.

## R1 transport contract

`AuthZenPrincipalAuthorizer` sends one standard Evaluation request containing only:

- verified ingress Principal as `subject`;
- Gateway-derived canonical `resource`;
- Gateway capability as `action`.

Caller-authored MCP identity or admission assertions are not copied into the AuthZEN request.

The adapter:

- requires HTTPS, except explicit loopback HTTP for bounded interoperability canaries;
- obtains bearer material through an injected credential provider rather than storing credentials;
- performs no automatic retry;
- requires HTTP 200, a Boolean `decision`, and exact `X-Request-ID` echo;
- fails closed on transport, binding, response-shape, or credential errors;
- emits an internal schema-v3 Gateway authorization decision whose evidence is explicitly
  `interactive-principal-authzen` and whose `authorityProjection` / `effectAdmission` are null.

The existing schema-v2 delegated-Agent decision remains unchanged and still requires admitted
`authorityProjection` plus `effectAdmission` before Gateway may call the natural owner.

## Provider stance

The PEP contract is provider-neutral.

Keycloak 26.7.4 is useful as a same-version interoperability oracle because it exposes an AuthZEN
Evaluation API, but that Keycloak feature is explicitly experimental and MUST NOT be treated as the
production PDP solely because the existing Agent-native website lab already uses Keycloak for
OAuth/DPoP.

Cerbos or another conformant AuthZEN PDP may be used as an independent interoperability oracle or
production candidate. OPA/Rego remains valid for Ordivon Agent/Grant/Effect policy semantics; an
AuthZEN adapter does not require replacing Rego or turning Gateway into a policy server.

## Live gate

Do not wire `AuthZenPrincipalAuthorizer` into Gateway `main()` until all of these are true:

1. a natural credential owner is selected and Gateway receives only a bounded reference/provider,
   not credential persistence authority;
2. one AuthZEN-compatible PDP is production-qualified and at least one independent interoperability
   oracle passes the same request/decision fixtures;
3. policy/resource names for `artifact.runtime` are explicitly configured and default-deny;
4. denied, malformed, unavailable, stale/mismatched identity and object-binding cases prove no
   natural-owner invocation;
5. live enablement has an immediate configuration rollback that removes the authorizer without
   changing owner truth;
6. H3 delegated-Agent authorization remains separately gated on trusted Agent/Grant/approval
   evidence and cannot fall back to H2 merely because a Principal session exists.

## Non-goals

R1 does not create:

- an Ordivon OAuth authorization server;
- a Gateway IAM database or credential vault;
- a universal Grant registry;
- a replacement for WebAuthn, OAuth/DPoP, SPIFFE, or provider-native workload identity;
- a second policy engine beside Security;
- effect idempotency, replay reconciliation, or effect receipts inside AuthZEN.
