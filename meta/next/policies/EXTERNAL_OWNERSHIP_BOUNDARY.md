# External Ownership Boundary

Status: CURRENT ARCHITECTURE POLICY
Lineage: stabilized from the former `ORDIVON_CORE_ZERO_ENFORCEMENT_R3` migration ratchet

## Purpose

This policy prevents repository modernization from replacing one Ordivon-owned abstraction with another. Generic responsibility should remain with a mature external standard, provider, protocol or tool whenever one naturally owns it.

Central rule:

```text
new local semantic authority -> reject
external-owned thin integration type -> explicit admission
retired local subsystem -> must not be reconstructed
```

The policy is a repository-specific architecture boundary, not a new cross-domain standard. External authorities retain their native semantics.

## Mechanical contract

`policies/external-ownership-boundary.json` records:

- the empty Agent Service reintroduction ceiling and completed retirement evidence;
- already retired legacy types and persistence surfaces;
- explicitly admitted post-baseline integration types, if any;
- canonical external owners used by the boundary;
- behavioral deletion gates that prevent class-count reduction from overriding correctness.

`tests/test_external_ownership_boundary.py` enforces the machine profile.

Agent Service deletion is complete. Reintroducing any equivalent top-level subsystem or semantic type requires a new concrete workload, a demonstrated failure of mature external ownership, a non-authoritative narrow integration role, and an explicit canonical external owner; restoring the historical subsystem is not an accepted path.

## Why this is policy rather than planning

The earlier R3 document described future destructive waves. Those waves have already removed multiple custom stores, coordinators, registries and facades. What remains is no longer a construction sequence; it is a stable non-regression rule.

Therefore:

- implementation waves belong to task-local plans or Git history;
- retired types belong to the machine ratchet only as a non-reintroduction set;
- current architecture policy belongs here;
- specific unresolved replacement decisions remain in `planning/` only while they still affect future work.

## Credential-reference retirement

The historical Agent Service CredentialReferenceStore is retired together with Agent Service. No persistent Ordivon credential registry remains in this repository. Credential material belongs to the selected secret/credential provider; OAuth issuer metadata, resource targeting and scope semantics remain owned by RFC 8414, RFC 8707/RFC 9728, RFC 6749/RFC 9700 and provider-native authority.

A future consumer may retain a task-local transient binding only when it is necessary to bind an exact provider handle or least-privilege expectation for that concrete effect. Such a binding must not recreate the deleted Agent Service store, authorization server, protected-resource authority or scope-grant authority.

## External ownership baseline

The machine profile currently names external owners including A2A, Temporal, CMMN, SACM, OPA, OpenFGA, SPIFFE, CloudEvents, OpenTelemetry, W3C PROV, OpenLineage, SLSA, in-toto and RFC 9562. Their inclusion is a mapping aid only; it does not combine them into an Ordivon super-standard.

## Long-term maintenance

The Agent Service ceiling is now empty. Keep it empty. When a new integration type is genuinely required elsewhere, record its external owner and non-authoritative role before admission. Do not restore historical Agent Service vocabulary merely because an old use case reappears.
