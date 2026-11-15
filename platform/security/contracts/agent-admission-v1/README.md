# Agent Admission Contract v1

This directory is a public Security-owner contract for callers that already
possess normalized, verified identity/delegation evidence.

Runtime prerequisites are Python 3's standard library and an OPA CLI with Rego v1
support on the caller's PATH. Consumers must provision these in their own execution
environment. Missing or failing OPA returns a nonzero exit; callers must fail closed.

Input is the existing Agent Admission v0 normalized JSON shape. The caller must
not treat this contract as an authentication protocol: public clients may not
self-assert `authenticated=true`, Principal identity, Agent identity, Grant
scope, or WebAuthn approval. Its `approval.effectDigest` field is optional for
legacy low-risk inputs, but **required by the actual Agent policy whenever a
high-risk verified WebAuthn approval is used**. Both `effectId` and
`effectDigest` must match the current effect. A missing/changed digest returns
`STEP_UP`, never high-risk ALLOW. A trusted natural Owner must authenticate the
approval and bind it to the same effect before constructing this JSON; OPA does
not validate a WebAuthn signature.

The evaluator composes:

```text
agent_admission.rego
        |
        | ALLOW authorityProjection + authorityDigest
        v
effect_admission.rego (source-bound input schemaVersion=2)
```

Output is a single JSON Agent/Effect admission chain.

The evaluator owns policy-location knowledge. Consumers must invoke this
contract rather than import Rego files or Security lab implementation sources.
The public Agent envelope remains schemaVersion 1, but its **internal Effect
Admission input** must be version 2. The adapter checks the policy response's
inputContractVersion, authorityDigestBound and exact authorityDigest before it
returns an admitted Effect. The Rego decision validates binding to its supplied
Authority record; actual source trust and commit-time currentness remain the
natural Owner's responsibilities. Unversioned direct policy requests are
rejected; do not downgrade the contract on a missing digest.

This contract does **not**:

- verify OAuth/DPoP;
- resolve Grants;
- mutate budgets;
- execute domain effects;
- persist Effect receipts.

Those remain separate identity/state/effect owners.
