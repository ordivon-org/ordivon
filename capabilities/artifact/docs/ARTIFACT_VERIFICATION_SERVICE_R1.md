# Artifact Verification Service R1

## Standing

`LOCAL_THIN_ADAPTER_OVER_LIVE_PROVEN_PROFILE_VALIDATORS`

This service exists for one narrow reason: consumers such as Game may already have artifact bytes and need Artifact to answer whether those exact bytes satisfy one exact Artifact profile. The pre-existing `request-v1` remains a build/release envelope and is not widened for this use case.

R1 adds no universal artifact AST, no transport protocol, no scheduler, no publication semantics, and no caller-domain meaning. The request binds only:

- one normalized Artifact profile identity + SHA-256;
- one regular-file subject path + SHA-256;
- one optional exact object-contract file + SHA-256;
- one evidence directory;
- optional consumer metadata that carries no verification authority.

The adapter admits only an explicit R1 route whose profile has exactly one `LOCAL_LIVE_PROVEN` capability binding, rechecks all byte digests before delegation, then calls the existing isolated family verifier. Its service result embeds the untouched family result and digest-binds the request/profile/subject/binding/verifier identities.

## Current R1 routes

- `still-image-png-srgb-r1`
- `still-image-svg-static-r1`
- `dataset-parquet-flat-r1`
- `audio-flac-pcm16-r1`
- `audio-wave-pcm16-r1`
- `audio-ogg-vorbis-r1`
- `geospatial-geopackage-point-r1`
- `moving-image-matroska-ffv1-v3-r1`
- `design-3d-glb-static-mesh-r1`
- `web-archive-warc-response-r1`
- `message-internet-text-r1`

`software-release-oci-image-r1` is intentionally not routed because its subject is a directory-layout object rather than a regular-file subject. Production Office/Web delivery profiles remain on their existing build/release path.

## First real consumer smoke

The first cross-owner smoke uses the exact current Game subject `web-v3/assets/rescue-expression.png` from Game revision `413882d197c672c22898d8c7d3c0316f9eaf6997`. The subject passed `still-image-png-srgb-r1` through the thin service with exact independent-decoder agreement. The bounded receipt is frozen in `artifact-delivery/consumer-acceptance/game-station-zero-still-image-r1.json`.

This was deliberately one consumer/profile proof, not a Game asset-pipeline graduation. A second consumer smoke now covers `audio-wave-pcm16-r1`: Veilwild `vr_orient_tick_a.wav` passes libsndfile + FFprobe + SoX technical agreement and exact FFmpeg/SoX canonical PCM equality; its receipt is `artifact-delivery/consumer-acceptance/game-veilwild-wave-pcm16-r1.json`. Ogg/Vorbis, SVG, Tiled, Aseprite, richer glTF and Godot release profiles remain separate admission work.

## Boundary

A service `PASS` means only that the exact requested subject bytes passed the selected profile through its already live-proven family verifier. It does not:

- promote Profile v2 from shadow to production;
- prove that Game, Research, Media, or another caller should use the artifact;
- prove artistic quality, semantic truth, rights, accessibility, or other profile non-claims;
- turn a local path into an Artifact transport contract;
- make Artifact own consumer-domain acceptance.

Cross-owner immutable transport should continue to use Runtime input authorities or the relevant mature external storage/API substrate.
