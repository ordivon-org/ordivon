# Distribution v2 R7 — Artifact release-standing handoff

R7 established a still-current Distribution rule: Artifact-backed effects bind the exact Artifact identity and Artifact-owned release standing into Distribution occurrence identity instead of letting a caller assert publication eligibility.

For Artifact-backed intents, the occurrence binds:

- exact Artifact SHA-256;
- `releaseReady`;
- `trustStanding`;
- `sourceRef`;
- exact effect payload/provider/account/effect identity already present in R6.

Non-Artifact intents preserve their prior occurrence projection.

Effectful publication of an Artifact with `releaseReady != true` returns `artifact_release_not_ready` with `externalEffectPerformed=false`. This gate is independent of exact-effect user authority: a non-release Artifact is not publishable merely because effect authority exists.

A `releaseReady=true` Artifact does **not** imply publication authority. Distribution still requires the same exact EffectAuthority and current provider observation.

## Retired migration adapter

The original R7 implementation included `scripts/artifact_handoff.py`, which consumed Artifact's then-current custom `package-index.json` relationship format. Artifact subsequently retired `package-index.json` and `release-manifest.json` in favor of standards-based OCI 1.1 descriptors/referrers plus the common in-toto/SLSA/Sigstore release envelope.

The executable R7 package-index adapter and its forward regression test are therefore retired in R10. They are not a compatibility surface and must not be revived to connect current Artifact and Distribution.

Historical R7 evidence remains valid evidence about the old migration cut: it demonstrated that release standing was bound into Distribution admission and that an unreleased Artifact was blocked before provider write. It is not evidence that the retired package-index representation remains current.

## Forward boundary

Current Artifact → Distribution integration must consume Artifact's current standards-based release identity/evidence or a thin projection derived from that authoritative representation. Distribution may bind the facts it needs (`sha256`, `releaseReady`, `trustStanding`, `sourceRef`) but must not recreate Artifact packaging, SBOM, SLSA/in-toto provenance, Sigstore verification, vulnerability/secret evidence, or a second package relationship tree.

R10 local software-store preflight is deliberately independent of this release-trust handoff. It can prove local packaging/install/update/rollback mechanics while reporting Artifact release evidence as unbound; it cannot mint `releaseReady` itself.

## Historical negative acceptance

The 2026-09-12 R7 migration evidence recorded a development Artifact with `trustStanding=LOCAL_UNSIGNED_DEVELOPMENT` and `releaseReady=false`; Distribution evaluated the attempted effect as `artifact_release_not_ready` with `externalEffectPerformed=false`. No GitHub write was performed.
