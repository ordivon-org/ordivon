# Verification / Assurance / Formal Current-Truth Census R1

Date: 2026-09-24
Status: **CURRENT-TRUTH SYNTHESIS / REUSE EXISTING OWNERS / V07 TRACEABILITY GAP TARGETED**

## Result

Ordivon does not have one monolithic "formal verification system". It already has a composable assurance fabric whose parts retain different owners:

```text
claim / composition requirement
        -> Verification Obligation
        -> exact task-local verifier binding
        -> natural verifier
        -> owner-native evidence / attestation
        -> Composition Gate Result
        -> mechanical closure
        != domain acceptance
        != promotion/effect authority
```

The primary remaining formal-method gap is not the absence of a proof engine. It is the narrower relation between a checked formal abstraction and the production implementation that is claimed to realize that abstraction.

## Current LEGO map

| LEGO | Current owner / carrier | Standing | Boundary |
|---|---|---|---|
| V00 Claim / support scope | domain, Runtime RF11, task-local Circuit | PASS_DISTRIBUTED | no universal claim truth store |
| V01 Verification obligation | `packages/composition` | PASS | gate projection only |
| V02 Obligation compiler | `packages/composition` | PASS | deterministic projection; no execution |
| V03 Verifier binding | `packages/composition` | PASS | caller-authored exact task-local binding; no discovery/ranking |
| V04 Natural verifier providers | owner-native, Artifact, Security, Research, OPA, TLA+/TLC, Pacti shadow | PASS_PARTIAL_PORTFOLIO | each verifier keeps native semantics |
| V05 Physical evidence claim | Runtime + natural evidence owners | PARTIAL / owner-scoped | evidence is claim-relative; no global evidence DB |
| V06 Currentness / invalidation | Interface Contract + owner-specific checks | PARTIAL | broader invalidation remains pressure-gated |
| V07 Formal model ↔ implementation trace | Runtime | OPEN_TO_PARTIAL | TLC model check != Rust refinement proof |
| V08 Completion semantics | Runtime + Composition + domain owners | PASS_SEPARATED_PARTIAL | physical terminality != gate closure != domain acceptance |
| V09 Attestation / signer trust | Artifact/Security Sigstore/VSA/in-toto-style carriers | PASS_BOUNDED | authenticity/provenance != semantic truth |
| V10 Promotion / effect authority | Git/release/provider/domain authority | PASS_SEPARATED | verification never self-grants mutation authority |

## Existing formal providers

### TLA+/TLC

`services/runtime/formal/RuntimeDispatchR1.tla` models the narrow concurrent dispatch/recovery boundary. Current accepted finite-model evidence covers:

- durable admission before physical dispatch;
- at-most-once physical dispatch per Attempt;
- ambiguity requiring reconciliation;
- explicit retry as a new Attempt;
- terminal evidence belonging to a dispatched Attempt.

The model and its README explicitly refuse the claim that TLC success proves the Rust implementation.

### OPA/Rego

Security owns policy/consequence verification. A policy PASS remains a policy result, not provider consequence truth.

### Pacti

Pacti remains an optional shadow contract-algebra provider after exact-version dogfood. It is not promoted into a universal dependency.

### Artifact verifiers

Artifact profiles use mature format-native implementations and independent-reader/decoder agreement where appropriate. Dataset R1 is the canonical example: DuckDB + PyArrow, exact object contract, key integrity, and bounded non-claims.

### Future theorem provers

Lean/Coq/Isabelle remain workload-gated. No current theorem-grade obligation justifies installation as architecture substrate.

## V07 — exact residual gap

The repository already has two sides of the relation:

```text
FORMAL SIDE
RuntimeDispatchR1.tla
  AtMostOnceDispatchPerAttempt
  AmbiguityRequiresReconciliation

IMPLEMENTATION SIDE
planning/invariants-r1.json
  I05 JobAttemptSeparation
  I11 AmbiguityNoBlindRedispatch

registry/lifecycle.rs
  mark_dispatch_issued
  Accepted + exact row_version + committed bundle
  -> atomic state='starting' CAS
  -> DISPATCH_ISSUED / AT_MOST_ONCE_BOUNDARY_COMMITTED

engine/execution.rs
  ensure_attempt_dispatched
  Accepted -> dispatch
  Starting/Running/Stopping/Recovering -> reconcile

integration_tests.rs
  runtime_two_observers_do_not_race_dispatch_of_one_accepted_attempt
  runtime_ambiguous_dispatch_is_lost_without_automatic_redispatch
```

What was missing was a fail-closed machine-readable relation between these existing objects.

R1 therefore introduces only:

- `services/runtime/formal/RuntimeDispatchR1.trace-r1.json`;
- `services/runtime/scripts/verify_formal_trace.py`;
- a focused test for the trace gate.

The gate binds the exact formal module/config digests, named model invariant/transition, existing Runtime invariant IDs and proof refs, implementation symbols and exact semantic anchor fragments, and integration-test symbols.

## What the trace gate proves

Only:

```text
The checked formal artifact is the expected artifact
+
the named Runtime invariant bindings still exist
+
the named implementation/test seams still contain the required correspondence anchors
```

It does not prove semantic equivalence between Rust and TLA+.

This moves V07 from:

`OPEN_WITH_BOUNDED_MODEL_EVIDENCE`

toward:

`PARTIAL_EXPLICIT_TRACEABILITY_GATE`

while keeping stronger refinement proof explicitly open.

## Stronger refinement admission rule

A stronger mechanism is admitted only when a concrete claim requires more than traceability + model checking + owner-native tests. Candidate escalation order:

```text
explicit trace gate
-> property/reference-model tests
-> generated model/test correspondence
-> model-based testing / state-machine conformance
-> proof-oriented refinement tooling
```

Do not jump directly to a theorem prover merely because a formal model exists.

## Assurance laws retained

```text
Observation != Evidence != Proof != Truth authority
Digest identity != provenance != semantic truth
Verifier binding != verifier execution
Verifier execution != obligation discharge
Mechanical closure != domain acceptance
Formal model checking != implementation conformance
Attestation != correctness
PASS != promotion authority
```

## Remaining gaps after V07 R1

1. Stronger model-to-implementation refinement remains open if future claims require it.
2. Currentness/invalidation remains partially owner-specific; broaden only under measured stale-support/revalidation pressure.
3. V05 physical evidence-claim binding continues to converge with Runtime's execution/evidence architecture rather than creating a new evidence schema.
4. Cross-domain verifier coverage grows seam-by-seam; no universal verifier catalog is admitted.
