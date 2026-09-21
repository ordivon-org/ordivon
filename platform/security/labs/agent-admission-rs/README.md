# Agent Admission Resource Server Lab

This directory is an isolated, non-production experiment for the Agent Admission
model.

It intentionally separates four semantic owners:

1. **Keycloak 26.7.4** — OAuth Authorization Server and DPoP-bound access token issuance.
2. **oauth4webapi** — Resource Server JWT Access Token + DPoP verification.
3. **OPA/Rego** — stateless Agent Admission and the existing Effect Admission policy.
4. **SQLite** — durable Grant budget and the local website effect transaction.

The lab does not implement OAuth, JWT, DPoP, WebAuthn, or cryptographic
verification itself.

## Local E2E

```text
Keycloak
  -> DPoP-bound client_credentials token
  -> oauth4webapi validateJwtAccessToken(requireDPoP=true)
  -> unique server-side Grant resolution
  -> agent_admission.rego
  -> effect_admission.rego
  -> SQLite BEGIN IMMEDIATE
     -> re-check Grant revision
     -> budget decrement
     -> effect receipt insert
     -> comment insert
  -> COMMIT
```

The server-side Grant fixture represents a delegation that was already approved
by the Principal. A later stage replaces fixture creation with a real
WebAuthn-backed Grant issuance surface.

`X-Ordivon-Effect-Id` is deliberately private application metadata. The
Idempotency-Key work is not treated as a stable HTTP standard in this
experiment.

Exact replay is resolved before current Grant budget checks because replaying a
committed effect creates no new external side effect. The request must still be
authenticated as the same Agent and carry the same effect digest.

## Development

Requires:

- Node 26.9.0
- pnpm 12.5.1
- OPA
- Podman for the Keycloak E2E

The localhost lab explicitly enables oauth4webapi's insecure-request test flag.
Do not carry that flag into any deployed profile.

## Keycloak / oauth4webapi interoperability

Keycloak 26.7.4 currently emits a private `cnf.kc-jkt-type="DPoP"` discriminator
in addition to the standards-defined `cnf.jkt`. `oauth4webapi` 3.8.8 rejects
that two-member `cnf` object before its normal DPoP validation. The lab carries
a narrowly scoped pnpm patch that accepts only this exact Keycloak discriminator
and leaves upstream signature and DPoP validation intact.

See `KEYCLOAK-OAUTH4WEBAPI-COMPAT.md` for the source evidence, RFC rationale,
unpatched control experiment, and mandatory removal gate.

## Local network topology

The first Podman bridge version declared `127.0.0.1:18080 -> 8080`, but on the
current host netavark recorded the mapping without realizing a reachable host
path. Keycloak itself was healthy inside the container network namespace while
the host endpoint timed out.

The lab therefore removes the unnecessary NAT layer and uses Podman host
networking while binding Keycloak itself to **127.0.0.1:18080**. This is a
localhost-only test topology, not a production deployment recommendation.

The E2E harness also reconciles `podman pull` and `podman run` against external
image/container state when a CLI call returns non-zero after the external state
has already committed.
