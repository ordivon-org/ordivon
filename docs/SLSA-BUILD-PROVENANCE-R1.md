# SLSA Build Provenance R1

Date: 2026-09-12
Initial standing: implementation ready; physical build acceptance must run from a committed clean revision.

Security v2 now distinguishes two standard attestations:

- **Build Provenance** (`https://slsa.dev/provenance/v1`): produced by the actual build process and describing the artifact, exact source revision, build definition, builder and invocation metadata.
- **Verification Summary Attestation**: produced later by Security after verifying evidence/policy.

They are not interchangeable. Security must not reconstruct Build Provenance after the build from incomplete logs.

The R1 local builder is deliberately limited to a SLSA Build L1 acceptance. It builds an exact `git archive HEAD` using uv, emits provenance inside the same builder invocation, and supports independent artifact/source/builder/build-type verification. It makes no hosted-builder, signed-provenance, or hardened-build claim.
