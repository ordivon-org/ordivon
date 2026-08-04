# Runtime introduction

This is the first real Ordivon Studio production and the acceptance case for the Studio architecture.

## Bound source

Product facts and executable evidence are bound to:

```text
ordivon-runtime
d620d7ce71ae76140cf88b570c141edd777ec91c
```

`production.json` owns that binding once. `claims.json` references it through the `runtime` binding ID and limits what the production may say.

## Current sources

- [`plan.md`](plan.md) — code-derived demonstration and film design;
- `claims.json` — five bounded Runtime claims with exact evidence paths;
- `story.mdx` — editorial source, not final publication copy;
- `script/` — English and Chinese narration drafts;
- `timed-text/` — provisional internal cue timing;
- `assets.json` — selected media assets; currently empty because real capture has not started;
- `timeline/` — future OTIO snapshots after editorial work begins;
- `../../apps/motion-remotion/` — verified programmatic Runtime motion source.

## Chosen proof

The first film will not enumerate every Runtime feature. It will prove one complete trajectory:

```text
exact source
→ guarded Patch
→ durable Job
→ recover the same Job after uncertain delivery
→ read bounded evidence and review the diff
→ compare-and-close the exact reviewed Workspace state
```

The executable demonstration belongs in `ordivon-runtime`; Studio owns the story, motion, capture selection, edit and delivery variants.

## Verified now

The shared Runtime flow renders as a seven-second 1920×1080, 30 fps H.264 component. Machine QC requires `yuv420p`, limited range, BT.709 matrix/transfer/primaries, and no audio stream.

This proves the code, token, render, and QC path. It does not prove the final visual direction or the complete film.

## Decisions still open

The next implementation should build and verify the bounded Runtime demo client described in `plan.md`. After it produces a real redacted receipt, Studio can decide the final visual treatment, narration voice, capture tooling, editorial pacing and asset-storage configuration from actual footage rather than assumptions.
