# Media v2 — external audio / loudness R3

## Objective

Replace the demonstrated legacy `measure_loudness()` / `validate_loudness()` path with direct external-tool evidence rather than another Media-owned DSP implementation.

## Composition

```text
exact audio artifact
  -> FFprobe stream facts
  -> FFmpeg loudnorm BS.1770-family measurement
  -> retained raw stderr + extracted tool JSON
  -> explicit audio/loudness profile assertions
  -> digest-bound EvidenceReceipt
```

The adapter does not implement a loudness algorithm. FFmpeg performs the measurement. Media v2 retains the raw tool evidence and applies only profile-owned acceptance thresholds.

## Truth boundary

A passing receipt establishes bounded technical stream facts and the measured loudness/true-peak relationship to the supplied profile. It does not establish listening quality, intelligibility, semantic quality, accessibility outcome, mastering suitability for every destination, or publication acceptance.

## Destructive acceptance

`media-v2/tests/audio-smoke.sh` requires all three conditions:

1. a 48 kHz mono PCM fixture around -23 LUFS passes;
2. an otherwise equivalent intentionally over-loud fixture fails `loudness.integratedLufs`;
3. the known-good fixture fails when evaluated under a deliberately stricter true-peak profile.

A measurement path that accepts all fixtures is a false green and fails R3.

## Real-production byte availability

`productions/runtime-introduction/assets.json` contains a historical narration declaration for SHA-256 `798c8f90f9eeb90d6407d78329e88e71dab6d4aa5d38831568c7e14f445d828d` with declared 48 kHz mono PCM and loudness facts. The exact WAV bytes were not present in the repository, workspace outputs, inspected cache roots, or visible archived-object paths during R3. Therefore those historical values are **not** reused as fresh measurement evidence. Real-production audio parity remains pending exact byte recovery/materialization.

## Legacy disposition after R3

For new Media v2 work, `ordivon_studio.qc.measure_loudness()` and `ordivon_studio.qc.validate_loudness()` are now **legacy compatibility only**. Their demonstrated semantics are covered by the external-first path. They are not yet physically deleted because the legacy `ordivon-studio qc-video` command and its old unit tests still reference them. New production paths must not add new references.
