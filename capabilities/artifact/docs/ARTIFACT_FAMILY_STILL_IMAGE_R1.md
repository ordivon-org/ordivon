# Artifact E2E — Still Image Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

This family is the first non-Office proof of the standards-first taxonomy. It does not modify `profile-v1.schema.json`, Temporal production routing, release policy, or any existing production Artifact profile.

## External authority structure

Still images are not one format and do not need an Ordivon image AST. The family selects the native standard for each representation/format and keeps several evidence surfaces independent:

1. **format/datastream validity** — owned by the native format specification and a mature format-aware checker;
2. **profile facts** — bit depth, animation/static status, explicit colour signalling and other use-profile restrictions;
3. **metadata observation** — EXIF/IPTC/XMP/format metadata extraction, without asserting that descriptive/rights values are true;
4. **colour management** — native colour signalling or a selected ICC profile; this is not inferred from “an image decoder opened the file”;
5. **independent decoding** — two materially independent decoder stacks normalize to a declared sample representation and compare resulting pixels;
6. **visual/semantic/human review** — separate evidence when a use profile actually requires it.

A decoder opening the file is therefore not a substitute for format validity, metadata policy, colour correctness, visual quality or accessibility.

## First bounded profile: `still-image-png-srgb-r1`

The first profile is intentionally narrow:

- family: `still-image`;
- representation: `raster`;
- format/media type: PNG / `image/png`;
- purpose: display + exchange;
- W3C PNG Third Edition datastream;
- static only — no APNG chunks;
- 8-bit RGB/RGBA only;
- explicit PNG `sRGB` chunk;
- `iCCP` and `cICP` excluded so ICC/HDR/wide-gamut semantics do not silently enter this profile;
- at least two independent decoders must produce exactly equal normalized 8-bit sRGB RGBA sample bytes.

This profile is **not** a general PNG profile. PNG Third Edition supports APNG and HDR features as well; those require separate profiles and evidence.

## Selected local capability binding

### PNG datastream validity — pngcheck 4.0.1

`pnggroup/pngcheck` is owned by the PNG Development Group. PNG Third Edition's W3C Recommendation transition record explicitly noted that the PNG group had adopted pngcheck, and current pngcheck 4.0.1 contains Third-Edition-aware checks for cICP, HDR-related chunks, APNG chunks and eXIf ordering.

Local carrier:

- `/opt/ordivon/external/pngcheck/4.0.1/bin/pngcheck`
- source tag `v4.0.1`
- source commit `861c978c3b1bac93659202fd25b9b76bc852eee1`
- binary SHA-256 `ba5deaa1b3a737223b5994ff71a05e54a74bc5e545bb08e1e4fd3d0e954fe520`

The upstream CMake project currently defines no ctest cases, so the carrier receipt does **not** claim an upstream ctest PASS. Local functional proof instead establishes:

- valid PNG → pngcheck PASS;
- deliberately corrupted IDAT payload → pngcheck non-zero / fail-closed;
- carrier source/binary identity is frozen.

Claim boundary: pngcheck contributes PNG datastream validity/conformance-oriented evidence. It is not treated as certification that arbitrary PNG encoder/decoder/editor implementations satisfy every W3C implementation conformance requirement.

### Metadata observation — ExifTool 13.55

ExifTool is used only for metadata extraction/inspection. IPTC's current Photo Metadata Standard explicitly documents ExifTool tag mappings as implementation help while stating that those mappings are non-normative. The metadata standard itself, XMP/IIM/EXIF and native image-format embedding rules remain the authority.

Local carrier:

- `/opt/ordivon/external/exiftool/13.55-1/exiftool`
- Arch package `perl-image-exiftool 13.55-1`
- package SHA-256 `11f2f296cdcd8c17879b478201e3e9722a8cc63dfe2bb22df86b728009ecfb6f`
- detached package signature: PASS via Arch keyring, signer T.J. Townsend
- wrapper SHA-256 `4adf4f756837cb3fe2dd1d74f0d6969bfa9565d42ea7d9a8e30845e5aed2c404`

The package was extracted into an isolated `/opt` carrier; the host package database and ambient PATH were not changed.

### Independent decoder matrix — ImageMagick + libvips

The local smoke and unit fixtures were decoded independently through:

- ImageMagick 7.1.2-29;
- libvips 8.18.6 / libpng path.

Both normalize the bounded profile to 8-bit sRGB RGBA sample bytes. A deterministic 8×6 RGBA smoke image produced the exact same sample digest through both decoders:

`06efe5240385e9023016035200fff99e88af1e3bb54da935b3b82f28fa2c0d3d`

The first attempted proof intentionally failed because the fixture was 16-bit while only the ImageMagick path was reduced to 8-bit. That result was rejected rather than interpreted as decoder divergence. After explicitly fixing the fixture/profile normalization at 8-bit RGBA, the independent sample bytes matched exactly.

## Colour boundary

The generic still-image family recognizes ICC as an independent colour-management authority. ICC.1:2022 / profile version 4.4 remains the current ICC v4 specification lineage (co-published as ISO 15076-1:2025). This first PNG profile does not require ICC because it deliberately chooses explicit PNG sRGB signalling.

A future `still-image-*-icc-v4` profile should bind ICC profile identity/validity and colour transforms explicitly. It must not be admitted merely because ImageMagick or another decoder reports a colour-space string.

## Metadata and accessibility boundary

IPTC Photo Metadata can carry descriptive, administrative, rights and accessibility-related properties, including an Alt Text (Accessibility) property. Presence of such a field does **not** make a standalone image universally accessible. Accessibility remains contextual: embedding HTML/document semantics, surrounding text, target consumer and human suitability can all matter.

Accordingly `still-image-png-srgb-r1` observes metadata but makes no accessibility claim.

## Evidence flow

```text
PNG payload
   │
   ├─ pngcheck ──────────────── datastream validity evidence
   │
   ├─ profile fact extraction ─ static / 8-bit / RGB(A) / explicit sRGB
   │
   ├─ ExifTool ──────────────── metadata observation
   │
   ├─ ImageMagick ─┐
   │                ├────────── normalized decoded sample equality
   └─ libvips ─────┘
```

No one tool is promoted to a universal image authority.

## Falsifiers proven

Three focused tests currently pass:

1. conforming bounded static 8-bit sRGB PNG → PASS;
2. PNG that is structurally valid but lacks the profile-required `sRGB` chunk → profile FAIL;
3. PNG with a deliberately corrupted IDAT byte → format check fails closed.

The second test is particularly important: **format validity cannot launder a missing use-profile fact into release acceptance.**

## What remains outside R1

- JPEG/JPEG 2000/TIFF/AVIF/JPEG XL profiles;
- SVG/vector profile;
- APNG;
- HDR/cICP PNG;
- ICC-v4 managed wide-gamut/print workflows;
- preservation/JHOVE-oriented image profiles;
- professional-photo IPTC field requirements;
- human visual quality or content review;
- embedded-context accessibility.

Those should be added as independent profiles only when a real workload requires them.
