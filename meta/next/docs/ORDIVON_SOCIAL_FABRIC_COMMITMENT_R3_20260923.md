# Ordivon Social Fabric Commitment R3

Status: candidate implementation slice.

## Purpose

R3 implements SF41 policy-defined quorum shadow and SF42 explainable commitment projection on top of R2. It deliberately stops before any owner-native resource lease, execution admission, or EffectAuthority.

## Policy model

OPA/Rego is the policy evaluator. Ordivon does not introduce a new policy language.

The reference profile uses only explicit set and blocker predicates:

- candidate subject prefix applicability;
- required support roles;
- required candidate evidence prefixes;
- explicitly blocking damage reason codes;
- explicitly blocking modulatory dimensions.

There is no support count threshold, weighting, score, ranking, or majority rule.

A support event counts for a required role only when it carries both a role and at least one evidence reference. Repeated support for the same role cannot substitute for a different required role.

## SF42 state machine

The compiler evaluates every applicable R2 candidate independently through OPA.

- zero policy-satisfied candidates -> `NOT_READY`;
- exactly one -> `READY_SHADOW`;
- more than one -> `AMBIGUOUS_MULTIPLE_READY`;
- no policy-applicable candidates -> `NOT_APPLICABLE`.

Multiple satisfied candidates are never tie-broken.

Every state keeps:

- `effectAuthorityGranted=false`;
- `externalEffectPerformed=false`;
- `requiresOwnerBinding=true`.

Therefore `READY_SHADOW` means only that one candidate uniquely satisfies this explicit social policy at this bounded cut.

## Dogfood

Two complementary cuts are required:

1. A synthetic single maintenance candidate with independent `operations` and `storage` support plus `job:` evidence must become `READY_SHADOW`.
2. The real WSL/VHD collision cut from R2 must remain `NOT_READY` because every maintenance candidate is already `inhibited_shadow`.

This proves that the policy layer can express positive readiness without overriding R2 conflict semantics.
