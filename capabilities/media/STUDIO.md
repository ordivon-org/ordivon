# Studio design

## The irreducible problem

Ordivon products and research own reality: code, state, interfaces, executable demonstrations, claims, evidence, and limits. A public work must transform that reality into a medium-specific experience without creating a second truth store or destroying the ability to re-edit the work.

The durable Studio problem is therefore:

```text
source-bound facts
+ reusable identity
+ immutable media bytes
+ editable medium-specific structure
+ human creative judgment
→ many truthful, coherent, replaceable delivery forms
```

The architecture is optimized for information preservation and recomposition, not for maximizing the number of tools or formal records.

## Corrected decisions

### 1. Semantic identity and byte identity are different

A SHA-256 digest identifies exact bytes. It does not provide a stable human or production role.

Studio therefore uses both:

```text
asset ID       stable semantic identity inside a production
blob digest    immutable identity of one exact byte sequence
```

`runtime-demo-primary` may point to a new selected Blob after a recapture. The previous Blob remains addressable and its replacement remains explicit.

### 2. There is no single universal media master

Different media preserve different truths:

- a Resolve project preserves NLE-specific edit, color, Fairlight, and effect state;
- an OTIO file preserves open editorial cut structure and metadata, but not every proprietary effect;
- Remotion source preserves deterministic programmatic motion;
- raw recordings and stems preserve source information;
- delivery MP4, AAC, WebVTT, and images are outputs, not sources.

Studio retains the narrow source required to reconstruct each layer instead of declaring OTIO, Resolve, or MP4 the sole canonical object.

### 3. Timed text is richer than a delivery subtitle file

WebVTT and SRT are delivery formats. Internal timed text needs stable cue identity, language relationships, speaker, semantic kind, provisional or locked timing, and frame-rate context.

Studio owns a small JSON TimedText model and derives WebVTT, SRT, ASS, chapters, transcript fragments, and interactive synchronization from it.

### 4. DTCG is the token source; the transformer is replaceable

The DTCG 2025.10 format is the cross-tool source format.

Studio compiles only the subset it actually uses—color, typography, spacing, duration, easing, and layout—from a small audited transformer. The transformer is replaceable; token source files and their meaning are not tied to one design-tool adapter.

### 5. Programmatic visuals are independent of the video renderer

Reusable diagrams, labels, terminals, status views, and visual grammar live as React/SVG primitives. Remotion is the first motion renderer, not the owner of the visual language.

```text
identity tokens
→ React / SVG visual primitives
→ Remotion compositions, Web interactions, still images, or other renderers
```

This contains Remotion's special licensing and renderer-specific APIs at an adapter boundary.

### 6. Object storage is a remote replica, not the only archive

The current working set lives on Windows-local storage. Immutable selected assets and masters are copied to R2 under content-addressed keys. Git stores manifests and checksums.

R2 must not be mounted as the live NLE filesystem. Upload uses copy semantics, never destructive synchronization, and an object is never overwritten at a digest key. Irreplaceable source remains in at least the local working set and the remote object store; a second offline replica can be added without changing identifiers.

### 7. Product truth remains revision-bound

A Studio claim references the owning repository and exact revision. The claim record states the allowed public meaning, known boundary, and evidence target. It does not copy product maturity or become a permanent product authority.

When the source revision changes, Studio either retains the historical production claim or explicitly rebases it after review.

### 8. AI is a production actor, not a data model

Text, image, video, voice, music, transcription, and translation providers remain replaceable. A selected AI-derived asset records provider, model, settings, prompt or instruction source, input Asset IDs, and output Blob digest.

Temporary generations do not all enter permanent provenance. Selected assets and published outputs do.

### 9. Creative judgment is claim-dependent, not permanently human-gated

Studio is human-facing, but an Agent should not be forced to imitate a human editor and then wait for a human approval ritual at every composition boundary. Agents may generate, critique, select, edit, and publish within source-bound production authority.

The important distinction is **what kind of claim a judgment makes**:

```text
mechanical / factual claim
    → verify against source and production evidence

medium craft judgment
    → use mature conventions, explicit intent, and bounded critique

human-experience claim
    → use empirical priors and sample human/expert response only when uncertainty matters
```

One human preference is not universal taste authority, and one Agent preference is not human-perception truth. The Art & Expression Laboratory in `research/expression/` supplies cross-medium priors, records where they fail, and lets later Agents inherit better judgment rather than requiring permanent human supervision.

## Art and expression research

Creative infrastructure is incomplete if it preserves media perfectly but has no disciplined way to reason about why one composition is clearer, more beautiful, more compelling, more memorable, or more narratively effective than another.

[`research/expression/README.md`](research/expression/README.md) therefore owns the cross-medium Art & Expression Laboratory. It studies empirical aesthetics, visual composition, narratology, motion/editing, sound/music, rhetoric/voice, style/culture, and computational aesthetics. Its machine-readable [`context.json`](research/expression/context.json) is context for Agent judgment, not a universal style generator.

Medium-specific systems remain free to specialize these priors. Web, for example, can bias toward fluency, trust, hierarchy, and accessibility while a film can spend substantially more uncertainty on tension, surprise, and temporal expression.

C2 makes that specialization explicit in [`research/expression/profiles/`](research/expression/profiles/). Motion/Video and Writing now have operational medium profiles; Web remains owned by its own repository and binds Studio as an upstream consumer. Still, Audio, and Interactive remain provisional until real production earns promotion.

## System shape

```text
ordivon-studio
├── apps
│   ├── preview             cross-medium source and production preview
│   └── motion-remotion     first programmatic video renderer
├── packages
│   ├── identity            DTCG source and generated platform tokens
│   └── visuals             renderer-independent React/SVG primitives
├── schemas                 language-neutral production contracts
├── src/ordivon_studio      Python media, asset, caption, timeline, and QC tools
└── productions             real article, video, audio, and interactive sources
```

## Dependencies on the rest of Ordivon

```text
Runtime / Host / Harness / research repositories
    own facts, demos, fixtures, and evidence
                   ↓
Studio binds exact revisions and captures or renders expression sources
                   ↓
Web and external platforms consume exported publication packages
```

No product repository imports Studio to execute its core behavior. Web may consume released identity and visual outputs, but Studio cannot redefine Web editorial authority or product facts.

## First production

`productions/runtime-introduction` is the architectural acceptance case. It must prove that one source package can bind Runtime facts, preserve raw evidence, compose real capture and generated motion, keep audio and captions editable, and export multiple platform variants without duplicating the whole production.

C3 adds one thin continuation layer: [`docs/production-cognition.md`](docs/production-cognition.md). A Production may reference a Markdown cognition record that recovers current `FRAME/BIND/EXPRESS/RENDER/AUDIT/DECIDE` judgment plus scoped post-decision `LEARNING` while leaving physical and factual authority in the existing manifest, Claim, Asset, Timeline, and evidence records.

C4 adds a correspondingly thin execution-side creative loop: [`docs/fast-inner-loop.md`](docs/fast-inner-loop.md). Supported motion entrypoints satisfy deterministic local preconditions, produce a real render, and compile disposable technical/keyframe review evidence. They deliberately stop before semantic/aesthetic approval; the Agent remains responsible for `AUDIT` and `DECIDE`.

C5 adds the consumption boundary: [`docs/review-consumption.md`](docs/review-consumption.md). Review packets freeze the relevant Production/Cognition/Claim decision context alongside render evidence, while Agent critique remains transient by default. A bounded revision is evidenced by the source diff and new artifact rather than by storing an approval transcript.

C6 adds the perception-preparation boundary: [`docs/artifact-perception.md`](docs/artifact-perception.md). Video review combines temporal coverage with pixel-change peaks, materializes exact full-resolution observation frames and an ordered contact sheet, and leaves interpretation to a vision-capable Agent. Native image transport has now passed end-to-end acceptance through Runtime `workspace.content` and a fresh vision-capable Agent; the observed replay view earned a bounded `no-op`. Runtime/Host/MCP still own transport, Studio still owns model-view selection, and audio/continuous-playback transport remains future work only when a real unresolved production question requires it.

The exact visual direction, narration voice, motion language, footage treatment, and platform cut strategy remain design questions for the next review. The technical substrate should constrain them only where information would otherwise be lost.
