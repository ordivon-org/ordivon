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

- `claims.json` — five bounded Runtime claims with exact evidence paths;
- `story.mdx` — editorial source, not final publication copy;
- `script/` — English and Chinese narration drafts;
- `timed-text/` — provisional internal cue timing;
- `assets.json` — selected media assets; currently empty because real capture has not started;
- `timeline/` — future OTIO snapshots after editorial work begins;
- `../../apps/motion-remotion/` — verified programmatic Runtime motion source.

## Verified now

The shared Runtime flow renders as a seven-second 1920×1080, 30 fps H.264 component. Machine QC requires `yuv420p`, limited range, BT.709 matrix/transfer/primaries, and no audio stream.

This proves the code, token, render, and QC path. It does not prove the final visual direction or the complete film.

## Decisions still open

The next production review should decide:

- the Runtime demonstration journey and capture runner;
- visual identity beyond the current Web-derived baseline;
- narration voice and language treatment;
- final film structure and pacing;
- how much motion is programmatic versus NLE-edited;
- Windows media-root layout and R2 archival configuration;
- whether Resolve, OBS, and Figma remain the best tools after a real workflow test.
