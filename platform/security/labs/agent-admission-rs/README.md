# Agent Admission Resource Server Lab

This directory is an isolated, non-production experiment for delegated Agent
authority.

It intentionally separates five semantic owners:

1. **Keycloak 26.7.4** — OAuth Authorization Server and DPoP-bound access-token issuance.
2. **oauth4webapi** — Resource Server JWT Access Token + DPoP verification.
3. **SimpleWebAuthn 14** — WebAuthn option generation and registration/authentication verification.
4. **OPA/Rego** — stateless Agent Admission and existing Effect Admission policy.
5. **SQLite** — Principal credentials/challenges, Grants, effect approvals, budgets, receipts, and the local website effect.

The lab does not implement OAuth, JWT, DPoP, WebAuthn cryptography, or signature
verification itself.

## Authority model

The WebAuthn profile exercises this chain:

```text
Principal
  -> WebAuthn credential
  -> one-shot WebAuthn challenge
  -> server-side delegation Grant
  -> OAuth + DPoP Agent
  -> Agent Admission
  -> Effect Admission
  -> R2 autonomous effect

R4 effect
  -> STEP_UP
  -> pending effectId + effectDigest
  -> one-shot WebAuthn approval
  -> same effect resumes
  -> approval is consumed
```

WebAuthn approval is deliberately **effect-bound**, not a broad authenticated
session. Approving effect A does not authorize effect B, and the approval for A
cannot be reused after it is consumed.

Grant issuance and Grant revocation are also WebAuthn challenges. Revocation
prevents future effects but does not erase or invalidate an already committed
historical effect receipt. An exact replay of an already committed effect still
returns the same receipt after its Grant is revoked.

## Two local E2E profiles

### DPoP R1 regression

```bash
pnpm e2e
```

This retains the original bootstrap-Grant experiment so the OAuth/DPoP and
effect-fence behavior has a stable regression profile.

Observed matrix:

```text
missing DPoP proof           -> 401
wrong DPoP key               -> 401
new R2 effect                -> 201
same DPoP proof replay       -> 401
fresh proof + exact replay   -> 200
same effectId, changed body  -> 409
R4 without step-up           -> 428
```

`bootstrap-grant.ts` exists only for this legacy R1 regression profile. The
WebAuthn profile below does not use it.

### WebAuthn delegation R1

```bash
pnpm webauthn-e2e
```

The harness starts Keycloak and the Resource Server, launches Chromium, installs
a CDP virtual CTAP2 authenticator, and exercises registration, Grant issuance,
R2 execution, effect-bound R4 approval, Grant revocation, and cleanup.

The current verified matrix includes:

```text
credential enrollment             -> 201
enrollment challenge replay       -> 409

Grant issuance                    -> 201
Grant challenge replay            -> 409

R2 delegated effect               -> 201

publish A before approval         -> 428
publish B before approval         -> 428
WebAuthn approve A                -> 201
approval challenge replay         -> 409
publish B after approving A       -> 428
publish A after approving A       -> 200
publish A after approval consumed -> 428

WebAuthn revoke Grant             -> 200
revocation challenge replay       -> 409
new effect after revocation       -> 403
historical exact replay           -> 200
```

The WebAuthn step-up hooks are an explicit server profile enabled with
`AGENT_ADMISSION_WEBAUTHN_STEP_UP=1`; they are not silently enabled for the
legacy DPoP R1 profile.

## First-enrollment boundary

The localhost experiment protects initial credential enrollment with
`X-Lab-Enrollment-Token`. This is a bootstrap gate for the lab only.

A production website must replace it with the site's existing authenticated
Principal/account ceremony (or an equivalent enrollment/invitation authority).
WebAuthn cannot by itself answer who is authorized to create the first
credential for a previously unknown Principal.

## Virtual authenticator evidence boundary

The automated E2E uses Chromium's CDP virtual authenticator with CTAP2 and user
verification enabled. It proves the WebAuthn protocol path, challenge binding,
credential verification/counters, Grant binding, and effect binding.

It **does not** claim that a physical human touched a hardware authenticator.
The frozen evidence explicitly records `productionHumanPresenceClaim=false`.

See:

```text
evidence/AGENT-ADMISSION-E2E-R1.json
evidence/AGENT-ADMISSION-WEBAUTHN-E2E-R1.json
```

## Effect semantics

`X-Ordivon-Effect-Id` is deliberately private application metadata. The
Idempotency-Key work is not treated as a stable HTTP standard in this
experiment.

Exact replay is resolved before current Grant budget/activity checks because
replaying a committed effect creates no new external side effect. The request
must still authenticate as the same Agent and carry the same effect digest.

New effects always require a currently active, unexpired Grant with remaining
effect budget.

## Local network and workspace topology

The first Podman bridge version declared `127.0.0.1:18080 -> 8080`, but on the
current host netavark recorded the mapping without realizing a reachable host
path. The lab therefore removes the unnecessary NAT layer and uses Podman host
networking while binding Keycloak itself to **127.0.0.1:18080**. This is a
localhost-only test topology, not a production deployment recommendation.

Runtime workspaces are mounted with restrictive host permissions. The E2E
harness therefore copies the frozen Keycloak realm into a temporary explicit
`0644` mount input and removes it during cleanup instead of assuming that
workspace file modes are container-readable.

The WebAuthn harness also passes the installed Chromium executable explicitly;
it does not rely on Playwright inferring HOME/cache paths inside a Runtime Job.

## Keycloak / oauth4webapi interoperability

Keycloak 26.7.4 currently emits a private `cnf.kc-jkt-type="DPoP"`
discriminator in addition to the standards-defined `cnf.jkt`.
`oauth4webapi` 3.8.8 rejects that two-member `cnf` object before its normal
DPoP validation. The lab carries a narrowly scoped pnpm patch that accepts only
this exact Keycloak discriminator and leaves upstream signature and DPoP
validation intact.

This remains a **lab-only compatibility shim**, not production-eligible code.
See `KEYCLOAK-OAUTH4WEBAPI-COMPAT.md` for the control experiment and mandatory
removal gate.

## Development

Requires:

- Node 26.9.0
- pnpm 12.5.1
- OPA
- Podman
- Playwright Chromium for the WebAuthn E2E

The localhost lab explicitly enables insecure HTTP allowances needed by the
test environment. Do not carry those allowances, the lab enrollment token, the
virtual authenticator, or the compatibility patch into a deployed profile.
