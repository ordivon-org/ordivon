# Audio: bounded native-format verification

## Choose the exact profile, not a generic “audio PASS”

Artifact currently has separate standards-first audio profiles for native FLAC, RIFF/WAVE PCM and Ogg/Vorbis. Each has its own exact binding, object contract and native verifier:

| Profile | Existing entrypoint | Essential evidence |
| --- | --- | --- |
| `audio-flac-pcm16-r1` | `scripts/artifact_audio.py` | Full-stream reference FLAC test; STREAMINFO and metadata policy; FFprobe technical view; FLAC/FFmpeg canonical PCM and MD5 identity |
| `audio-wave-pcm16-r1` | `scripts/artifact_wave.py` | libsndfile/FFprobe/SoX technical views, FFmpeg/SoX canonical PCM comparison and exact object contract |
| `audio-ogg-vorbis-r1` | `scripts/artifact_ogg_vorbis.py` | Format-specific Ogg/Vorbis checks; inspect the selected contract and native result rather than extrapolating FLAC/WAVE claims |

Prior source note: `capabilities/artifact/docs/ARTIFACT_FAMILY_AUDIO_R1.md`. It is historical source-bound evidence, not proof of current executable/provider availability. Actual routing and required claims live in `capabilities/artifact/artifact-delivery/shadow-v2/examples/` and `capability-bindings-v1.json`, followed by a current tool probe.

## Human: state the real output requirement

1. Name the audio file's role and consumer (game sound, archive, music, podcast, etc.). Choose an exact technical profile, not generic “audio”.
2. Supply the native file and its object contract. For FLAC this covers sample rate, channels, 16-bit sample depth, total samples and optional decoded PCM SHA-256.
3. Use the existing `scripts/artifact_verify.py` entrypoint with a request satisfying `artifact-delivery/verification/request-v1.schema.json`. It binds exact profile, subject and optional object-contract SHA-256; it is **not** a transfer operation.
4. Inspect `service-result.json`, native `verification.json` and raw evidence. Validate the actual consumer separately: technical PASS does not establish mastering quality, licensing, artistic meaning or game suitability.

## Agent: preserve bounded evidence

1. Discover a live verifier and current capability binding on the actual node; previous “live proven” records and this Skill are not current installation proof.
2. Delegate to native FLAC, FFmpeg, libsndfile and format-specific validators; do not implement a generic audio parser.
3. Bind exact subject/Profile/object-contract bytes and their digests before invocation. Distinguish input absence, invalid contract, missing provider and evaluated checks.
4. For FLAC, read native `claimResults` keys that correspond one-to-one to required Profile evidence: `contractSchema`, `referenceIntegrity`, `metadataBlockPolicy`, `streamInfo`, `independentTechnicalView`, `decoderMatrix`, `pcmIdentity`. Every claim is `PASS`, `FAIL` or `NOT_EVALUATED`; an overall verifier PASS must never invent missing claim results.
5. Deliver the exact receipt and non-claims to the consuming Owner; consumer-domain acceptance, transport and publication belong to their actual owners.

## Verification

From `capabilities/artifact/` use `mise run verify` for locked dependencies, Ruff and non-integration Owner tests. It does not establish current native-target installation, cross-Owner acceptance or production deployment.
