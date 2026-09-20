# Still image reference

## Bounded proven profile

`still-image-png-srgb-r1`

- PNG / `image/png`
- W3C PNG Third Edition
- static 8-bit RGB/RGBA
- explicit PNG `sRGB` chunk
- bounded profile excludes APNG, iCCP/cICP/HDR semantics
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven validators/providers

- pngcheck 4.0.1 — datastream validity
- ExifTool 13.55 — metadata observation only
- ImageMagick 7.1.2-29 — normalized independent decode
- libvips 8.18.6 — normalized independent decode

Independent decoders must agree on the declared normalized sample representation when the profile requires decoder agreement.

## Boundary

Decoder success is not a substitute for datastream validity, profile constraints, colour correctness, visual quality, metadata truth, or accessibility.

## Source evidence

`/root/projects/ordivon-artifact-v2/docs/ARTIFACT_FAMILY_STILL_IMAGE_R1.md`
