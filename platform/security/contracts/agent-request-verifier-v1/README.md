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

## Keycloak compatibility boundary

Keycloak 26.7.4 currently emits `cnf.kc-jkt-type="DPoP"` in addition to the
standards-defined `cnf.jkt`. oauth4webapi 3.8.8 rejects this extra private
member before normal DPoP validation. This contract carries the same narrow,
tested compatibility patch as the Security lab:

- only `kc-jkt-type="DPoP"` is accepted;
- the private discriminator is excluded from confirmation-member cardinality;
- oauth4webapi signature, JWK thumbprint, htu/htm, and DPoP validation remain
  unchanged.

This shim is a deployment blocker for production eligibility. Remove it when
Keycloak emits the standard confirmation object for this profile or
oauth4webapi supports the discriminator upstream.
