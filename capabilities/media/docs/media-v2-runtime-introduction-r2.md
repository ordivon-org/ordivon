# Media v2 — runtime-introduction real-production R2

## Scope

Exercise the existing `runtime-introduction` Remotion production through the new external-first AV QC path without importing the legacy Python media stack.

## Build observations

1. `pnpm install --frozen-lockfile` succeeded from the existing lockfile/cache.
2. The first Remotion render failed before media rendering because `@ordivon/identity` exported a generated `tokens.css` that had not yet been materialized.
3. `pnpm tokens:build` generated the declared token artifact from the tracked token source.
4. The second Remotion render completed successfully: 2340 frames at the production's 30 fps composition length.

The generated-token prerequisite is a build-order concern. It is not evidence for a Media-owned rendering abstraction.

## Fresh candidate

Fresh rendered path: `out/runtime-introduction-master.mp4`

Fresh SHA-256:

`sha256:9f476ded056358b95008e8bb5cb2cfbbc14610e5a0a94ae00db8fd3533d9bb6b`

Fresh size: `2258932` bytes.

The v2 FFprobe-based profile gate accepted the candidate as:

- exactly one video stream;
- H.264;
- 1920x1080;
- 30/1 fps;
- yuv420p;
- BT.709 primaries / transfer / matrix;
- limited (`tv`) range;
- no audio stream.

The evidence receipt explicitly leaves semantic quality, aesthetic quality and publication standing unevaluated.

## Lineage mismatch discovered

`productions/runtime-introduction/production.json` currently declares the rendered output digest:

`sha256:7d994f80627968f4e64a3a53c08d5241bb8f398e17d52c24080f935e7c716430`

The fresh render digest is different. Therefore the R2 candidate must **not** be promoted as the exact historical rendered Blob named by `production.json`.

Current disposition:

- fresh candidate mechanical AV profile: **PASS**;
- equality to declared historical output Blob: **FAIL / different bytes**;
- semantic/aesthetic review: **NOT EVALUATED**;
- publication standing: **NOT EVALUATED**;
- historical digest correction: **NOT PERFORMED**.

The mismatch should become a dedicated reproducibility/lineage falsifier rather than being hidden by updating the declared digest.

## Consequence for legacy retirement

This run establishes that the real production's mechanical AV inspection no longer needs `ordivon_studio.assets.probe_media` or `ordivon_studio.qc.validate_video_probe`. Those functions remain present in legacy code but are no longer necessary for the demonstrated v2 slice.
