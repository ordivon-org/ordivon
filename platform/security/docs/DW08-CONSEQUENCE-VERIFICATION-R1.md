# DW08 Consequence Verification R1

Status: DWC-specific binding over the existing Security consequence-verification policy.

## Purpose

DW08 verifies one explicit bounded protection predicate after DW07 reports an admitted provider
commit. It never treats an executor/provider receipt as world truth.

The mechanical chain is:

```text
DW07 exact request/admission
        +
DW07 provider receipt (worldEffectVerified=false)
        +
independent authoritative post-effect observation (plane=world-truth)
        ↓
existing consequence_verification.rego
        ↓
verifier-class predicate
        ↓
DW08 bounded verification result
        ↓
task-local Composition Gate result
```

## Verifier classes

R1 supports four bounded templates:

- version
- configuration
- exposure
- attack-negative

Each binding carries exact caseRef, subjectRef, subjectSnapshotDigest, protectionClaimRef,
supportScope and Composition gate identity. It also binds the exact DW07 proposalDigest,
requestId and requestDigest, closing the bridge from the DWC case/subject to the actual
effect request and preventing cross-effect receipt reuse.

## Closure semantics

A provider receipt alone remains UNKNOWN / EXECUTED_UNVERIFIED.

A current authoritative observation plus VERIFIED_CONSEQUENCE may close only the explicit
predicate. Even when that predicate is SATISFIED:

```text
verifiedProtectionEstablished = true
compromiseAbsenceEstablished  = false
eradicationEstablished        = false
recoveryEstablished           = false
domainAcceptanceEstablished   = false
```

Stale/currentness-unknown observations cannot close protection. Mismatched case, subject
snapshot, request identity or request digest fails closed.

Attack-negative evidence additionally requires COMPLETE bounded coverage and an exact scopeDigest.

## Invalidation boundary

The result exposes exact invalidation keys for:

- subjectSnapshotDigest
- verifier binding digest
- authoritative observation source digest

Relevant drift therefore creates a new/revalidated defense epoch rather than mutating old
verified evidence in place.

## Acceptance

The R1 acceptance reuses the harmless DW07 in-memory fixture and the existing pinned OPA
consequence policy. The independent observer is a different fixture owner and reads the
post-effect state independently of the provider receipt.

A synthetic qualification-only circuit is used so the DW07 fixture case and the DW08 gate case
are identical. It does not discharge the historical DW06 ProxyLogon circuit.

No OS, network, Runtime service, Security configuration or external system is changed.
