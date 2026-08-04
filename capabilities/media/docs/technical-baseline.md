# Technical baseline

This baseline exists to prevent information loss and cross-medium drift. It is not a fixed visual style.

## Time

- Each Production declares an exact rational frame rate, initially `30/1` for the Runtime technical film.
- Time calculations use integer units or rational time, never floating-point seconds as durable identity.
- Capture, motion render, NLE timeline, captions, and delivery profiles declare their time base.
- Variable-frame-rate source is normalized or proxied before editorial use.

## Video and color

- Web, SVG, and still-design source use sRGB.
- Screen capture is SDR with operating-system HDR disabled.
- Video editorial output is Rec.709 SDR; Resolve project output is initially Rec.709 Gamma 2.4.
- Programmatic motion renders must declare BT.709 primaries, transfer, and matrix, use limited range, and use an approved YUV pixel format.
- Color primaries, transfer, matrix, range, pixel format, and bit depth are machine-checked rather than trusted from file names or editor presets.
- The first workflow avoids Fusion-heavy effects because the current workstation has 16 GB system memory; reusable motion is rendered in Remotion and imported as media.
- ACES/OpenColorIO is not the default for screen-first SDR work. It remains available when real EXR, HDR, camera, or VFX requirements appear.

## Audio

- Editable narration, music, ambience, and effects remain separate.
- Source and mix masters use 48 kHz, 24-bit PCM WAV where the upstream tool allows it.
- Loudness is measured using BS.1770-compatible tooling.
- Delivery loudness is an Output profile, not a destructive change to source stems.
- The first film uses Resolve Fairlight for editorial mixing and FFmpeg for automated inspection and delivery verification.
- Programmatic motion components without audio render no empty audio track.

## Captions and localization

- Internal TimedText JSON is the source.
- WebVTT is the primary Web delivery format.
- SRT is emitted for broad platform compatibility.
- ASS or rendered text is emitted only when visual subtitle styling must be preserved.
- English and Chinese are separately written and timed; translation is not assumed to retain identical cue boundaries.

## Capture

- OBS records recoverable MKV source.
- Capture uses a clean demo environment with secrets, usernames, irrelevant paths, and notifications excluded.
- Source capture remains uncut and receives a Blob digest before editing.
- An edit-friendly proxy or remux is derived; it never replaces the original capture Asset.

## Editorial

- DaVinci Resolve is the first NLE and audio master environment.
- Resolve project exports are retained at named milestones outside Git.
- OTIO snapshots preserve open editorial cut structure where supported.
- Lossy interchange is verified rather than assumed; effects, titles, color, audio processing, and generators may require separate source retention.
- CapCut/剪映 may create platform-specific derivatives but is not the only holder of the master edit.

## Programmatic motion

- Identity and diagrams remain renderer-independent React/SVG.
- Remotion is the first renderer adapter and is pinned exactly across all `remotion` packages.
- Remotion render configuration fixes codec, CRF, pixel format, BT.709 signaling, and muted motion-only output.
- Programmatic renders are version-bound Assets and enter the NLE like other source media.
- Renderer licensing and replacement remain visible; production meaning cannot depend on undocumented Remotion-only state.

## Tokens

- DTCG 2025.10 JSON is the source representation.
- Studio initially compiles only the token types it uses.
- Generated CSS and TypeScript are checked against the source digest.
- Existing `ordivon-web` variables provide a visual baseline, not an unreviewable permanent identity.

## Storage

```text
Git
  source text, code, SVG, DTCG, schemas, manifests, TimedText, OTIO

Windows local workspace
  current raw files, editor projects, caches, proxies, renders

R2
  immutable selected source, editable binary milestones, and approved masters
```

R2 keys use Blob digests. Upload is non-destructive copy with verification. Live editing does not stream directly from object storage.

## QC

Every approved media Output is inspected for:

- digest and size;
- container and stream codecs;
- duration and exact frame rate;
- dimensions and pixel format;
- color metadata and range;
- audio sample rate, channel layout, loudness, and true peak;
- caption presence and parseability;
- relationship to the Production and source revision.

The initial `qc-video` command enforces structural video facts. Loudness, caption/package completeness, and publication-specific checks are added only when the corresponding real outputs exist. Human playback review remains required after machine QC.
