# Artifact R2-S1 — Evaluation / Evidence / Standing Pressure Test R1

## Standing

R2_S1_PRESSURE_TEST_COMPLETE_EXPLICIT_CLAIM_RESULTS_REQUIRED

This slice does not change production routing.

It pressure-tests whether the redecomposed Artifact Standing Kernel can represent both the production-v1 verification lineage and the standards-first verifier-plugin lineage without semantic loss.

## Result

Three parts of the hypothesis survived:

1. EvaluationRequest can be common.
2. EvidenceObservation can be common as a typed envelope around untouched native evidence.
3. StandingDecision can be common only when verifier plugins explicitly report claimResults keyed by the exact profile requiredEvidence vocabulary.

The fourth shortcut was rejected:

Native verifier aggregate PASS is not sufficient authority for profile PASS.

## Lossless EvidenceObservation

The prototype at planning/prototypes/evidence_observation_r1.py wraps two current result families:

- artifact-delivery-verify-stage;
- artifact-verification-result.

The common envelope indexes:

- exact subject reference;
- exact profile reference;
- capability/adaptor reference;
- observation identity/kind/status;
- evidence references;
- method reference;
- standing projection axes;
- non-claims.

Verifier-native evidence remains opaque and is preserved rather than rewritten into a universal Artifact AST.

The prototype canonical-digest round-trips both result families exactly.

It also fails closed when:

- common status projection drifts from native evidence;
- subject projection drifts;
- native evidence changes without a matching source-result digest.

Pressure cases cover:

- legacy verify-stage PASS with incomplete required evidence;
- legacy verify-stage PASS with complete selected gates;
- family verification service PASS;
- family verification service FAIL.

## Standing is a vector, not one scalar

R2-S1 retains these separate axes:

- verificationStatus;
- profileAuthority;
- evidenceCompleteness;
- trustStatus;
- releaseStatus.

Consumer-domain acceptance and human preference remain outside the Artifact kernel.

A legacy verify-stage status PASS with pending required gates becomes:

- verificationStatus: PENDING;
- evidenceCompleteness: PARTIAL.

It is not promoted to profile PASS.

## Required-evidence addressability gap

Across the 19 currently bound verify profiles:

- 102 profile requiredEvidence keys exist;
- 10 have same-name keys in standing.bindings;
- 9 have same-name keys in standing.proof;
- 69 appear as same-name string literals in verifier source;
- 0/19 profiles have complete standing.bindings key coverage;
- 0/19 profiles have complete verifier-source literal coverage.

This means there is no current universal claim-mapping registry.

Example: audio-wave-pcm16-r1 has explicit native result objects for referenceContainerView, independentTechnicalView, decoderMatrix and pcmIdentity, but the profile also requires contractSchema. The native verifier can return aggregate PASS without exposing a distinct contractSchema result object.

The fail-closed StandingDecision prototype therefore returns PENDING/PARTIAL rather than laundering aggregate PASS into profile PASS.

## Candidate VerifierPlugin result contract

planning/verifier-plugin-result-r2-candidate.schema.json defines the planning-only envelope.

The central semantic rule is stronger than JSON Schema alone:

claimResults keys must exactly equal the selected profile requiredEvidence keys.

Each claim result has:

- status: PASS / FAIL / NOT_EVALUATED;
- observationIds;
- evidenceRefs;
- nativePointers;
- nonClaims.

The plugin retains its untouched nativeResult and binds it by canonical SHA-256.

There is deliberately no plugin-authoritative overall profile status.

StandingDecision derives the profile-level verification status from claimResults plus profile policy.

## Why exact key equality

Exact equality prevents three failure classes:

1. missing required evidence silently disappearing;
2. plugin-specific aliases being guessed by a generic engine;
3. extra verifier facts accidentally becoming profile claims.

A plugin may retain arbitrary additional facts inside nativeResult. They do not become Artifact claims unless the profile declares them.

## Next slice

R2-S1B:

Pressure-test explicit claimResults adapters for:

- WAVE;
- PNG;
- legacy verify-stage compatibility.

The goal is not to modify current family verifier outputs yet.

The goal is to prove that explicit adapters can map every profile requiredEvidence key without re-running verification, parsing failure prose, or weakening current boundaries.

If an adapter cannot do that from the native result, the native verifier output contract must be expanded before production adoption.
