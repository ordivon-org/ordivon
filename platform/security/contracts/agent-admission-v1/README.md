# Agent Admission Contract v1

This directory is a public Security-owner contract for callers that already
possess normalized, verified identity/delegation evidence.

Input is the existing Agent Admission v0 normalized JSON shape. The caller must
not treat this contract as an authentication protocol: public clients may not
self-assert `authenticated=true`, Principal identity, Agent identity, Grant
scope, or WebAuthn approval.

The evaluator composes:

```text
agent_admission.rego
        |
        | ALLOW authorityProjection
        v
effect_admission.rego
```

Output is a single JSON Agent/Effect admission chain.

The evaluator owns policy-location knowledge. Consumers must invoke this
contract rather than import Rego files or Security lab implementation sources.

This contract does **not**:

- verify OAuth/DPoP;
- resolve Grants;
- mutate budgets;
- execute domain effects;
- persist Effect receipts.

Those remain separate identity/state/effect owners.
