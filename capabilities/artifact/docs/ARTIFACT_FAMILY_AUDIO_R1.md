# Artifact E2E — Audio Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Audio R1 proves a bounded native FLAC profile rather than generic “media support”. The external format authority is IETF RFC 9639. IANA registers `audio/flac` for native FLAC audio; FLAC inside another container takes that container's media type.

## First bounded profile

`audio-flac-pcm16-r1`

```text
family          audio
representation  lossless-encoded-audio
format          FLAC
media type      audio/flac
standard        RFC 9639
PCM domain      signed 16-bit, mono/stereo
purpose         interchange
```

R1 intentionally excludes Ogg FLAC, MP4-mapped FLAC, >2 channels, non-16-bit PCM, and metadata block families not yet given Artifact semantics.

Allowed metadata block types are:

- STREAMINFO (0)
- PADDING (1)
- SEEKTABLE (3)
- VORBIS_COMMENT (4)

APPLICATION, CUESHEET, PICTURE, reserved/unknown blocks, and container mappings remain outside R1.

## Object contract

Schema:

`artifact-delivery/shadow-contracts/audio-flac-contract-v1.schema.json`

The contract binds exact decoded-audio technical facts:

- sample rate;
- mono/stereo channel count;
- 16-bit PCM;
- exact total sample count;
- optional expected canonical decoded-PCM SHA-256.

This last field is deliberately representation-independent: two different valid FLAC encodings of the same PCM may have different artifact byte digests but the same decoded-audio identity.

## Evidence layers

Audio R1 keeps several truths separate:

```text
RFC/profile legality
        │
        ├─ reference FLAC full-stream test
        ├─ STREAMINFO technical facts + decoded MD5
        ├─ bounded metadata-block policy
        ├─ FFprobe independent technical interpretation
        ├─ reference libFLAC decode
        └─ FFmpeg independent decode
                    │
                    ▼
          canonical s16le PCM bytes
                    │
          exact decoder agreement
                    │
          object-contract PCM identity
```

`flac -t` alone is not Artifact PASS. It establishes stream decodability/integrity under the reference implementation, not the object's expected sample rate, duration, metadata policy, or decoded semantic identity.

## Capability binding

### FLAC reference tools 1.5.0

Frozen signed carrier:

`/opt/ordivon/external/flac/1.5.0-1/`

- Arch package `flac 1.5.0-1`;
- package SHA-256 `7c8dce6bde402b9d243fd240847722a57b94df1dbf53e0cabc9119219dd04735`;
- detached package signature: PASS;
- `flac` binary SHA-256 `73091e774fa7c80e6c97b6efe9ba9b1b8fb01ed27cba83e377f320b4ce7d42d9`;
- `metaflac` binary SHA-256 `db558716cd01aca0b5b807b5f5377079f82cfe0a119d5c8e2e1bd2405222ebc6`.

The reference path contributes:

- complete-stream decode/test;
- STREAMINFO;
- metadata-block enumeration;
- canonical raw PCM decode.

### FFmpeg 9.0

Independent consumer path:

- package `ffmpeg 2:9.0-5`;
- `/usr/bin/ffmpeg` SHA-256 `46dea8dda22fcc6572a524ba805428a18f0caadf61fe75b443676a485b10ea5d`;
- `/usr/bin/ffprobe` SHA-256 `1e165ca6749e6343f71cf85eb3b90283db0e40e3e04ee3adfb703e81d8459a7c`.

FFprobe independently checks native FLAC identification, sample rate, channels, raw bit depth and total samples. FFmpeg independently decodes the stream to canonical signed little-endian interleaved 16-bit PCM.

## Live proof

Runtime job:

`job-01a095e3-7945-75c0-a9e4-2ca26be99637`

Exact FLAC artifact:

- SHA-256 `033007e2f17db0b5a9a9a020f3fa1a2de1b485d0f87fabbcb5cbd8f75c670a3d`;
- size 47,005 bytes;
- contract canonical digest `f28d14db8a76b5b069bff6a7883869715fe4901ed4f5c03b8fd852cedcb8efbb`.

Both decoders independently produced exactly 192,000 bytes of `s16le` PCM with the same SHA-256:

`ba1d2877f8fea56cb5c8c8b37be25d0b3910408e8ecf0e58559dacf8eb8b7507`

STREAMINFO decoded-audio MD5 and the MD5 of canonical decoded PCM also matched exactly:

`bd4ab533291afc436287daaa424b7c6a`

Technical facts agreed across STREAMINFO and FFprobe:

```text
sample rate     48000 Hz
channels        2
bits/sample     16
total samples   48000
```

## Falsifiers proven

Seven focused tests pass:

1. valid native FLAC + matching object contract → PASS;
2. FLAC remains reference-valid but contract sample rate is wrong → Artifact FAIL;
3. encoded frame bytes are corrupted → fail closed;
4. PICTURE metadata is added and `flac -t` still passes, but R1 metadata policy → FAIL;
5. both decoders produce identical PCM but contract expected PCM digest is wrong → FAIL;
6. contract attempts 24-bit PCM outside the bounded R1 → FAIL before decoder evidence;
7. frozen tool digests are checked against the local proven substrate.

The core distinctions are therefore:

```text
FLACReadable != AudioContractSatisfied
ReferenceIntegrity != ProfileSatisfied
TwoDecodersAgree != ExpectedAudioIdentity
```

## Claim boundary

PASS does not establish subjective quality, loudness/mastering compliance, clipping/silence/phase quality, truth of tags, factual/artistic correctness, or general preservation-policy compliance.
