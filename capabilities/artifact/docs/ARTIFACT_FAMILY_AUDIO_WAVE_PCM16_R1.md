# Artifact E2E — Audio / RIFF-WAVE PCM16 R1

## Standing

`SHADOW_PROFILE_LOCAL_LIVE_PROVEN`

R1 covers one bounded WAVE case needed by real Game workloads: Microsoft RIFF/WAVE carrying `WAVE_FORMAT_PCM` (`0x0001`) with 16-bit signed PCM and one or two channels. IANA's historic WAVE registry associates codec `1` with Microsoft PCM. The profile does not reinterpret BWF/EBU metadata merely because BWF is based on WAVE.

## Authority split

- **libsndfile `sndfile-info`**: reference container/codec view, including RIFF/WAVE, `WAVE_FORMAT_PCM`, sample rate, channel count, bit width and frame count.
- **FFprobe**: independent technical view of `wav` + `pcm_s16le` + codec tag `0x0001` and contract facts.
- **SoX**: second independent technical view and decoder.
- **FFmpeg + SoX**: exact canonical `s16le` decoded-byte matrix.
- **Artifact object contract**: exact sample rate, channels, 16-bit depth, frame count and optional expected decoded-PCM SHA-256.

No Artifact-specific WAVE parser is introduced. Ancillary RIFF chunks are allowed as container material but are not semantically promoted by R1.

## Real Game pressure test

The current Game revision `413882d197c672c22898d8c7d3c0316f9eaf6997` file `experiments/veilwild-r1/godot/modules/f16/audio/vr_orient_tick_a.wav` passed the profile. libsndfile and FFprobe agreed on 48 kHz / mono / 16-bit / 8,880 frames, while FFmpeg and SoX produced exactly the same 17,760 canonical PCM bytes with SHA-256 `2d4382d8e8d1f6d071c1147d18a5f40166fa9cc51702840b503b861680c5ad73`.

The frozen object contract is `artifact-delivery/shadow-contracts/audio-wave-pcm16-game-smoke-r1.json`; local capability evidence is `artifact-delivery/shadow-bindings/audio-wave-pcm16-local-r1.json`.

## Non-claims

PASS does not establish artistic correctness, subjective quality, loudness/mastering, ancillary metadata truth, Broadcast Wave Format metadata conformance, RF64/WAVE64, compressed WAVE codec support, clipping/silence/phase quality, or Game suitability beyond the consuming Game's own acceptance.
