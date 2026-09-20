# Signed VSA verification

Security v2 uses Cosign/Sigstore for the cryptographic envelope rather than implementing signature primitives.

The verification contract has two independent layers:

1. `cosign verify-blob-attestation` verifies the DSSE signature against a preconfigured public key or, in production, an equivalent KMS/keyless Sigstore trust root;
2. `verify_vsa_bundle.py` decodes the *signed* DSSE payload and fails closed unless its VSA semantics match the expected subject Git commit, predicate type, verifier identity, verified level, `PASSED` result, and a trust-policy mapping from verifier ID to the exact public-key SHA-256.

When an expected unsigned Statement is supplied, the signed DSSE payload must be byte-identical to it.

A repository-local ephemeral key is suitable only for integration testing. Production signing authority must be externalized to KMS/HSM or a keyless Fulcio/OIDC identity. The private key must never be committed to this repository.

## R2 integration evidence — 2026-09-12

A local pinned-public-key integration run using Cosign v3.1.0 completed both layers successfully:

- Cosign DSSE verification: `Verified OK`;
- Security v2 semantic VSA verification: `PASSED`;
- subject Git commit: `5e3142b92fc5aed3259295b63c0300f01b45e04a`;
- verifier implementation revision: `558eda72479d0531c9be1e5d8fded4eb96bfef93`;
- required level: `SECURITY_PRODUCT_POLICY`.

Retained test public-key SHA-256:

`sha256:426a1044bec0857fc2286638fd95995bddfdb075ab2cbd42d9affa61c5b6d75a`

Sigstore bundle SHA-256:

`sha256:719dd115d59168d30c5b021dc1546f82c808fb560e4d2fa22d2e4ec5c4e9c31f`

Signed VSA Statement SHA-256:

`sha256:dc313924cfb94d78e1a08c24b663a7c9cc48079f9d7a7480e60bd80378396cea`

The ephemeral private key used for this integration proof was deleted after signing. This proves the local pinned-key path, not production KMS/Fulcio identity readiness.
