# Ordivon Root Social Card — production cognition

Status: active production decision record
Protocol: [`../../research/expression/protocol.md`](../../research/expression/protocol.md)

This is **not a second Production manifest**. It records only the current visual decision frontier while `production.json`, `claims.json`, `assets.json`, exact image bytes, and the bound Web revision retain factual/physical authority.

## FRAME

**Viewer model.** A link-preview reader gets roughly one glance at a reduced 1.90:1 image. The card must establish `ORDIVON` and `Durable work for AI agents` before any supporting detail. It is a social preview, not a miniature `/system` page.

**Observed baseline problem.** Web's current `public/opengraph-image.png` is valid 1200×630 PNG bytes, but direct visual inspection at the exact image shows the identity/copy occupying a very small fraction of the canvas. The default social surface therefore spends most of its limited perceptual budget on empty space. This is an Agent perceptual judgment, not a source Claim.

## BIND

Owner authority is Ordivon Web revision `e832fbc0b8798bbcacc7e744a608439ef4ab1fb4`. `claims.json` binds the social surface, public durable-work position, and current design-token palette. The existing Web root image baseline is `sha256:f07ede4ed1d6e9b4b82eea4411308481e6658157d67a4cdaf76debded9d64f3`.

The card may visually suggest continuity across model/process/provider changes, but it must not imply that every Ordivon project is required to traverse one Host→Harness→Runtime stack.

## EXPRESS

Use current Web visual language rather than the older green-led root card: dark ink canvas, paper foreground, purple accent, restrained success green. Make the headline the dominant object. Keep the continuity motif secondary and abstract enough to support the mission instead of becoming architecture documentation.

At reduced preview scale, secondary labels may disappear before the brand/headline does; that degradation is acceptable. Brand and headline must not.

## RENDER

Editable source: `source/opengraph-image.svg`.
Selected candidate: `output/opengraph-image.png`.
Canvas: 1200×630.
Renderer: `rsvg-convert --width 1200 --height 630`.

No frame rate, audio, TimedText, Resolve/OTIO, CAS, or R2 is selected by this Production. Git-tracked SVG/PNG bytes are sufficient for the current local Studio/Web durability boundary unless a later distribution/recovery requirement proves otherwise.

## AUDIT

Required checks before approval:

- PNG decodes as exactly 1200×630;
- selected Output digest matches the PNG Asset digest;
- all Claim source paths exist at the bound Web revision;
- `ORDIVON` and `Durable work for AI agents` remain legible in a real browser at 600×315 and 400×210 preview sizes;
- no text clips or crosses the safe outer frame;
- the continuity motif remains secondary to the headline;
- direct Web consumption can replace only `public/opengraph-image.png` without changing metadata authority or page pixels.

## DECIDE

Current decision: **Output approved; Production remains review.** The exact PNG `sha256:9a67bb6fc7f27c754556e090d52ebd41b1bd91e35ff062e5bd1215a1e0176807` is 1200×630 and matches the selected Asset digest. Direct full-resolution inspection and real Chromium previews at 600×315 and 400×210 preserve `ORDIVON`, `DURABLE WORK FOR AI AGENTS`, and the supporting durable-work statement. Under the same browser-preview conditions, the previous Web root card `sha256:f07ede4ed1d6e9b4b82eea4411308481e6658157d67a4cdaf76debded9d64f3d` collapses its identity/copy into a tiny corner treatment. V1 therefore resolves the bounded social-preview legibility defect without requiring a second architecture diagram.

Web has now deliberately consumed these exact bytes in local commit `9d7cb2cb521d5a3934176809baafff1f01e9003a`: its only product change is `public/opengraph-image.png`, whose digest remains `sha256:9a67bb6fc7f27c754556e090d52ebd41b1bd91e35ff062e5bd1215a1e0176807`. Web-side Chromium previews at 600×315 and 400×210 are byte-identical to Studio's approved previews (`sha256:bf03fd142a92c60f0020bca66bc970de15305a7e31abfea57d1dceadb15039d1` and `sha256:d0293d50c64eddae5f59ad0ebb0c38d1d0f43816b75547999b592da31a56d1bb`). The Output is therefore accepted by its local Web consumer, but the Production remains `review` because no remote/public deployment has occurred.

## LEARNING

P1–C4 already reduced this Production's path materially: `workingProfile` needed only `canvas`; the Output used a real Asset manifest because binary image identities mattered; cognition stayed a short current frontier; no preference ballot was needed because the defect was task legibility rather than comparative taste; and Resolve/OTIO, TimedText, CAS, and R2 were never invoked.

Two retained priors recurred without creating new laws: real rendered pixels—not source validity—decided the defect, and exact selected bytes need a durable authority. The latter is satisfied here by tracked SVG/PNG Git bytes once committed, so universal CAS/R2 remains unjustified.
