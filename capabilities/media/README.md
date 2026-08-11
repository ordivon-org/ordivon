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
- deterministic media inspection, transformation, delivery, verified local CAS archive/materialization, and narrow Cloudflare R2 replica/restore tooling;
- real source-bound Productions across different media, currently Runtime Introduction motion and the Writing-only Browser Perception Note.

Large media bytes, editor caches, proxies, and exports are intentionally outside Git. Git stores identities, manifests, open interchange snapshots, editable text and code, and checksums that resolve those bytes from a local cache or object store.

## Start here

- [`STUDIO.md`](STUDIO.md) — first-principles architecture and corrected technical choices;
- [`research/expression/README.md`](research/expression/README.md) — Art & Expression Laboratory, its research boundary, tensions, and Agent loop;
- [`research/expression/evidence-map.md`](research/expression/evidence-map.md) — evidence-backed aesthetic and narrative priors with explicit scope limits;
- [`research/expression/cultural-observatory.md`](research/expression/cultural-observatory.md) — live cultural/attention observation, winner-control corpus discipline, and autonomous hypothesis testing;
- [`docs/media-model.md`](docs/media-model.md) — Asset, Blob, Production, Claim, TimedText, and Output objects;
- [`docs/technical-baseline.md`](docs/technical-baseline.md) — time, color, audio, storage, editor, and rendering baseline;
- [`docs/storage-layout.md`](docs/storage-layout.md) — selected-byte durability boundary, verified local archive/materialization, and accepted private R2 replica/restore path;
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
- optional Resolve/OTIO equipment has passed real read-only, bounded-mutation, and six-case compatibility acceptances against Resolve Free 21.0.3.7; it is excluded from the default Core dependency/check path and is validated explicitly with `pnpm check:equipment:resolve` when that NLE path is used.

DaVinci Resolve 21, OBS Studio 32, and Figma Desktop are installed on the current workstation. They are used only when a production actually requires them.

Runtime Introduction now has a complete source-bound 78-second English **picture+narration review candidate**. P2 established exact local selected bytes; P3 proved fresh-Workspace recovery through `materialize`; P4 then replicated the selected picture, narration stem, and final A/V candidate to the private Cloudflare R2 bucket `ordivon-artifacts`, redownload-hashed all three, and restored the picture master after deliberately removing its local CAS object. The productized `ordivon-studio r2 restore` path recreated the exact local digest and a valid 78-second H.264 BT.709 working picture. The audition copy remains at `D:\OrdivonStudio\productions\runtime-introduction\review\runtime-introduction-en-7d994f806279.mp4`. The film remains `rendered / review`, not approved or published, because off-machine durability does not answer the remaining human auditory-response claim about the selected voice.

The second Production, Browser Perception Note, is Writing-only and has an internally `approved` semantic-text Output bound to Web revision `e11a6585b049776e46011289c80197f1183ec330`. Its approved Output digest exactly matches the Git-tracked `story.mdx` payload and recovers from the Git object without a media-cache copy. This materially different case narrows the durability invariant: exact selected bytes need a durable authority, but that authority need not be the media CAS when source control already owns the exact payload. The workload also keeps `workingProfile: {}` rather than inventing video/audio parameters and preserves generic Receipt dispatch by `kind`.

## Tool split

```text
React / SVG             reusable visual primitives
Remotion adapter        deterministic motion rendering
DaVinci Resolve         selected editorial, color, and Fairlight environment
Resolve adapter         bounded internal operations for Resolve Free
OpenTimelineIO          optional NLE interchange snapshots (`resolve` extra)
OBS                     selected real-product capture environment
FFmpeg / ffprobe        media transforms and machine QC
Python                  asset, timeline, caption, and storage tooling
MDX                     editorial and interactive source
DTCG JSON               cross-medium design-token source
Local CAS               selected binary/media byte authority and working recovery
Cloudflare R2 adapter   private off-machine replica + destructive-loss restore path
```

## License

Apache-2.0. Production assets may carry their own rights and usage records in their Asset metadata.
