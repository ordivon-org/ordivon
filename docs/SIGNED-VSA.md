# Signed VSA verification

Security v2 uses Cosign/Sigstore for the cryptographic envelope rather than implementing signature primitives.

The verification contract has two independent layers:

1. `cosign verify-blob-attestation` verifies the DSSE signature against a preconfigured public key or, in production, an equivalent KMS/keyless Sigstore trust root;
2. `verify_vsa_bundle.py` decodes the *signed* DSSE payload and fails closed unless its VSA semantics match the expected subject Git commit, predicate type, verifier identity, verified level, `PASSED` result, and a trust-policy mapping from verifier ID to the exact public-key SHA-256.

When an expected unsigned Statement is supplied, the signed DSSE payload must be byte-identical to it.

A repository-local ephemeral key is suitable only for integration testing. Production signing authority must be externalized to KMS/HSM or a keyless Fulcio/OIDC identity. The private key must never be committed to this repository.
