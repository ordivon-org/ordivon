# Artifact E2E — Moving Image Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Moving Image R1 proves a narrow preservation-oriented profile rather than generic video playback: one RFC 9559 Matroska v4 container carrying one stable RFC 9043 FFV1 version-3 video stream.

## External authorities

- **Matroska:** IETF RFC 9559; IANA media type `video/matroska`.
- **FFV1:** IETF RFC 9043. Version 3 is the stable modern branch; micro-version 4 is the first stable variant of version 3.
- **Implementation checking:** MediaConch 25.04 built-in Matroska/FFV1 implementation reports.
- **Technical interpretation / decode:** MediaInfo 26.05 through the frozen MediaConch carrier plus FFprobe/FFmpeg 9.0.

The profile does not promote a tool name into a standard. Standards describe what must hold; mature implementations produce evidence about those claims.

## First bounded profile

`moving-image-matroska-ffv1-v3-r1`

```text
family             moving-image
representation     audiovisual-container
container          Matroska v4 / RFC 9559
media type         video/matroska
codec              FFV1 version 3, micro-version >= 4 / RFC 9043
stream topology    exactly one video stream
pixel format       yuv422p / 8-bit / 4:2:2
scan               progressive
frame-rate mode    CFR
purpose            preservation + interchange
```

Audio, subtitles, attachments and other pixel formats are deliberately outside R1.

## Object contract

Schema:

`artifact-delivery/shadow-contracts/moving-image-ffv1-contract-v1.schema.json`

The object contract binds:

- width / height;
- exact frame-rate rational;
- frame count;
- pixel format / bit depth / chroma subsampling;
- progressive scan;
- optional SHA-256 of the canonical decoded rawvideo frame sequence.

The decoded-content digest is intentionally independent from Matroska bytes. Two independently muxed files from the same deterministic source produced different Matroska SHA-256 digests while decoding to the same rawvideo SHA-256. Therefore:

```text
ContainerBytesIdentity != DecodedVisualIdentity
```

## MediaConch boundary

MediaConch 25.04 was materialized at:

`/opt/ordivon/external/mediaconch/25.04-1/`

The official MediaArea Arch package is pinned by SHA-256:

`25be0269c5e7440e49d46e3ef19dba36f4979e6999cb75b9e73d405dc4c42e1a`

MediaConch binary SHA-256:

`d89480c06f991c7d4085580704b480c08b0ad53d53f38a6a6d3e63d17f009eed`

The official adjacent detached-signature URL is unavailable. R1 therefore does **not** claim upstream signature verification for the MediaConch executable. The exact official HTTPS package digest is pinned, while the frozen Arch dependency packages (`libzen`, `libmediainfo`, `graphviz`, `libmms`, `tinyxml2`) were all verified with Arch package signatures.

A first carrier attempt failed closed because the transitive `libmediainfo` runtime dependencies were incomplete. The carrier was promoted only after `ldd` reported no unresolved libraries.

## Implementation-check semantics

For the clean smoke artifact, MediaConch executed:

```text
Matroska / EBML
  checks             23
  tests run          606
  pass               606
  fail               0
  warn               0

FFV1 clean-file group
  checks              1
  tests run           0
  fail                0
  warn                0
```

The zero-test clean FFV1 group is **not** interpreted as full FFV1 conformance. It is an explicit non-claim.

However, MediaConch still provides meaningful FFV1 integrity evidence: after one byte inside an FFV1 packet was changed, it reported `FFV1-SLICE-JUNK` failures as well as a Matroska `EBML-CRC-VALID` failure.

Critically, FFmpeg decoding the same corrupted file returned process exit code **0**, despite reporting a slice CRC mismatch and producing different decoded bytes. Hence:

```text
FFmpegDecodeExit0 != Bitstream/ContainerIntegrity
```

This is why the specialist implementation checker remains a required gate.

## Technical cross-view

MediaInfo and FFprobe independently observe the bounded technical contract.

The live smoke reports:

```text
Matroska version     4
FFV1 version         3.4
video tracks         1
width                64
height               64
frame rate           10/1 CFR
frame count          10
pixel format         yuv422p
chroma               4:2:2
bit depth            8
scan                 Progressive
```

FFmpeg decodes to canonical rawvideo `yuv422p` in frame order. For the smoke object:

- expected raw bytes: 81,920;
- observed raw bytes: 81,920;
- rawvideo SHA-256: `568441a6da6651e5f07c68d0e040ffbcc155298505b9248c08b7ae7e77ba229f`.

## Live proof

Runtime job:

`job-01a095ed-cb2d-7c81-ad1d-42aa716a03e1`

Exact smoke artifact:

- SHA-256 `c45b36677841f850f7eca665a0a7546165ab1f8a8d14fdab1bf25f85238b7d1e`;
- size 27,264 bytes;
- object-contract canonical digest `288c3a03ef7287f2c6e110a9f048b1b0674c3a43e420d54e76b5f278dc234f8b`.

MediaConch implementation evidence SHA-256:

`cf639f2772ced215240f87f27d3c1a5b98db61d77a0fb2bd7dd00f308aee7c03`

## Falsifiers proven

Eight focused tests currently pass:

1. bounded Matroska v4 + stable FFV1 v3 + matching object contract → PASS;
2. valid implementation-checking file + wrong contract dimensions → FAIL;
3. one FFV1 packet byte corrupted → FAIL even though FFmpeg process exits zero;
4. valid FFV1 v1 stream → valid file but R1 profile FAIL;
5. valid Matroska/FFV1 plus audio track → video-only profile FAIL;
6. implementation checks pass but expected decoded-frame digest is wrong → FAIL;
7. contract requests non-R1 pixel format → FAIL before external evidence promotion;
8. frozen tool identities are digest-checked.

## Claim boundary

PASS does not claim visual/artistic correctness, arbitrary-player compatibility, full FFV1 conformance merely from MediaConch's zero-test clean FFV1 group, audio/subtitle semantics, broad colorimetric correctness, or bit-identical Matroska reproducibility.
