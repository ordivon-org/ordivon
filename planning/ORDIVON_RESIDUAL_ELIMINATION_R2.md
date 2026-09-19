# ORDIVON RESIDUAL ELIMINATION R2

Date: 2026-09-19
Status: CORE_ZERO_PROVISIONAL
Parent: ORDIVON_CORE_ELIMINATION_R1
Source revision: f0bb52bb680542bf45aef1f565ee27b90ba6768e

## Result

The four R1 residual candidates do not qualify as Ordivon primitives.

They are reclassified as integration and conformance responsibilities:

1. cross-standard identity mapping -> adapter/profile responsibility;
2. non-idempotent external-effect reconciliation -> distributed-systems uncertainty handling;
3. semantic completion binding -> domain verification / assurance responsibility;
4. cross-standard conformance -> test/profile responsibility.

Therefore:

```
acceptedIrreduciblePrimitives = []
residualCandidates = []
```

This is a design conclusion only. It does not authorize immediate deletion of production state until replacement parity tests pass.

## R1 — Cross-standard canonical identity mapping

### Elimination

Do not invent one global Ordivon identity.

Each authoritative system keeps its native identity:

- A2A owns its Task, Message and context identifiers.
- Temporal/provider execution owns execution identifiers.
- Git/OCI owns immutable revision/artifact identifiers.
- OpenTelemetry owns trace/span correlation.
- W3C PROV relates different descriptions of the same underlying thing through provenance relations such as specialization/alternate.
- RFC 9562 UUID/URN is available where a globally unique application identifier is actually required.

The adapter keeps an explicit mapping between foreign identities.

The mapping is ordinary integration data, not a semantic kernel.

### Rule

```
native_id != global_master_id
```

and:

```
CrossSystemBinding {
  authority
  nativeIdentifier
  relation
  targetAuthority
  targetIdentifier
}
```

is a profile/documentation shape only. It must not become an Ordivon-owned universal object model.

### Why this eliminates the residual

A2A explicitly treats Task IDs and context IDs as protocol-scoped identifiers. OpenTelemetry Context provides cross-process correlation rather than domain identity. PROV explicitly supports different identified entities that represent the same underlying thing from different perspectives. RFC 9562 already standardizes UUIDs and UUID URNs.

The missing operation is translation, not a new identity theory.

Disposition: ADAPTER_ONLY / NON_CORE.

## R2 — Externally observed non-idempotent effects

### Elimination

There is no general exact-once mechanism for a non-idempotent external API when:

- the caller may time out or crash after issuing the request;
- the provider gives no idempotency key;
- the provider gives no read-after-write/query/receipt interface;
- the effect is not transactionally coupled to caller state.

Under those conditions, an outcome can be unknowable.

A local Ordivon ledger cannot turn an unknowable remote fact into a known fact.

### Standard pattern hierarchy

Use, in order:

1. provider-native idempotency key / conditional operation;
2. provider-native operation ID and result lookup;
3. caller-owned transactional outbox/inbox for state under caller control;
4. durable workflow retry only around idempotent or reconcilable activities;
5. Saga/compensation where the domain exposes a valid inverse;
6. explicit UNKNOWN / RECONCILIATION_REQUIRED when the remote effect cannot be proven.

### Rule

```
timeout != failure
timeout != success
unknown remote effect = UNKNOWN
```

Do not synthesize success and do not silently redispatch an irreversible effect.

### Why this eliminates the residual

This is a fundamental distributed-systems failure mode, not an Ordivon-specific missing primitive. Temporal explicitly recommends idempotent Activities; the transactional-outbox pattern also requires idempotent consumers because publication can occur more than once.

Disposition: STANDARD_PATTERN / NON_CORE.

## R3 — Semantic completion binding

### Elimination

Execution systems report execution facts.

Domain owners decide whether those facts satisfy a domain claim.

Use:

- A2A Task lifecycle for agent-protocol work status;
- CMMN case/milestone semantics for knowledge-work progression where appropriate;
- SACM for structured claims, argumentation and evidence;
- SLSA/in-toto/PROV/OpenLineage for artifact/evidence provenance;
- a domain-native verifier for the actual acceptance predicate.

### Invariant

```
execution_terminal != semantic_complete
process_exit_zero != claim_proven
artifact_exists != artifact_accepted
```

These are conformance assertions, not new runtime states.

### Why this eliminates the residual

SACM already has normative machine-readable metamodels for structured assurance/evidence. CMMN already supplies a standardized case model for adaptive work. A2A defines Task as a protocol lifecycle object. None of these requires one universal Ordivon completion object.

Disposition: DOMAIN_VERIFIER + STANDARD_ASSURANCE / NON_CORE.

## R4 — Cross-standard conformance profile

### Elimination

A conformance profile is not a runtime authority.

It is:

- a list of required standards and versions;
- mapping rules;
- negative constraints;
- behavioral tests;
- compatibility fixtures.

Kubernetes demonstrates the mature pattern: a platform can define a standard conformance test set without inventing an additional runtime semantic object that owns the tested behavior.

### Rule

```
profile -> tests
tests -> evidence
profile != runtime authority
```

Disposition: DOCUMENTATION + TCK / NON_CORE.

## Core-zero conclusion

After R2:

```
Ordivon-specific architectural primitives: 0
Ordivon-specific wire protocols required: 0
Ordivon-specific policy languages required: 0
Ordivon-specific identity system required: 0
Ordivon-specific provenance model required: 0
Ordivon-specific workflow engine required: 0
```

What may remain operationally is a distribution/repository containing:

- pinned external components;
- thin adapters;
- migration code;
- domain-specific verifiers;
- conformance tests;
- deployment manifests;
- documentation.

Those are engineering assets, not an irreducible Ordivon core.

## Replacement boundary

Do not delete a local subsystem merely because this document classifies it as non-core.

Deletion requires behavioral parity for the exact local guarantees that matter.

If an external replacement cannot preserve one guarantee, record the smallest failing guarantee as a migration blocker. Do not promote the old entire subsystem back into the architectural core.

## First destructive migration candidates

Order by confidence and blast radius:

1. Host News -> move out of Host work-control authority.
2. Board authority semantics -> enforce projection-only role.
3. LEGO registries -> remove every runtime/kernel dependency.
4. Agent Service vocabulary -> freeze additions; replace class families by external-native references.
5. custom policy/identity models -> OPA/OpenFGA/SPIFFE adapters.
6. custom Task/Attempt duplication -> differential migration against A2A/CMMN/Temporal.
7. Runtime workflow/controller abstractions -> retain only physical execution adapters after parity.

## External references used for R2

- A2A Protocol specification: https://a2a-protocol.org/dev/specification/
- OpenTelemetry Context: https://opentelemetry.io/docs/specs/otel/context/
- OpenTelemetry context propagation: https://opentelemetry.io/docs/concepts/context-propagation/
- W3C PROV Primer: https://www.w3.org/TR/prov-primer/
- RFC 9562 UUIDs: https://www.rfc-editor.org/rfc/rfc9562.html
- OMG CMMN: https://www.omg.org/spec/CMMN/
- OMG SACM: https://www.omg.org/spec/SACM/2.1
- SLSA 1.2: https://slsa.dev/spec/v1.2/
- Transactional Outbox pattern: https://microservices.io/patterns/data/transactional-outbox
- Kubernetes conformance: https://github.com/cncf/k8s-conformance
