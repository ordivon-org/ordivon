# Artifact Profile authority and bounded v1鈫抳2 refinement R1

## First-principles contract

A subject hash does not prove which Profile was authoritative. A Profile
registration may not silently drop malformed, schema-invalid, ambiguous or
drifted authority files, or return cached semantics paired with a newly
computed digest of different file bytes.

Read the source document **once** for its parsed JSON and SHA-256. Reject
duplicate names at all JSON nesting levels. Retain the indexed digest, and
fail closed at resolution if the source content has changed. Publicly
returned Profile data is an independent copy, not the mutable registry index.

The canonical v2 directory contains only Profile files. All must parse,
have version 2, correct identity/filename and pass existing JSON Schema
Draft 2020-12. The production v1 examples directory is mixed: all files
must parse strictly, while known request/source documents outside Profile
authority are excluded; a candidate with an ID, artifactClass, primaryOutput
or profileVersion must pass the v1 Schema. Historic `$schema` annotation
is stripped from the *validation instance only*, never from source bytes.

## Precisely scoped refinement

For v1 source `s` and its canonical v2 interpretation `v`, require that
`R(s,v)` preserves: (1) ID and known family crosswalk; (2) construction
authority mode and locale; (3) ordered primary/companion output role,
format name, purpose, required and editable; (4) primary renderer identity
and required flag.

At resolve, the obligation is `indexed source digests still match AND R(s,v)`.
Every one of the eight existing v1 Profiles has a canonical counterpart.

No equivalence is asserted for v1 verification gates vs v2 requiredEvidence,
unmapped policy, actual renderer behavior, provider installation, external
decoders, consumer acceptance, or production v2 cutover. Existing historical
mapping manifests are not alternative source authority.

## Evidence and falsification

- Real source: 28 v2 Schema-valid Profiles, 8 v1 Schema-valid production
  Profiles; 8 current v1/v2 bounded refinements pass.
- `artifact_verification/formal/verify_profile_refinement.py`: 8 real Profiles
  脳 128 Boolean agreement-state combinations = 1,024 abstract model states,
  independently checked against the intended common-field refinement oracle.
- `tests/test_artifact_profile_authority.py`: invalid JSON, nested duplicate
  keys, wrong schema/version/name, source drift, wrong projection, and caller
  mutation cannot be promoted into valid authority.
- `tests/test_artifact_binding_authority.py`: ambiguous provider standing,
  duplicates and stale Build/Verify registry identity must fail closed.
- `tests/test_artifact_consumer_acceptance.py` remains the real native
  producer 鈫?verifier 鈫?independent consumer readback path.
- Both `mise run verify` and `mise run queue` run the model and native tests.
  The standard non-integration scope does not prove live deployed services.

This is bounded executable refinement, not a proof about arbitrary JSON,
historical source maps, outside-the-process writes or installed consumers.

## Human versus Agent instructions

**Human:** bind the intended target consumer and exact Profile/contract
bytes; treat v2 as an interpretation until stronger cutover evidence exists.
Do not confuse verified source authority with acceptance by PowerPoint,
FFmpeg, a game engine or a production deployment.

**Agent:** malformed/ambiguous or changed authority is a verification
failure, never an optional missing capability. On `changed after indexing`,
recreate the registry at a fresh SourceCut rather than recomputing the digest
for a stale cached object. Preserve UNKNOWN for unmapped policy semantics.
