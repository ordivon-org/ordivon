# External Ownership Boundary

Status: CURRENT ARCHITECTURE POLICY
Lineage: stabilized from the former `ORDIVON_CORE_ZERO_ENFORCEMENT_R3` migration ratchet

## Purpose

This policy prevents repository modernization from replacing one Ordivon-owned abstraction with another. Generic responsibility should remain with a mature external standard, provider, protocol or tool whenever one naturally owns it.

Central rule:

```text
new local semantic authority -> reject
external-owned thin integration type -> explicit admission
existing local type -> migration debt that may shrink
```

The policy is a repository-specific architecture boundary, not a new cross-domain standard. External authorities retain their native semantics.

## Mechanical contract

`policies/external-ownership-boundary.json` records:

- the current Agent Service top-level type ceiling;
- already retired legacy types and persistence surfaces;
- explicitly admitted post-baseline integration types, if any;
- canonical external owners used by the boundary;
- behavioral deletion gates that prevent class-count reduction from overriding correctness.

`tests/test_external_ownership_boundary.py` enforces the machine profile.

Deletion is always allowed. A new top-level Agent Service type is not allowed merely because an older custom type was removed. Any post-baseline type must be non-authoritative, have a narrow integration role, and name its canonical external owner.

## Why this is policy rather than planning

The earlier R3 document described future destructive waves. Those waves have already removed multiple custom stores, coordinators, registries and facades. What remains is no longer a construction sequence; it is a stable non-regression rule.

Therefore:

- implementation waves belong to task-local plans or Git history;
- retired types belong to the machine ratchet only as a non-reintroduction set;
- current architecture policy belongs here;
- specific unresolved replacement decisions remain in `planning/` only while they still affect future work.

## Security exception

Externalization must not weaken confidentiality, integrity, availability or authority scoping. A local component may remain temporarily when no mature replacement owner preserves the existing security boundary. `CredentialReferenceStore` is currently such a documented exception: its locator metadata must not be moved into a broader shared journal merely to reduce the local class count.

## External ownership baseline

The machine profile currently names external owners including A2A, Temporal, CMMN, SACM, OPA, OpenFGA, SPIFFE, CloudEvents, OpenTelemetry, W3C PROV, OpenLineage, SLSA, in-toto and RFC 9562. Their inclusion is a mapping aid only; it does not combine them into an Ordivon super-standard.

## Long-term maintenance

When a legacy type is deleted and parity is proven, tighten the ceiling. When a new integration type is genuinely required, record its external owner and non-authoritative role before admission. Do not add local architecture vocabulary merely to make the profile look complete.
