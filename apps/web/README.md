# Ordivon Web

`apps/web` is the first website owner in the Ordivon modular monorepo. It is a
modular monolith, not a new root JavaScript workspace.

## Human Browser Rail

The first accepted slice implements:

```text
Principal
  -> WebAuthn credential
  -> WebAuthn login
  -> opaque __Host-session cookie
  -> server-side Session
  -> CSRF + Origin/Fetch-Metadata protection
  -> authenticated website mutation
  -> audit event
```

Cookie state is deliberately weak in semantics: the browser cookie contains
only a random opaque session token. The server stores only its SHA-256 hash.
The cookie never carries Principal attributes, roles, Agent Grants, OAuth
tokens, DPoP keys, or WebAuthn key material.

Default session cookie:

```text
__Host-session=<opaque>
Secure
HttpOnly
SameSite=Lax
Path=/
no Domain
```

Authenticated mutations additionally require an `x-csrf-token`, exact Origin,
and reject `Sec-Fetch-Site: cross-site`.

## Principal and session state

SQLite is the canary durable owner for:

- Principals;
- WebAuthn credentials;
- one-shot WebAuthn challenges;
- browser Sessions with idle + absolute expiry;
- canary notes;
- append-only audit events.

SQLite is intentionally retained for this canary because no measured scale or
availability requirement justifies introducing Redis, Kafka, or an ORM.

Sessions support:

- list;
- single-session revocation;
- revoke-all;
- idle expiry;
- absolute expiry;
- logout.

## Browser security baseline

Fastify uses its maintained first-party plugins:

- `@fastify/cookie`;
- `@fastify/csrf-protection`;
- `@fastify/helmet`;
- `@fastify/rate-limit`.

The response baseline includes CSP, HSTS, `nosniff`, Referrer-Policy,
Permissions-Policy, and `Cache-Control: no-store` on API/security surfaces.

Errors are projected as `application/problem+json` with a request correlation
identifier.

## WebAuthn boundary

SimpleWebAuthn owns WebAuthn protocol generation and verification. Ordivon owns
Principal/challenge/session semantics only.

Initial Principal enrollment still uses a canary-only bootstrap enrollment
token. A deployed site must replace this with its existing authenticated
account/invitation authority.

The browser E2E uses a Chromium CDP virtual CTAP2 authenticator. It proves the
protocol and browser-session integration but makes no physical-human-presence
claim.

See:

```text
evidence/HUMAN-RAIL-BROWSER-E2E-R1.json
```

## Toolchain

Accepted owner toolchain:

- Node 26.9.0;
- pnpm 12.5.1;
- TypeScript 7.0.2.

`skipLibCheck` is enabled because the current
Fastify/Pino/`thread-stream@4.2.0` declaration graph references the removed
Node 26 `worker_threads.TransferListItem` declaration. Application source
remains fully strict. This is an external declaration-compatibility exception,
not a reason to downgrade Node or `@types/node`; remove it when the upstream
declaration graph becomes Node-26-clean.

## Commands

```bash
pnpm typecheck
pnpm test
pnpm e2e
```

## Delegated Agent authority

The website now owns the product/domain half of delegated Agent authority:

```text
Principal WebAuthn
  -> issue/revoke Agent Grant
  -> Agent request
  -> exact-replay check
  -> unique Grant resolution
  -> Security-owned Agent Admission contract
  -> Effect Admission
  -> R2 canary.note.create
  -> R4 canary.note.publish STEP_UP
  -> effect-bound WebAuthn approval
  -> transaction fence
  -> Effect receipt
```

Browser authority routes remain on the Human trust rail and require the opaque
Session cookie plus CSRF/Origin protections. Agent mutation routes do not
consume browser Cookies or CSRF tokens.

The website does not import Security Rego internals. It invokes the public
`platform/security/contracts/agent-admission-v1` evaluator. Agent request
authentication is an injected `AgentRequestVerifier` boundary; the current
application tests use a verified-Agent fixture while exercising the real
Security admission contract. Promoting the existing oauth4webapi OAuth/DPoP
verifier from the Security lab to a public Security contract remains the final
identity-ingress integration gate.

Current evidence:

```text
evidence/HUMAN-RAIL-BROWSER-E2E-R1.json
evidence/AGENT-AUTHORITY-BROWSER-E2E-R1.json
```

The Agent authority tests additionally prove R2 commit/exact replay/conflict,
R4 effect-bound approval consumption, Grant revocation semantics, fail-closed
ambiguous Grant resolution, and fail-closed behavior when no Security-owned
Agent verifier is configured.

The website is not yet production eligible. Real account-bound initial
enrollment, production OAuth/DPoP verifier binding, recovery, production
TLS/origin configuration, Agent Passport UI, and deploy/release acceptance
remain separate gates.
