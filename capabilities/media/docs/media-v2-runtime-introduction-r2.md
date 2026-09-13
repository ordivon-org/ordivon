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

## Lineage observation and 2026-09-13 correction

R2 originally compared the fresh picture-only `out/runtime-introduction-master.mp4` against the `production.json` rendered output digest `sha256:7d994f80627968f4e64a3a53c08d5241bb8f398e17d52c24080f935e7c716430`. That comparison crossed production stages: the declared output is `runtime-introduction-en-av-candidate`, the final picture+narration A/V occurrence. It is not the picture-only master.

The same-stage historical picture occurrence is `runtime-introduction-master-motion` at:

`sha256:77d8eae832a3cac47c641211aa8c9019c04c542faf0ae87a9ae0e82d37acc736`

A 2026-09-13 rerun at source revision `dc447ccd99cbef8d33af3d36b11937b4bf2b57ff`, Remotion `4.0.502`, and the current lockfile reproduced the R2 fresh picture bytes exactly:

`sha256:9f476ded056358b95008e8bb5cb2cfbbc14610e5a0a94ae00db8fd3533d9bb6b` (`2258932` bytes)

Therefore:

- current recipe/toolchain reproducibility: **PASS** for the observed current occurrence;
- current rerender equality to the prior R2 fresh picture: **PASS / byte-identical**;
- current rerender equality to the older accepted picture occurrence `77d8...`: **NO / distinct exact occurrence**;
- comparison of picture-only `9f47...` to final A/V `7d99...`: **INVALID AS AN EQUALITY TEST** because they are different production stages;
- semantic/aesthetic review: **NOT EVALUATED**;
- historical accepted bytes: **PRESERVED**, not rewritten.

The older accepted picture Blob, narration Blob, and final A/V Blob are all still present in the local content-addressed cache with exact matching SHA-256. The v2 rule is to preserve distinct occurrence identity rather than normalize different bytes into one asset. See `productions/runtime-introduction/evidence/media-v2-picture-lineage-recheck-r7.json`.

## Consequence for legacy retirement

This run establishes that the real production's mechanical AV inspection no longer needs `ordivon_studio.assets.probe_media` or `ordivon_studio.qc.validate_video_probe`. Those functions remain present in legacy code but are no longer necessary for the demonstrated v2 slice.
