# Moving image reference

## Bounded proven profile

`moving-image-matroska-ffv1-v3-r1`

- Matroska v4 / RFC 9559 / `video/matroska`
- FFV1 version 3, stable micro-version >= 4 / RFC 9043
- one video stream, yuv422p, 8-bit 4:2:2, progressive, CFR
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven providers

- MediaConch 25.04 — Matroska/FFV1 implementation checks
- MediaInfo 26.05 — technical interpretation
- FFprobe/FFmpeg 9.0 — independent decode/technical evidence
- canonical rawvideo digest comparison — decoded visual identity

## Boundary

`ContainerBytesIdentity != DecodedVisualIdentity`. Two valid encodings/muxes may differ bytewise while decoding to identical content.

## Source evidence

`/root/projects/ordivon-artifact-v2/docs/ARTIFACT_FAMILY_MOVING_IMAGE_R1.md`
