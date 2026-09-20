# Research-adopted policy — OPA reference profile R1

This directory demonstrates the missing executable composition edge between Ordivon research and effect authorization **without** creating a custom policy engine or a `research_to_permission()` shortcut.

## Boundary

The flow is:

```text
Research / evidence / standing
        ↓ informs
Evidence-to-Decision / Structured Decision Making
        ↓ explicit adoption
Institutional decision record
        ↓ administered as policy data (PAP)
OPA/Rego decision (PDP)
        ↓ composed with current delegated authority
Domain/provider enforcement point (PEP)
        ↓
Harness / Runtime / provider effect
```

Research refs in `data.json` are provenance on an **adopted decision**. The Rego policy never treats research standing, model confidence, risk level, evidence count, or Human approval as authority by itself.

`input.delegation` is intentionally a thin placeholder for a current decision from the actual delegation/IAM/capability substrate. It is not a new Ordivon token format. A production binding should translate provider-native IAM/capability output into the request context or use that provider directly when it can enforce the complete policy.

The example policy is deliberately narrow: it adopts a Game research result allowing a delegated Game Agent to run a synthetic evaluator for Station Zero structural claims. It does **not** authorize product commitment, live external effects, or claims whose target variable is irreducibly Human.

## Mechanical check

Run the mature evaluator directly:

```bash
opa test policies/research-adopted-r1 -v
```

The tests establish that:

- research standing alone cannot mint permission;
- an explicit adopted decision is required;
- current delegated authority is required and provider `DENY` is preserved;
- action/resource scope cannot widen;
- high consequence and epistemic `UNKNOWN` do not automatically create a Human approval gate;
- an already adopted operational policy can remain applicable under uncertainty unless its own decision record/reopen conditions say otherwise.

This is a reference profile, not a universal schema. Domains should replace the example data shape with provider-native PAP/PDP/PEP/IAM representations whenever the mature substrate can carry the semantics directly.
