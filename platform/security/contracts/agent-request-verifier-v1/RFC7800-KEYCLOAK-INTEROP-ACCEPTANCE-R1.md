# RFC 7800 / Keycloak DPoP interoperability acceptance R1

Standing: **ACCEPTED_PINNED_INTEROP_PROFILE**

Scope: the Security-owned `agent-request-verifier-v1` contract only.

## External facts

- RFC 7800 section 3.1 defines `cnf` as an extensible JSON object and says
  confirmation members an implementation does not understand are ignored when
  no context-specific requirement says otherwise.
- RFC 9449 defines `cnf.jkt` as the JWK SHA-256 thumbprint confirmation method
  for DPoP-bound JWT access tokens and requires the Resource Server to validate
  the DPoP proof and its key binding.
- Keycloak 26.7.4 emits `cnf.jkt` plus the private
  `cnf.kc-jkt-type="DPoP"` discriminator.
- Keycloak's DPoP mapper is created on the fly for token requests rather than
  exposed as an Admin-UI protocol mapper. In the 26.7.4 bytecode and current
  upstream source, the access-token path sets both the JWK thumbprint and
  `DPOP_JKT_TYPE` directly.
- oauth4webapi 3.8.8 rejects any `cnf` object containing more than one member
  before access-token signature and DPoP validation.

References:

- RFC 7800: https://www.rfc-editor.org/rfc/rfc7800.html
- RFC 9449: https://www.rfc-editor.org/rfc/rfc9449.html
- Keycloak DPoP guide:
  https://github.com/keycloak/keycloak/blob/main/docs/guides/securing-apps/dpop.adoc
- Keycloak DPoP implementation:
  https://github.com/keycloak/keycloak/blob/main/services/src/main/java/org/keycloak/services/util/DPoPUtil.java
- Keycloak AccessToken confirmation model:
  https://github.com/keycloak/keycloak/blob/main/core/src/main/java/org/keycloak/representations/AccessToken.java
- oauth4webapi:
  https://github.com/panva/oauth4webapi

## Local decision

Do not replace oauth4webapi and do not reimplement RFC 9449.

Keep the exact-version pnpm patch for oauth4webapi 3.8.8. The patch is accepted
only because all of the following are true:

1. it recognizes one observed private Keycloak discriminator;
2. when present, that discriminator must equal `DPoP`;
3. it excludes only that discriminator from oauth4webapi's confirmation-member
   cardinality check;
4. it does not bypass `cnf.jkt`;
5. it does not bypass access-token signature, issuer, audience, `htm`, `htu`,
   `ath`, DPoP proof signature, or key-thumbprint binding;
6. the exact package version remains pinned;
7. the compatibility behavior is covered by generated-key cryptographic tests;
8. removal remains preferred once either upstream converges.

## Falsification matrix

The contract cryptographic tests prove:

| Case | Required result |
| --- | --- |
| standard `cnf.jkt` | ALLOW |
| `jkt + kc-jkt-type=DPoP` | ALLOW |
| `jkt + kc-jkt-type=Client-Attestation` | REJECT |
| `kc-jkt-type=DPoP` without `jkt` | REJECT |
| wrong `jkt` | REJECT |

A stock oauth4webapi 3.8.8 differential run against the same valid Keycloak
shape fails before cryptographic DPoP validation with:

```text
UnsupportedOperationError: multiple confirmation claims are not supported
```

The patched package passes that shape and then proceeds through oauth4webapi's
normal cryptographic validation.

## Production standing

The presence of this pinned, tested interoperability profile is **not by
itself** a production blocker.

Production eligibility for the Website still depends on the separate Website
gates: production HTTPS/origin/RP-ID configuration, account-bound initial
credential enrollment, recovery, Agent Passport / Grant product surfaces,
production storage and backup acceptance, security notifications, deployment,
and external acceptance testing.

The profile must fail closed if the package version, patch application, or
Keycloak token shape changes unexpectedly.
