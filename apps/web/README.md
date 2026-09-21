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

The website is not yet production eligible. Agent Grant/Effect integration,
real account-bound initial enrollment, recovery, production TLS/origin
configuration, and deploy/release acceptance remain separate gates.
