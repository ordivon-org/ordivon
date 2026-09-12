# Distribution v2 R7 — Artifact release-standing handoff

R7 binds Artifact release standing into Distribution occurrence identity rather than trusting an upstream helper to enforce publication eligibility.

For Artifact-backed intents, the occurrence now binds:

- exact Artifact SHA-256;
- `releaseReady`;
- `trustStanding`;
- `sourceRef`;
- exact effect payload/provider/account/effect identity already present in R6.

Non-Artifact intents preserve their R6 occurrence projection and therefore preserve existing approval/effect identities.

Effectful publication of an Artifact with `releaseReady != true` returns `artifact_release_not_ready` with `externalEffectPerformed=false`. This gate is independent of exact-effect user authority: a non-release Artifact is not publishable even if a caller constructs or supplies an EffectAuthority object.

A `releaseReady=true` Artifact does **not** imply publication authority. It still requires the same R6 exact EffectAuthority and current provider observation.

`scripts/artifact_handoff.py` accepts an Artifact package index, verifies its primary relative path and primary bytes against `primary.digest.sha256`, and produces a provider-neutral Distribution intent. It does not call a provider and cannot create an EffectAuthority.

## Real negative acceptance

The post-retirement Artifact workflow `artifact-v2-source-authority-smoke-20260912-03` produced a package with:

- primary SHA-256 `2e5970e05bc8b823e9ca2f4fcaa2fa97de43b619c896c85afde92058fae0c9e9`;
- `trustStanding=LOCAL_UNSIGNED_DEVELOPMENT`;
- `releaseReady=false`.

R7 bound that real package into `evidence/r7-artifact-development-publication-intent.json`, performed only provider-native GitHub read observations, and evaluated the envelope to:

- action: `artifact_release_not_ready`;
- reason: `artifact-backed-effect-requires-release-ready-artifact`;
- `externalEffectPerformed=false`.

No GitHub write was performed.
