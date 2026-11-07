# Security v2 attestation model

Security v2 does not promote its local runner status JSON into a new security evidence standard.

The external evidence chain is represented using existing attestation standards:

1. provider-native evidence remains unchanged (`SARIF`, `CycloneDX JSON`, OSV JSON);
2. each retained provider artifact is referenced by an in-toto Statement v1 using the Reference predicate;
3. the final policy result is emitted as a SLSA Verification Summary Attestation (VSA) predicate inside an in-toto Statement v1;
4. the subject uses in-toto's `gitCommit` digest type;
5. the VSA binds the verifier revision, named profile, exact policy digest, and all retained input reference-attestation digests.

`verifiedLevels` uses the custom value `SECURITY_PRODUCT_POLICY` for a passed Security policy result. This is deliberately **not** a claim that the subject satisfies a SLSA Build or Source level. Failed policy results use `FAILED`.

## Current trust boundary (2026-11-07 source audit)

The original R1 emitter produces unsigned in-toto Statements. An unsigned Statement remains a content claim only; it does not authenticate a producer or a verifier. The subsequent Signed-VSA R2 integration uses mature Cosign/Sigstore for the DSSE cryptographic envelope and Security's verify_vsa_bundle.py for exact VSA semantic binding. See docs/SIGNED-VSA.md for the tested local pinned-key profile. That integration is **not** evidence of production KMS/keyless identity admission.

Build provenance is distinct from a Security VSA. The legacy standalone Python wheel producer was retired because its Python 3.12 claim and repository layout no longer matched this owner. Build owners should issue signed provenance with their native provider (for example GitHub actions/attest); verify signature and issuer with gh attestation verify before interpreting Security's content-only PROVENANCE_CONTENT_BOUND output. Neither parsing unsigned provenance nor a historical local example qualifies a production release.
