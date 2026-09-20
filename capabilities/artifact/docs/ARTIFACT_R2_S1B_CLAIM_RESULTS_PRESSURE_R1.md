# Artifact R2-S1B — Explicit claimResults Adapter Pressure Test R1

## Standing

R2_S1B_PRESSURE_TEST_COMPLETE_SELECTIVE_NATIVE_EXPANSION_REQUIRED

This slice asks one narrow question:

Can current verifier outputs be adapted to the candidate VerifierPlugin claimResults contract without rerunning verification, parsing failure prose, or duplicating profile semantics?

## Result

Not universally.

### Legacy verify-stage

Standing: ADAPTER_SUFFICIENT.

The compatibility adapter can enumerate the canonical profile requiredEvidence key set, map each emitted gate receipt directly, and mark absent gates NOT_EVALUATED.

This preserves the existing distinction between stage PASS and profileVerificationComplete.

### WAVE

Standing: NATIVE_RESULT_EXPANSION_REQUIRED.

Safe current mappings:

- referenceContainerView;
- independentTechnicalView;
- decoderMatrix;
- pcmIdentity.

Gap:

- contractSchema.

The verifier validates the contract before downstream work, but the successful native result does not expose a distinct contractSchema status object. Inferring PASS from aggregate success or control flow would make the adapter depend on hidden implementation semantics.

### PNG

Standing: NATIVE_RESULT_EXPANSION_REQUIRED.

Safe current mappings:

- datastreamValidity from the explicit pngcheck return code;
- metadataObservation from metadata.status;
- decoderMatrix from decoderMatrix.status.

Gap:

- profileFacts.

The profile-fact decision is currently distributed across decoded image facts, PNG chunks and aggregate failures. Re-evaluating those conditions in an adapter would duplicate verifier policy and create a second semantic authority.

## Candidate contract rule

A conforming VerifierPlugin result must expose claimResults whose key set exactly equals the selected profile requiredEvidence key set.

Every key must have one explicit status:

- PASS;
- FAIL;
- NOT_EVALUATED.

Aggregate native verifier status is not a substitute for missing claim results.

The native verifier result remains present and digest-bound for backward compatibility and family-specific detail.

## Next slice

R2-S1C will make the minimum non-breaking native-output changes:

- WAVE emits explicit contractSchema plus all existing required claim results under claimResults;
- PNG emits explicit datastreamValidity, metadataObservation, decoderMatrix and profileFacts under claimResults.

Existing fields, CLI behavior, service routing, profile standing and current consumers remain unchanged.

Only after compatibility tests prove that additive output is safe should the candidate VerifierPlugin envelope be considered for production routing.
