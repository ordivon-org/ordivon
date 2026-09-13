# Artifact E2E — Still Image / Static SVG R1

## Standing

`SHADOW_PROFILE_LOCAL_LIVE_PROVEN_WITH_RENDERER_PIXEL_DIVERGENCE`

R1 covers a deliberately narrow static SVG display/interchange subset needed by current Game assets. It is not a claim of full SVG 1.1 or SVG 2 conformance.

The profile requires well-formed XML in the SVG namespace; positive numeric `width`/`height`; `viewBox="0 0 width height"`; and a bounded set of static primitive elements/attributes. Scripts, event handlers, animation, external references, embedded raster images, `foreignObject`, style elements and DOCTYPE/entity declarations are rejected before rendering.

Authority is split across mature implementations:

- libxml2 `xmllint`: XML well-formedness with network access disabled;
- librsvg `rsvg-convert`: reference non-empty rasterization and intrinsic dimensions;
- pinned Chromium + Firefox: real browser `<img>` decode/raster facts.

## Current Game pressure test

At Game revision `809a82b733e3b3c761847a72a6a7fb7a94502ae5`, `expression-signals.svg`, `hazard-signal.svg` and `system-signal.svg` all pass. Chromium, Firefox and librsvg agree on intrinsic dimensions; Chromium and Firefox also agree on non-transparent-pixel counts. Browser pixel checksums differ, reflecting renderer/anti-alias implementation differences. R1 records that divergence and does not require pixel-exact cross-renderer equality.

## Boundary

PASS establishes exact-byte admission to this static-safe subset plus successful reference/browser rendering. It does not establish dynamic SVG/CSS/external-resource behavior, full-language conformance, accessibility quality, semantic/artistic correctness, print fidelity, rights, or caller-domain suitability.
