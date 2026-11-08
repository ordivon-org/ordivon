# Consumer acceptance: exact output, independent readback and scoped standing

## Purpose

Artifact verification and consumer acceptance are **different statements**. This guidance applies to common native artifacts such as a game audio clip, still-image asset, FLAC interchange file, and a Parquet dataset. It is not a new verifier or registry and does not transfer a consumer's authority to Artifact.

## Human guide

1. **Name an actual consumer and a usable outcome.** For example: WAVE in a game/audio reader, FLAC in a media decoder, PNG in an image-display application, or Parquet in a research/analytics query.
2. **Declare exact technical requirements.** Choose a canonical Profile from `artifact-delivery/shadow-v2/examples/` and, when required, an object contract. Constrain sample count/PCM identity, pixel interpretation, or dataset column/key semantics as appropriate.
3. **Produce one native file with a mature writer.** Do not settle for a JSON request or verification result that represents a file which was never created.
4. **Run the Artifact verification service against the actual bytes.** The existing `scripts/artifact_verify.py` reads the request defined by `artifact-delivery/verification/request-v1.schema.json`. Its service result includes `requiredEvidenceAssessment` and `profileVerificationComplete`.
5. **Have the consumer read the actual file.** Compare its observed facts with the intended acceptance predicate. Domain-specific acceptance (sound design, gameplay, scientific validity, text accuracy, distribution) is never implied by a technical readback.
6. **Record the result.** Keep subject hash, selected profile and contract hash, native verifier output, claim assessment, consumer-observed values, missing tests and non-claims. A green test of a source Workspace is not proof of production deployment.

## Agent execution rule

- Source owner: `capabilities/artifact/`, with exact profile/Capability Binding and native tool identities.
- Execution owner: the current Runtime/Harness Job mechanism; never replace an in-progress Job with an invented terminal state.
- Consumer owner: Game, Media, Research, Finance or the real target application. Use its own readback/acceptance mechanism. Merely putting a consumer ID in the Artifact request **does not execute the consumer**.
- Read `inputIdentity` before promoting native evidence. For self-contained
  FLAC/WAVE/PNG the verifier reads a digest-bound private snapshot. The canonical
  Profile is also snapshot-bound. Legacy sidecar-bearing formats still report
  `ADMISSION_DIGEST_ONLY`; do not infer stronger identity. Temporary native paths
  such as `verification.artifact.path` do **not** survive a service invocation.
  Independently hash the actual bytes opened by the target consumer.
- Evidence must preserve three independent boundaries:
  1. **Byte identity** — the exact subject and contract that were validated
  2. **Profile claims** — every required native claim that is actually supported and complete
  3. **Consumer acceptance** — separately executed target readback with observed values
- Missing profile `claimResults` are `NOT_EVALUATED`, **not** a second kind of PASS. In the current explicit claim rollout, the FLAC, WAVE and PNG capability bindings require complete claims. Legacy native formats remain verifiable under their existing route, but `profileVerificationComplete=false` until their adapter is qualified.
- A format-level PASS cannot certify real-world/audio meaning, text correctness, accessible presentation, data provenance, or production readiness. Negative cases should test bad digests, incomplete claim sets and native/claim status mismatches.

## Native evidence example

In the Artifact Owner working tree, run:

```bash
mise run verify
# To exercise common real producer -> verifier -> native consumer readback:
uv run python -m pytest -q tests/test_artifact_consumer_acceptance.py
```

The test file creates *temporary* WAV, FLAC, PNG and Parquet bytes with existing native/third-party writers, calls the real Artifact service, and performs separate consumer reads. Missing tools are reported as skips. Tests do not mutate external user assets or write into another Owner's directories.

## Mature primitives to reuse

- **Native representations:** RIFF/WAVE PCM, IETF RFC 9639 FLAC, W3C PNG, Apache Parquet.
- **Producer/validation:** reference FLAC, FFmpeg, libsndfile/SoX, ImageMagick/libvips/pngcheck, PyArrow/DuckDB.
- **Verification reporting:** in-toto Attestation Statement/Predicate/Envelope and the Simple Verification Result predicate can be considered when authenticated cross-system evidence is genuinely needed. Do not wrap all local tests in a new attestation format or confuse signing with the truth of a claim.
- **Identity and distribution:** OCI/ORAS when a real consumer needs registry distribution, not as an obligation of file validation.

Relevant source paths: `artifact_verification/claim_coverage.py`, `scripts/artifact_verify.py`, `artifact-delivery/capability-bindings-v1.json`.
