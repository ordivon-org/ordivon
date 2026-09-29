# Authority Obligation R1 — Task-local External Authority Binding

Date: 2026-09-23
Status: **R1 CANDIDATE / NON-AUTHORITATIVE**

## Decision

Cognitive Circuit R1 deliberately does not own permission semantics. C04 adds only the
smallest missing representation between an exact Circuit stage/capability binding and an
external authority owner:

    exact Cognitive Circuit
            +
    caller/Security-authored authority requirement
            ↓
    mechanical binding validation
            ↓
    task-local Authority Obligation
            ↓
    external authority owner

Composition never decides which stages are effect-bearing. Requirement coverage is authored
outside Composition and remains an external responsibility.

## Exact binding

Each requirement binds:

- exact Circuit ID + manifest digest;
- exact stage ID;
- exact capability-binding ID already used by that stage;
- external authority owner ID;
- exact authority-contract reference;
- required/optional standing;
- explicit non-claims.

Compilation copies the capability name and capability owner from the exact Circuit binding,
then emits canonical requirement/obligation/set digests.

## Non-authority law

Every compiled set states:

    mechanicalBindingEstablished = true
    effectCoverageEstablished = false
    authorityGranted = false
    executionAuthorityGranted = false

A valid obligation means only that the caller declares an exact external authority contract
must be satisfied before using this exact Circuit stage/capability.

It does **not** mean the authority owner returned ALLOW, a Grant exists, a credential is
valid, or every effect-bearing stage has been covered.

## Why coverage remains false

Inferring effect-bearing behavior requires semantics owned by Security, the natural
capability owner, or the caller/domain. Composition has no effect-taxonomy authority. It
therefore cannot infer a missing requirement and cannot promote an obligation into an
authorization decision.

A later consumer may fail closed unless a required external decision/evidence reference is
present, but that consumer must validate the owner-native authority contract independently.

## Anti-growth laws

This package must not grow:

- a policy engine or policy database;
- a Grant/permission registry;
- credential storage or validation;
- effect classification;
- authority-owner discovery/ranking;
- an ALLOW/DENY vocabulary owned by Composition;
- execution admission authority;
- a universal IAM model.

## Relation to A03

Gateway/Security A03 remains a separate owner seam. C04 may reference the exact
Security-owned capability-authorization contract, but does not execute or reinterpret it.
The current absence of a graduated production Agent/Grant evidence source therefore does not
block C04 mechanical binding and does not get hidden by it.
