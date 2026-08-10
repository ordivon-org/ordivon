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
- the Art & Expression Laboratory for cross-medium aesthetics, narrative, rhetoric, motion, sound, and style research;
- reusable editorial, visual, motion, caption, and interactive primitives;
- selected-asset provenance and rights records;
- production manifests and source packages;
- deterministic media inspection, transformation, delivery, and verified content-addressed archival tooling;
- real source-bound Productions across different media, currently Runtime Introduction motion and the Writing-only Browser Perception Note.

Large media bytes, editor caches, proxies, and exports are intentionally outside Git. Git stores identities, manifests, open interchange snapshots, editable text and code, and checksums that resolve those bytes from a local cache or object store.

## Start here

- [`STUDIO.md`](STUDIO.md) — first-principles architecture and corrected technical choices;
- [`research/expression/README.md`](research/expression/README.md) — Art & Expression Laboratory, its research boundary, tensions, and Agent loop;
- [`research/expression/evidence-map.md`](research/expression/evidence-map.md) — evidence-backed aesthetic and narrative priors with explicit scope limits;
- [`docs/media-model.md`](docs/media-model.md) — Asset, Blob, Production, Claim, TimedText, and Output objects;
- [`docs/technical-baseline.md`](docs/technical-baseline.md) — time, color, audio, storage, editor, and rendering baseline;
- [`docs/storage-layout.md`](docs/storage-layout.md) — selected-byte durability boundary and local content-addressed archival gate;
- [`docs/fast-inner-loop.md`](docs/fast-inner-loop.md) — local render/review iteration, hidden-precondition handling, and technical-versus-semantic audit boundary;
- [`docs/review-consumption.md`](docs/review-consumption.md) — Agent review consumption, authority snapshots, transient critique, and bounded revision evidence;
- [`docs/artifact-perception.md`](docs/artifact-perception.md) — temporal observation sampling, model-view preparation, and native image-transport boundary;
- [`docs/resolve-adapter.md`](docs/resolve-adapter.md) — the bounded Resolve Free internal-runner bridge;
- [`productions/runtime-introduction/README.md`](productions/runtime-introduction/README.md) — first real motion production vertical;
- [`productions/browser-perception-note/story.mdx`](productions/browser-perception-note/story.mdx) — second materially different, Writing-only Production pressure-testing cross-medium assumptions.

## Fresh Workspace bootstrap

JavaScript production commands fail fast when workspace dependencies are absent instead of running Python/media checks first and discovering `tsc` late. Materialize them once with:

```bash
pnpm bootstrap
```

`pnpm deps:check` is the cheap readiness probe. Python-only model and test commands remain usable without JavaScript bootstrap.

## Current state

The design foundation is executable and verified:

- Production, Claim, Asset, and TimedText contracts validate;
- DTCG source generates shared CSS and TypeScript tokens;
- one React/SVG Runtime visual is consumed by both Preview and Remotion;
- the Preview app builds;
- the Runtime motion composition renders at 1920×1080, 30 fps;
- QC verifies H.264, `yuv420p`, limited range, complete BT.709 signaling, and no empty audio track;
- progressive perception materializes exact review pixels, and native Runtime `workspace.content` delivery has passed a fresh vision-capable Agent acceptance with a bounded semantic `no-op`;
- the Resolve Free adapter has passed real read-only, bounded-mutation, and six-case compatibility acceptances against Resolve Free 21.0.3.7; native OTIO import preserves clip durations and gaps, while explicit Append source ranges are excluded from production assembly.

DaVinci Resolve 21, OBS Studio 32, and Figma Desktop are installed on the current workstation. They are used only when a production actually requires them.

Runtime Introduction now has a complete source-bound 78-second English **picture+narration review candidate**. The revised picture master, exact 48 kHz/24-bit narration stem, and deterministic A/V mux are each copied to and reverified from the local content-addressed cache under `D:\OrdivonStudio\cache\objects\sha256\...`. Voice materialization was allowed to revise the previous tail timing instead of being forced into an abstract edit. The film remains `rendered / review`, not approved or published, because naturalness and publication-worthiness of the selected synthetic voice are a real human auditory-response claim that current machine evidence does not establish. Its other article/vertical/interactive/Upwork outputs remain planned.

The second Production, Browser Perception Note, is Writing-only and has an internally `approved` semantic-text Output bound to Web revision `e11a6585b049776e46011289c80197f1183ec330`. It deliberately uses `workingProfile: {}` rather than inventing video/audio parameters. This second workload also forced generic Receipt validation to dispatch by `kind` instead of treating every Receipt as a Runtime Demo Receipt.

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
