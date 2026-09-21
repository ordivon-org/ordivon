# Agent-Native Website Platform R1

Status: architecture baseline with Human Browser Rail implementation started in
`apps/web` and delegated Agent authority implemented under
`platform/security`.

## Kernel

Ordivon treats identity, authority, action, and history as different facts:

```text
Cookie            -> Human browser Session
WebAuthn          -> Principal authority
OAuth + DPoP      -> Agent identity
Grant             -> delegated Agent authority
OPA               -> policy decision
Approval          -> one high-risk Effect authority
Effect            -> exact action identity
Fence             -> commit authority
Receipt           -> historical truth
Evidence          -> accountability
```

No one object may silently substitute for another.

## Three trust rails

```text
Human Browser       Delegated Agent       Workload/Service
     |                    |                    |
Session Cookie        OAuth + DPoP        Workload Identity
     |                    |                    |
Principal           Delegation Grant       Capability
     +--------------------+--------------------+
                          |
                  Authority Context
                          |
                  ALLOW / DENY / STEP_UP
                          |
                        Effect
                          |
                     Effect Fence
                          |
                       Receipt
```

Browser Cookies are never exported or reused as Agent credentials.

## Logical planes

| Plane | Owner fact |
| --- | --- |
| Edge | TLS, public ingress, WAF/rate controls |
| Browser | Cookie, CSRF, CSP and browser response policy |
| Principal | account identity, WebAuthn credentials, recovery |
| Session | temporary Human browser authority |
| Agent | Agent authentication and key possession |
| Workload | software execution identity |
| Delegation | Grants, scope, budget, expiry, revision, revocation |
| Admission | policy, risk classification and STEP_UP |
| Effect | effect identity, replay and commit fence |
| Data | transactional state, outbox and objects |
| Communication | notifications, email and webhooks |
| Evidence/Ops | audit, logs, metrics, traces and receipts |

Logical modularity does not imply microservices. R1 uses a modular monolith for
the website and explicit contracts to platform owners.

## Core invariants

1. Principal is not a Session.
2. Agent identity is not a Delegation Grant.
3. Grant is not an Effect.
4. Policy ALLOW is not commit authority; Effect Fence rechecks mutable authority.
5. Revocation changes future authority, not committed historical truth.
6. LLM output is never an authorization authority.
7. Human browser mutations and Agent mutations use distinct trust paths.
8. Cryptographic protocols remain owned by mature external substrates.

## Human Browser Rail R1

```text
WebAuthn
  -> Principal
  -> opaque __Host-session
  -> server-side Session
  -> CSRF + Origin + Fetch Metadata
  -> domain mutation
  -> audit
```

The session token is random and opaque. Only its hash is stored. Sessions have
idle and absolute expiry, can be listed, individually revoked, or revoked
together.

## Agent Rail

Already-proven platform Security flow:

```text
OAuth + DPoP Agent
  -> unique server-side Grant resolution
  -> Agent Admission
  -> Effect Admission
  -> R2 autonomous Effect
  -> R4 effect-bound WebAuthn STEP_UP
  -> Effect Fence
  -> durable receipt
```

The website owner must consume this through an explicit Security-owner contract;
it may not import Security lab internals merely because the monorepo co-locates
their source trees.

## First canary

The first real product resource is deliberately narrow:

```text
canary.note.create   R2
canary.note.publish  R4
```

A Human Session can create a draft. The Website authority slice now also
implements the product/domain half of delegated Agent execution:

```text
Principal WebAuthn
  -> Agent Grant issue/revoke
  -> unique Grant resolution
  -> Security Agent Admission contract
  -> R2 Agent draft create
  -> R4 publish STEP_UP
  -> effect-bound WebAuthn approval
  -> transaction fence
  -> durable receipt
```

Agent ingress is now bound through the Security-owned
`agent-request-verifier-v1` contract. The full canary E2E proves:

```text
Keycloak
  -> DPoP-bound access token
  -> Security Agent request verifier
  -> Website Grant resolution
  -> Security Agent Admission
  -> R2 autonomous draft
  -> R4 STEP_UP
  -> Principal WebAuthn approval
  -> publish
  -> revoke Grant
  -> future Effect denied
  -> committed historical Effect replay preserved
```

Website unit tests still support an injected verified-Agent fixture so domain
tests do not require an Authorization Server, while the full integration E2E
covers the real protocol path.

The Security verifier also carries an accepted pinned RFC 7800 / Keycloak
interoperability profile around oauth4webapi 3.8.8. The profile preserves
oauth4webapi's cryptographic DPoP verification and only handles Keycloak's
private `kc-jkt-type="DPoP"` confirmation discriminator. Generated-key
contract tests cover standard `jkt`, the Keycloak extension, missing/wrong
`jkt`, and a non-DPoP discriminator. Upstream removal is preferred, but this
profile is not itself a Website production gate.


## External owners

- Browser/WebAuthn implementation: browser platform + SimpleWebAuthn.
- HTTP lifecycle: Fastify.
- Cookie/CSRF/headers/rate controls: maintained `@fastify/*` plugins.
- Agent token and proof verification: OAuth/DPoP mature implementation in
  Security owner.
- Policy: OPA.
- Canary transaction store: SQLite.
- Future deployment edge: existing Ordivon Network/Cloudflare owner.

Ordivon-specific code owns the composition semantics: Principal, Session,
Grant, Effect, risk, approval, fence, replay and evidence boundaries.

## Production gates still open

- real HTTPS origin and RP ID;
- existing-account-bound first credential enrollment;
- passkey add/revoke and recovery;
- Agent Passport / Grant management product surface;
- browser-visible R4 approval product UI;
- production storage/backup/restore acceptance;
- notification/security-event delivery;
- edge deployment and external scan acceptance.
