# Software release reference

## Bounded proven profile

`software-release-oci-image-r1`

- OCI Image Layout / OCI image manifest
- OCI Image Format 1.1 semantics
- linux/amd64, single manifest
- object contract binds final manifest identity, platform, entrypoint/rootfs/runtime/security facts
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven providers

- Skopeo — final OCI layout normalization/read-back
- Syft 1.50.0 — SBOM evidence
- Trivy — vulnerability/secret evidence
- Podman — network-disabled runtime read-back acceptance
- in-toto/SLSA/Sigstore/OPA — generic trust/policy substrate when release requirements call for it

## Boundary

This profile validates a software release artifact; it does not build the software or replace Software Engineering. Structurally valid OCI bytes are insufficient for security/runtime contract acceptance.

## Source evidence

`/root/projects/ordivon/capabilities/artifact/docs/ARTIFACT_FAMILY_SOFTWARE_RELEASE_R1.md`
