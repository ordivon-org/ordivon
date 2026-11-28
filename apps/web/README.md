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

Challenge persistence is isolated in `src/store-challenges.ts`, using the
existing WebStore connection and one-shot transaction. Creation captures a
single JSON payload snapshot; consumption validates its stored digest and
decodes the payload before marking it consumed. Malformed or mismatched
storage fails closed and rolls back. The digest is an integrity consistency
check, not cryptographic protection against an actor who can rewrite both
payload and digest in the database.

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

- Node 26.12.1;
- pnpm 12.16.1;
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

## Agent effect response consistency

`src/agent-canary-routes.ts` registers the delegated canary mutation routes
and shares their admission/receipt orchestration. The Security-owned evaluator
and WebStore transaction remain separate. After the asynchronous decision,
exact replay is reconciled before any new approval or effect; current grant
uniqueness, identity, digest and revision are checked before STEP_UP or ALLOW.
A response code alone is not a general proof of domain completion: the
committed receipt is the canary's authoritative result.

See [the bounded protocol model and concrete race witnesses](formal/README.md).
Use `mise run web:formal:effect-response` from the repository root when the existing
pinned Runtime TLC JAR is available.

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

The website does not import Security Rego or OAuth/DPoP lab internals. It
invokes two explicit Security-owner contracts:

```text
agent-request-verifier-v1
  -> OAuth/JWT/DPoP Agent authentication

agent-admission-v1
  -> Agent Admission + Effect Admission policy chain
```

The Website supplies its own SQLite-backed DPoP replay guard to the verifier
contract, so Security owns protocol semantics while the Website remains the
durable owner for its local replay state.

Current evidence:

```text
evidence/HUMAN-RAIL-BROWSER-E2E-R1.json
evidence/AGENT-AUTHORITY-BROWSER-E2E-R1.json
evidence/AGENT-NATIVE-WEBSITE-E2E-R1.json
```

The Agent authority tests additionally prove R2 commit/exact replay/conflict,
R4 effect-bound approval consumption, Grant revocation semantics, fail-closed
ambiguous Grant resolution, and fail-closed behavior when no Security-owned
Agent verifier is configured.

The full Agent-native E2E additionally proves a real Keycloak DPoP-bound token,
missing-proof and wrong-key rejection, DPoP proof replay rejection, R2
autonomous commit, R4 browser WebAuthn STEP_UP, Grant revocation, future-effect
denial, and preservation of historical exact replay.

The website is not yet production eligible. Real account-bound initial
enrollment, recovery, production TLS/origin configuration, Agent Passport UI,
production storage/backup acceptance, security notifications, and deploy/release
acceptance remain separate gates.

The Security-owned OAuth/DPoP verifier uses an accepted pinned RFC 7800 /
Keycloak interoperability profile for oauth4webapi 3.8.8. That profile is
cryptographically tested and is not, by itself, a production blocker. Upstream
removal remains preferred.


## Read-only operator grant view

The first browser operator slice is GET /operator/grants. It reads the
current authenticated Principal's existing Web-owned Grant records and
renders a fresh observation with the server clock, revision, quota and
scope. It is not an admission or execution surface: "Candidate" means
only that the observed Grant is active, unexpired and has positive quota;
request-specific Security and transactional commit checks remain necessary.
Expired, exhausted and revoked are shown separately. The existing API is
unchanged; there is no new persistence layer, browser credential, public
deployment or cross-owner access.

The HTML uses native accessible table/heading/link semantics and escaping.
Successful and denied responses are no-store. Refresh explicitly observes
the current owner; the page is not a live subscription. Browser E2E checks
issue -> view -> revoke -> refresh -> logout -> denial using the existing
virtual authenticator. The framework-independent observation/authorization
boundary is the reference behavior for future React/Solid/UI SDK consumers.


Terminal approval evidence follows the committed Effect: a live pending
approval lookup excludes committed Effects, and the native approval write
does not reopen a consumed record or replace its Principal/digest binding.
Exact replay still returns the historical receipt without changing quota.
This is a Web owner record invariant, not a new authorization provider.
