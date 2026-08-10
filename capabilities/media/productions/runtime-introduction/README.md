# Runtime introduction

This is the first real Ordivon Studio production and the acceptance case for the Studio architecture.

## Bound source

Current product facts and executable evidence are bound in `production.json` to:

```text
ordivon-runtime
5dd206c74a2b9151fb0a87579ba2200aaf892633
```

`claims.json` limits what the production may say about that binding. Studio does not become a second Runtime authority.

## Current sources

- [`cognition.md`](cognition.md) — current FRAME/BIND/EXPRESS/RENDER/AUDIT/DECIDE/LEARNING judgment;
- [`plan.md`](plan.md) — proof and film construction;
- `claims.json` — bounded Runtime claims;
- `story.mdx` — editable editorial source;
- `script/narration.en.md` — English narration text locked to the 78-second picture;
- `timed-text/narration.en.json` — nine locked cues covering 0–78 seconds;
- `evidence/runtime-demo.receipt.json` — fresh selected live MCP proof, digest `sha256:c612500db2312fc956e0b9dc801853aab3ae31f7f182f3cce6a7649c02ccdbe1`;
- `assets.json` — selected media identities, including the current picture master and historical v0 placeholder assets;
- `timeline/assembly.v1.otio` — active placeholder-free picture-master snapshot;
- `timeline/assembly.v0.otio` — historical placeholder assembly;
- `../../apps/motion-remotion/` — editable deterministic motion source.

## Current proof

The first film proves one trajectory rather than enumerating Runtime features:

```text
exact source
→ guarded Patch
→ durable Job + recorded Attempt
→ observe bounded progress
→ replay exact request identity and recover the same recorded Job
→ inspect bounded evidence and one-path diff
→ compare-and-close the exact reviewed Workspace state
```

The selected live Receipt re-proved that trajectory against the installed Runtime service. It does **not** turn Job replay identity into a claim that every external effect is idempotent, and it does not establish semantic Task completion.

## Picture master

The active 16:9 picture master is now real rather than a placeholder skeleton:

```text
Asset: runtime-introduction-master-motion
Blob: sha256:56276cf3fb25fb42f1174f1ed2f2fc209090502a0b3b3dda1adc59cb527cb535
Duration: 78.000 s / 2340 frames
Video: 1920×1080 · 30 fps · H.264 · yuv420p · complete BT.709
Audio: intentionally absent at this review stage
```

The master uses deterministic motion plus clearly labeled receipt-derived evidence views. It does not fabricate a terminal recording. A first full render/pixel audit caught and corrected one provenance-label defect where Studio framing had been mislabeled as receipt-derived evidence.

## Current output decision

`runtime-film-en-landscape` is now `rendered` and the Production is in `review`. It is **not approved or published**.

The remaining gate is concrete and medium-specific:

- produce/select narration audio from the locked English text/timing;
- register the selected audio Asset;
- continuously playback-audit the combined 78-second master for pacing, readability and audio-image implication;
- run final delivery QC;
- decide approve/revise.

The Chinese short, article, interactive, and Upwork package remain planned. They should not be mechanically generated merely because the landscape picture master exists.
