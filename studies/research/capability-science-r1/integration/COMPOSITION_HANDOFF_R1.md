# Capability Science -> Cognitive Circuit Handoff R1

Status: **EXPERIMENTAL CONTRACT NOTE / NO AUTOMATIC INTEGRATION**

## Existing owner reused

`packages/composition` already defines the task-local Cognitive Circuit representation and explicitly rejects automatic capability discovery as a Composition responsibility.

Capability Science therefore stops before Circuit admission.

## Allowed handoff package

A caller may use a Capability Science result to author an existing Cognitive Circuit capability binding only when it supplies all of:

1. exact `semanticCapability` artifact reference and digest;
2. standing at least `INFERRED_SEMANTIC_CAPABILITY`;
3. exact natural owner/provider identity or an explicit unresolved owner assumption;
4. exact truth boundary;
5. evidence references supporting the claimed behavior/effects;
6. observation-policy reference;
7. authority and information-flow fields treated as claims/requirements, not grants;
8. unresolved assumptions and explicit non-claims.

If novelty is relevant, the caller additionally supplies the exact `NoveltyWitness` references. Novelty is not required merely to reuse a known capability.

## Forbidden promotions

The handoff must never infer any of the following:

```text
capability discovered
    => permission granted              (FORBIDDEN)
    => execution authority granted     (FORBIDDEN)
    => owner contract satisfied        (FORBIDDEN)
    => Composition Gate satisfied      (FORBIDDEN)
    => domain/scientific acceptance    (FORBIDDEN)
```

Authority requirements continue through the existing `Authority Obligation R1` path. Verification requirements continue through the existing `Verification Obligation R1` path.

## Current R1 integration status

No source change to `packages/composition` is required. This is deliberate: one research study is insufficient evidence to grow the shared Composition waist. Promotion requires independent consumers demonstrating the same irreducible handoff contract.
