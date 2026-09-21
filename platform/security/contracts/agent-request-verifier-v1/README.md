# Agent Request Verifier Contract v1

Security owns this public contract for Resource Servers that need to authenticate
a delegated Agent request.

The contract verifies:

- Authorization Server discovery;
- JWT Access Token signature/claims;
- expected audience;
- DPoP-bound access-token semantics;
- the request's DPoP proof;
- proof-of-possession binding;
- one-shot DPoP proof identity through an injected replay guard.

Successful output is intentionally small:

```text
agentId
clientId
subject
```

It does **not** resolve delegation Grants, run Agent Admission, mutate effect
budgets, execute domain effects, or persist receipts.

The caller owns the replay-state substrate by implementing `DpopReplayGuard`.
This keeps protocol semantics in Security while allowing the application's
transactional database to own its local durable state.

## RFC 7800 / Keycloak interoperability profile

Keycloak 26.7.4 emits the standards-defined DPoP `cnf.jkt` together with the
private discriminator `cnf.kc-jkt-type="DPoP"`. Keycloak's DPoP protocol
mapper sets that discriminator directly when it binds an access token to a
DPoP proof; the mapper is created on the fly for token requests rather than
being an Admin-UI mapper.

RFC 7800 section 3.1 makes the `cnf` object extensible and says confirmation
members that an implementation does not understand are ignored in the absence
of a context-specific requirement. RFC 9449 requires the DPoP `jkt` binding
and proof validation.

oauth4webapi 3.8.8 is intentionally stricter: before signature/DPoP validation
it rejects a `cnf` object containing more than one member. The pinned pnpm
patch narrows that mismatch only for the observed Keycloak discriminator:

- `cnf.jkt` is still required by the normal DPoP validation path;
- `kc-jkt-type`, when present, must equal `DPoP`;
- only that discriminator is excluded from oauth4webapi's confirmation-member
  cardinality check;
- access-token signature validation, issuer/audience validation, JWK
  thumbprint binding, `htu`, `htm`, `ath`, proof signature, and replay
  handling remain owned by oauth4webapi / the contract replay guard.

The contract test suite uses generated cryptographic keys and real DPoP proofs
to prove the compatibility behavior and the fail-closed cases for a missing or
wrong `jkt`.

This is an explicit, pinned interoperability profile rather than a replacement
JWT/DPoP implementation. Remove the patch when Keycloak stops emitting the
private discriminator for DPoP access tokens or oauth4webapi accepts the
extension upstream.
