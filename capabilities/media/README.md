# Ordivon Studio

Ordivon Studio is the creative-technology and multi-medium production environment for Ordivon.

It turns facts and executable evidence owned by Ordivon projects into articles, visual systems, audio, video, interactive explanations, demonstrations, and platform-specific publication packages. It also uses those productions to expose product-entry, comprehension, and experience failures.

Studio does **not** become a second owner of Runtime, Host, Harness, research, or public-site facts.

```text
owning project facts and executable evidence
→ Studio narrative, visual, audio, motion, and interaction sources
→ editable production masters
→ deterministic delivery variants
→ Web, GitHub, YouTube, Douyin, Upwork, and other surfaces
```

## What this repository owns

- the Ordivon cross-medium identity source;
- reusable editorial, visual, motion, caption, and interactive primitives;
- selected-asset provenance and rights records;
- production manifests and source packages;
- deterministic media inspection, transformation, and delivery tooling;
- the first Runtime introduction production.

Large media bytes, editor caches, proxies, and exports are intentionally outside Git. Git stores identities, manifests, open interchange snapshots, editable text and code, and checksums that resolve those bytes from a local cache or object store.

## Start here

- [`STUDIO.md`](STUDIO.md) — first-principles architecture and corrected technical choices;
- [`docs/media-model.md`](docs/media-model.md) — Asset, Blob, Production, Claim, TimedText, and Output objects;
- [`docs/technical-baseline.md`](docs/technical-baseline.md) — time, color, audio, storage, editor, and rendering baseline;
- [`docs/resolve-adapter.md`](docs/resolve-adapter.md) — the bounded Resolve Free internal-runner bridge;
- [`productions/runtime-introduction/README.md`](productions/runtime-introduction/README.md) — first real production vertical.

## Current state

The design foundation is executable and verified:

- Production, Claim, Asset, and TimedText contracts validate;
- DTCG source generates shared CSS and TypeScript tokens;
- one React/SVG Runtime visual is consumed by both Preview and Remotion;
- the Preview app builds;
- the Runtime motion composition renders at 1920×1080, 30 fps;
- QC verifies H.264, `yuv420p`, limited range, complete BT.709 signaling, and no empty audio track;
- the Resolve Free adapter has passed real read-only and bounded-mutation internal-menu acceptances against Resolve 21.0.3, including Project creation, settings, Bin and media import, Timeline assembly, save, and restoration of the previously open Project.

DaVinci Resolve 21, OBS Studio 32, and Figma Desktop are installed on the current workstation. Resolve editing, real OBS capture, narration, asset registration, and final delivery remain production work rather than repository architecture.

The first complete target is one editable Runtime production that can produce:

- an English technical article;
- an English landscape project film;
- a Chinese vertical short;
- reusable architecture motion;
- an Upwork portfolio package;
- a Web publication package.

## Tool split

```text
React / SVG             reusable visual primitives
Remotion adapter        deterministic motion rendering
DaVinci Resolve         selected editorial, color, and Fairlight environment
Resolve adapter         bounded internal operations for Resolve Free
OpenTimelineIO          open editorial interchange snapshots
OBS                     selected real-product capture environment
FFmpeg / ffprobe        media transforms and machine QC
Python                  asset, timeline, caption, and storage tooling
MDX                     editorial and interactive source
DTCG JSON               cross-medium design-token source
R2 + local cache        selected immutable media-byte storage model
```

## License

Apache-2.0. Production assets may carry their own rights and usage records in their Asset metadata.
