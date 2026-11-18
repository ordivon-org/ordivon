# Artifact claim coverage — specification, finite model, implementation bridge

**Authority:** the current Artifact Profile files and production code. This document is a method/evidence explanation, **not** a second status registry or claim that all profiles are formally proved.

## Consumer and unacceptable outcome

The verification service is consumed by Agent-driven native output review. **Safety property:** a native verifier's overall `PASS` must never be promoted into a **complete profile evidence** conclusion if a required claim is missing, unknown, failed, has no native evidence, or only cites its own claim record.

That is distinct from the native artifact's actual validity, data origin, legal semantics, target runtime usability or installed provider availability.

## Specification (R2.1 semantic obligation, not a newly registered LEGO)

- **Inputs:** canonical selected Profile `P`, native verification observation `N`, native aggregate status `S`, binding's `requireClaimResults` flag `B`.
- **Required set:** `R = keys(P.requiredEvidence)`, non-empty.
- **Supported claim:** `Supported(r, N) := r ∈ keys(N.claimResults) ∧ status(r)=PASS ∧ ∃ptr ∈ nativePointers(r): ptr is a non-self-referential pointer to a native node with status PASS`.
- **Coverage:** `C(P,N) := R ≠ ∅ ∧ keys(N.claimResults)=R ∧ ∀r∈R Supported(r,N)`.
- **Strict service admission:** `ServicePass(P,N,S,B) := S=PASS ∧ (¬B ∨ C(P,N))`.
- **Complete profile observation:** `ProfileVerificationComplete(P,N,S,B) := S=PASS ∧ C(P,N)`.
- **Effects:** the coverage evaluator is pure; the service writes evidence only after validating request/subject/contract digests and executing the chosen provider.
- **Non-claims:** `C` alone does not establish correctness of an external decoder, target consumer or format semantics, nor does a finite model prove arbitrary Python JSON pointer handling.

## Model and source refinement

The existing executable pure evaluator is `artifact_verification/claim_coverage.py`. Its bounded executable model checker is `artifact_verification/formal/verify_claim_coverage.py`. Each of the real FLAC, WAVE and PNG Profile claim sets is checked against a separately encoded specification oracle for the full Cartesian product of six representative states **per required claim**:

1. Missing claim
2. Explicit `NOT_EVALUATED`
3. Native `FAIL` with matching witness
4. Native `PASS` with a matching independent witness
5. False `PASS` using self-referential `/claimResults/…` as witness
6. False `PASS` with mismatching native witness

This is exhaustive **within that explicitly finite abstraction** (7, 5, 4 required claims); it binds exact current Python implementation and current Profile file bytes. It additionally checks zero/absent evidence, unexpected extra claims and non-vacuity (exactly one all-PASS state is accepted per Profile).

The proof does **not** cover arbitrary nested JSON shapes, concurrency, file-system races, integrity of external tools, or the veracity of a native validator's claims. Those require separate source/effect and real-consumer evidence.

## Input identity and executable refinement obligation

A pathname is not a content identity. The previous `hash(path)` followed by
`verifier(path)` had a TOCTOU gap. For qualified self-contained formats,
`artifact_core/input_snapshot.py` copies and hashes bytes from **one open
descriptor**, checks the request digest, and delegates the same private file.

Precondition: regular readable file, expected SHA-256, private scratch root.
Postcondition: if staging succeeds, SHA-256 of the snapshot's streamed bytes
equals the request digest; native verifier receives that snapshot rather than
the mutable original pathname.

The claim depends on SHA-256 and normal OS descriptor/read/write semantics.
It excludes malicious same-principal modifications of private scratch,
all concurrent external sidecars, later source-path identity, and actual
consumer-domain acceptance. The native tests cover digest mismatch, source
replacement, symlink/FIFO inputs, and service delegation after a pathname
mutation. Unlike the finite abstract claim proof, this is an effectful
property supported by real execution rather than a universal theorem.

## Native result identity: a second, independent proof obligation

Passing an exact-byte admission check does not imply that a native verification
result belongs to the admitted object. The service additionally checks the native
report's Profile ID, subject SHA-256, byte length and object-contract SHA-256.

Let `Mismatch(E,N)` mean a reported identity field disagrees with admitted
input E; `Unknown(E,N)` means an expected native field is missing.

- Strict/claim-complete binding: `NativeIdentityAccept := not Mismatch and not Unknown`.
- Legacy binding: `NativeIdentityAccept := not Mismatch`; missing facts
  stay `NOT_EVALUATED`, not complete evidence.
- Service `PASS` requires the native verifier's `PASS` and both the applicable
  claim/identity admission predicates. `profileVerificationComplete` additionally
  requires complete native identity agreement, including on legacy bindings.
- A different Profile, subject digest, byte count or contract digest cannot
  be promoted even when all other native claims are `PASS`.
- Native provider exceptions and non-object reports produce a bounded service
  failure rather than an exception escaping as implicit success.

The pure evaluator is `artifact_verification/native_identity.py`, with
`artifact_verification/formal/verify_native_identity.py` checking 216 finite
Cartesian states for strict/legacy, with/without contract, exact/unknown/mismatch
field categories. This is **not** an unrestricted theorem about all JSON,
provider honesty, filesystem effects, codec implementation or domain consumers.
`tests/test_artifact_native_identity.py` checks real service composition and
explicit counterexamples; the earlier `claimResults` finite model is independent.

## Execution and evidence

`mise run verify` and the existing GitHub queue task invoke the model/refinement checker **before** running the necessary native tests. Its output reports the exact source/profile SHA-256 commitments, bounded state counts, accepted states and counterexample count.

`tests/test_artifact_consumer_acceptance.py` retains independent executable service/consumer checks on actual WAV, FLAC, PNG and Parquet bytes and input-admission negative cases. Four redundant pure-function example tests are deliberately retired because exhaustive finite abstraction now covers those represented cases. Other native provider and integration checks remain because no implementation refinement evidence for their physical effects has been proved.

A production evidence receipt must separately confirm: current source revision, checked model/proof receipt, source-to-model coverage limit, native test exit, real consumer result, GitHub branch/CI/merge state, and installed node acceptance. Never infer one from another.

## Human versus Agent use

- **Human:** name the required real consumer and unacceptable false-positive. Read `profileVerificationComplete` as evidence sufficiency under explicit claims, **not** universal correctness. Demand actual playback/readback and domain acceptance separately.
- **Agent:** resolve current Profile/binding, preserve Profile SHA-256, invoke current verifier, reject self-referential witness pointers, apply `ServicePass`, run the model checker only after changing the evaluator, record checker/source hashes, and then independently read actual native bytes in a target consumer. Do not turn `UNKNOWN` into false or true by fallback.
- **Deletion:** remove a traditional test only when the current proof covers its exact property **and** implementation refinement is checked. Retain consumer-IO, tool-version, deployment and model-gap tests; do not delete on count targets.

## Upstream mature method precedents

- Design by Contract / Hoare-style specifications: explicit preconditions and postconditions.
- Finite-state model checking (TLA+/TLC, Quint) for owner lifecycle machines. This specific **pure function** needs finite state refinement rather than another state-machine infrastructure.
- Z3 or CrossHair can expand coverage over more complex pure predicates when the environment and semantics justify it. They are not automatically sound for file/network effects.
- in-toto attestation may package this proof result when a real external consumer requires authenticated evidence; do not create an Artifact-specific attestation standard.
