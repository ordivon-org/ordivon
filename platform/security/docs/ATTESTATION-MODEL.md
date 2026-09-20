# Security v2 attestation model

Security v2 does not promote its local runner status JSON into a new security evidence standard.

The external evidence chain is represented using existing attestation standards:

1. provider-native evidence remains unchanged (`SARIF`, `CycloneDX JSON`, OSV JSON);
2. each retained provider artifact is referenced by an in-toto Statement v1 using the Reference predicate;
3. the final policy result is emitted as a SLSA Verification Summary Attestation (VSA) predicate inside an in-toto Statement v1;
4. the subject uses in-toto's `gitCommit` digest type;
5. the VSA binds the verifier revision, named profile, exact policy digest, and all retained input reference-attestation digests.

`verifiedLevels` uses the custom value `SECURITY_PRODUCT_POLICY` for a passed Security policy result. This is deliberately **not** a claim that the subject satisfies a SLSA Build or Source level. Failed policy results use `FAILED`.

## Current trust boundary

The current R1 emitter produces unsigned in-toto Statements. They provide exact structural/provenance binding but **do not yet authenticate the verifier identity**. A later release/admission step must use a standard signing/envelope mechanism (for example DSSE/Sigstore) before these Statements can serve as independently authenticated external attestations.
