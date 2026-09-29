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

Fresh 2026-09-29 differential canaries prove Keycloak 26.7.4 discovery, client-credential token,
Evaluation ALLOW, `X-Request-ID` echo, `subject.properties`, and `resource.properties`. The same
experimental implementation rejects the AuthZEN-1.0-valid optional `action.properties` member with
HTTP 400. R1 therefore exports only the natural capability identity in `action.name`; Gateway tool
metadata is not authorization authority and is deliberately not copied into the PDP request. This
is deletion of unnecessary transport metadata, not a Keycloak-specific compatibility shim.

Cerbos direct Evaluation ALLOW/DENY canaries also pass, but the tested implementation does not echo
the exact `X-Request-ID`; treat it as a partial interoperability oracle rather than evidence of full
AuthZEN 1.0 transport conformance. The Gateway adapter keeps the standard request-ID binding and
fails closed rather than weakening that contract for a provider.

OPA/Rego remains valid for Ordivon Agent/Grant/Effect policy semantics; an AuthZEN adapter does not
require replacing Rego or turning Gateway into a policy server.

Interoperability evidence:

- Runtime Job `job-01a0eb9b-e4f4-7803-917c-11447df13034`: Keycloak discovery/token/Evaluation/echo
  wire PASS.
- Runtime Job `job-01a0eb9e-6c55-7bf3-ad94-ee9b4e5a3b83`: field differential isolates
  `action.properties` as the Keycloak 26.7.4 experimental parser gap.
- Runtime Job `job-01a0eba2-20cd-7822-8366-bb2da68c61cc`: patched canonical adapter Keycloak
  ALLOW/DENY PASS with exact request-ID correlation and no authority/effect-admission projection.
- Runtime Job `job-01a0e87c-7ba6-7b10-9fa6-b1a1aaf50abf`: Cerbos direct ALLOW/DENY PASS, exact
  request-ID echo absent.

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
