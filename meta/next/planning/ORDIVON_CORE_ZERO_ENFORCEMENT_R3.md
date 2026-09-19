# ORDIVON CORE ZERO ENFORCEMENT R3

Date: 2026-09-19
Status: ACTIVE_RATCHET
Parent: ORDIVON_RESIDUAL_ELIMINATION_R2

## Purpose

R2 reduced the accepted Ordivon architectural core and residual candidate set to zero. R3 makes that conclusion mechanically enforceable.

Central rule:

    new local semantic owner => FAIL
    external-owned thin integration type => explicit profile admission
    legacy local type => migration debt that may only shrink

Existing Agent Service vocabulary is grandfathered only as deletion debt. It is not evidence that those types belong in the architecture.

## Ratchet

planning/ordivon-core-zero-enforcement-r3.json snapshots the current top-level classes under agent_service/ as legacyTypeCeilings.agentServiceTopLevelClasses.

tests/test_ordivon_core_zero_enforcement_r3.py enforces:

1. architecturalCore == EMPTY;
2. accepted irreducible primitives remain empty;
3. residual candidates remain empty;
4. the observed legacy Agent Service top-level class set may shrink but may not grow silently;
5. any post-baseline type must be explicitly admitted as a non-authoritative adapter/client/error/projection/reader/verifier with a canonical external owner;
6. deletion gates remain behavioral rather than brand-based.

Deleting a legacy class does not require updating the ceiling. Later migration waves should tighten the ceiling after each accepted deletion batch.

## Why freeze the vocabulary first

The dominant risk is that migration work creates replacement-local concepts such as CanonicalTaskIdentity, UniversalCompletionRecord, or another Ordivon-owned policy/evidence/workflow object.

R3 changes the burden of proof:

    class exists locally
    does not imply
    class may continue to exist architecturally

and:

    new class
    requires
    named external owner + non-authority role

## External ownership baseline

The machine profile records canonical external references for A2A, Temporal, CMMN, SACM, OPA, OpenFGA, SPIFFE, CloudEvents, OpenTelemetry, W3C PROV, OpenLineage, SLSA, in-toto, and RFC 9562.

The profile does not claim these standards collectively form a new super-standard. Each keeps its native authority. Cross-system mapping stays adapter/profile data.

## Immediate consequence for Agent Service

The current top-level class population is now a debt ceiling.

Future work should prefer:

    existing custom type
    -> differential test
    -> external-native representation/adapter
    -> parity
    -> delete custom type
    -> tighten ceiling

not:

    existing custom type
    -> rename
    -> wrap in a new Ordivon abstraction

## Next destructive wave

R4 should target one narrow Agent Service family with a high-confidence external owner and low coupling. Recommended order:

1. capability/interface advertisements -> A2A Agent Card / MCP capabilities;
2. policy decision classes -> OPA decision adapter;
3. identity proof classes -> SPIFFE/OIDC adapter;
4. custom event envelope -> CloudEvents;
5. semantic session/task duplication -> A2A/CMMN/Temporal differential migration.

Each wave must add parity tests before deleting the corresponding legacy types, then tighten the R3 ceiling.

## Non-goals

R3 does not delete production classes yet.
R3 does not claim the external-first stack already passes all 15 deletion gates.
R3 does not turn the conformance profile into runtime authority.

Its function is narrower: prevent architectural regression while destructive migration proceeds.
