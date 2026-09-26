# Improvement Circuit Profile R1 — Governed Improvement as Composition

Date: 2026-09-23
Status: **R1 EXTRACTED PROFILE / NO NEW RUNTIME OBJECT**

## Decision

Two materially different successor cases now exercise the same bounded structure:

1. historical Harness RSI P2 -> P3, where the improvement mechanism itself was in the change set;
2. prospective Ordivon RW6, where a persistent self-change was produced without changing the improvement mechanism.

That repeated pressure is sufficient to name the composition pattern, but not to create another service, controller, scheduler, evaluator, database, workflow engine, or promotion authority.

The extracted profile is therefore:

```text
scoped objective
    +
exact predecessor
    +
task-local improvement process / Cognitive Circuit
    +
candidate materialization through existing owners
    +
frozen Evaluation Boundary
    +
Verification Obligations bound to natural verifiers
    +
Successor Contract
    +
external Promotion Policy reference
        ↓
Improvement Circuit Profile R1
```

The profile is an architecture relation over already-existing contracts. It is not a new durable state machine.

## Required separation

The profile preserves:

```text
target/proposal
    !=
candidate materialization
    !=
evaluation
    !=
successor-gate closure
    !=
promotion decision
    !=
physical Git/release/deployment mutation
```

The same implementation may participate in more than one role only where the natural owner explicitly permits it; authority identities remain distinct.

## Canonical objects reused

- Cognitive Circuit R1: task-local composition and owner-scoped stages.
- Experimental Episode R1: non-authoritative analytical projection when an experiment consumer needs it.
- Evaluation Boundary R1: freeze-before-evaluate and holdout separation.
- Verification Obligation R1: exact gate-to-verifier binding without discovery/ranking.
- Successor Contract R1: exact predecessor/candidate and succession-gate binding.
- Runtime / Harness / Domain owners: physical execution, cognition, domain state and evidence.
- Primary-main integration policy: external promotion mechanic only after qualification.

No new generic schema is introduced in R1 because the existing objects already carry the necessary identities and boundaries.

## Evidence basis

Historical case:
- `meta/next/evidence/acceptance/rsi-successor-contract-r1-20260922.json`
- recursion class: `IMPROVEMENT_MECHANISM_IN_CHANGE_SET`
- externally anchored evaluation
- mechanical successor closure true
- promotion authority false

Prospective case:
- `meta/next/evidence/acceptance/experimental-rw7-successor-acceptance-20260923.json`
- predecessor: `977e57e6813afa923bf6d69f59e5b25322f336da`
- candidate: `aec6cd0f061703ae367584aa93040b2609c32444`
- recursion class: `PERSISTENT_SELF_CHANGE_NO_MECHANISM_RECURSION`
- externally anchored evaluation
- mechanical successor closure true
- promotion authority false

Post-closure promotion observation:
- the accepted serialized Git integrator later fast-forwarded main from 977e57e6 to aec6cd0f;
- this is a separate authority event after mechanical closure;
- it does not change promotionAuthorityEstablished=false in the Successor Contract projection.

## Why this is enough for a profile but not a new service

The shared invariant is composition, not orchestration:

```text
exact state identity
+
explicit improvement-process identity
+
evaluation frozen outside the candidate
+
natural-verifier evidence
+
successor closure
+
authority separation
```

Both cases already run on existing execution/evidence owners. A new controller would duplicate Runtime/Harness/Temporal/Git/policy responsibilities and would create a second authority path.

## Admission rule for future growth

R1 remains a profile until a future consumer demonstrates a missing machine-enforced relation that cannot be expressed by the existing contracts.

A third consumer alone is not sufficient. It must expose a repeated missing relation.

Only then may a new bounded schema/API be proposed.

## Non-claims

This profile does not establish:
- open-ended recursive self-improvement;
- autonomous scientific or domain improvement;
- a universal fitness function;
- evaluator correctness;
- automatic promotion;
- recursive root authority;
- permission for a system to widen its own authority;
- a global system-state registry.

The intended architecture remains: improvement may recurse; root authority does not.
