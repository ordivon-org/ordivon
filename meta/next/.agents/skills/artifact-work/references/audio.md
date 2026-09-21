# Audio reference

## Bounded proven profile

`audio-flac-pcm16-r1`

- native FLAC / `audio/flac`
- RFC 9639
- signed 16-bit PCM, mono/stereo
- bounded metadata block policy
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven providers

- FLAC reference tools 1.5.0 — full-stream test/reference decode
- FFprobe/FFmpeg — independent technical interpretation/decode
- canonical s16le PCM digest comparison — decoded-content identity

## Boundary

FLAC stream decodability alone does not establish expected sample rate, duration/sample count, metadata policy, or decoded semantic identity.

## Source evidence

`/root/projects/ordivon/capabilities/artifact/docs/ARTIFACT_FAMILY_AUDIO_R1.md`
