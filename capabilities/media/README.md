# Ordivon Media

Ordivon Media owns **structured mediation** across Ordivon: how source-owned realities, descriptions, states and actions become representable, composable, transformable, exposable and interactable for human and Agent observers without becoming a second truth authority.

The project Constitution is [`MEDIA.md`](MEDIA.md); canonical Media research starts at [`research/media/`](research/media/README.md). **Ordivon Studio is retained inside this project as the authoring and production capability plane.** Existing `ordivon-studio` CLI/package/tool identities remain Studio capability names rather than repository-owner names.

## Studio capability plane

A Runtime fact is true at revision `R`. Studio turns it into a film. Runtime later changes.

The film still expresses what was bound at `R`; it does **not** become the current Runtime authority because it is polished, approved, or published.

**Ordivon Studio turns source-owned reality into editable medium-specific expression without creating a second truth store.**

```text
exact owner revision + bounded Claim
→ editable writing / visual / audio / motion / interaction source
→ selected Assets and exact bytes
→ render or composition
→ factual/mechanical review
→ medium craft judgment
→ human-response calibration only when the claim requires it
→ Output / publication package
```

## Purpose

Facts and code do not decide how a reader should encounter them. Studio owns the remaining creative responsibility: medium choice, narrative structure, editable production state, selected expression, rendering, review preparation, and replaceable delivery variants.

The source owner keeps current product/research truth. Studio keeps the expression bound to the exact source revision.

## One expression journey

For a video explaining Runtime recovery:

1. Runtime owns the fact and evidence.
2. Studio binds an exact Runtime revision through a Claim that limits what may be said.
3. Studio chooses narration, diagrams, pacing, typography, motion, sound, and edit structure.
4. Render evidence proves what artifact was observed; decision context proves which Claim/Production boundary governed review.
5. An Agent may revise or no-op; intermediate critique is transient unless its consequence matters later.
6. A later Runtime change does not silently float the old Claim. Studio keeps a historical expression or explicitly rebases it.

## Responsibility boundary

| Responsibility | Owner |
| --- | --- |
| current product/research fact | source repository/native owner |
| revision-bound allowed expression | Studio Claim |
| creative intent and editable production state | Studio |
| exact selected bytes | the named durable byte authority for that medium |
| render/QC evidence | Studio tooling and retained receipts |
| public site orientation/publication | Web or destination platform |
| human comprehension, preference, trust, recall, or other audience response | scoped human-response evidence |

Persisting or presenting another owner's fact does not transfer that fact to Studio.

## Human-response boundary

Studio separates three claims:

```text
mechanical / factual → verify against source, bytes and render evidence
medium craft         → conventions + explicit intent + bounded critique
human experience     → human/expert evidence when uncertainty matters
```

A vision-capable Agent can falsify obvious semantic or visual problems. It cannot establish that people understood, preferred, trusted, remembered, or enjoyed the work. One person's preference is not universal taste authority either.

This is why a Production may remain in `review` after technical, factual, storage, and Agent-perception checks pass when the unresolved decision is genuinely human-response dependent.

## Current boundary

Studio currently retains:

- the cross-medium identity source and Art & Expression Laboratory;
- Production, Claim, Asset/Blob, TimedText, Receipt, and Output contracts;
- editable production sources and reusable expression primitives;
- provenance/rights records for selected Assets;
- deterministic media inspection, rendering, QC, review preparation, and selected-byte recovery;
- optional Resolve/OTIO equipment behind explicit compatibility checks;
- real motion and Writing-only Productions that pressure-test the model.

Large media bytes, caches, proxies, and exports stay outside Git. Git stores identities, manifests, editable text/code, provenance, interchange snapshots, and checksums. Exact selected bytes use the durable authority appropriate to their medium and failure boundary; Git itself may already be sufficient for canonical tracked text/code.

Current production status and storage evidence remain in the production and technical documents rather than this entry page.

## Start here

| Need | Read / invoke |
| --- | --- |
| inspect one Production, its Claims/Outputs, and optional source-binding Git relation without rendering or editing | `uv run ordivon-studio production-context <production-root> [--source-repo BINDING_ID=PATH]` |
| understand the Media owner contract | [`MEDIA.md`](MEDIA.md) |
| inspect Phase-1 closure / freeze / reopen posture | [`docs/media-phase1-construction-audit.md`](docs/media-phase1-construction-audit.md) |
| understand why Studio exists | this README |
| determine document/fact/evidence authority | [`docs/authority.md`](docs/authority.md) |
| first-principles architecture and technical choices | [`STUDIO.md`](STUDIO.md) |
| Production/Claim/Asset/Blob/Output model | [`docs/media-model.md`](docs/media-model.md) |
| Agent review consumption and transient critique | [`docs/review-consumption.md`](docs/review-consumption.md) |
| perception/model-view preparation | [`docs/artifact-perception.md`](docs/artifact-perception.md) |
| Art & Expression research | [`research/expression/README.md`](research/expression/README.md) |
| local render/review loop | [`docs/fast-inner-loop.md`](docs/fast-inner-loop.md) |
| storage/recovery boundaries | [`docs/storage-layout.md`](docs/storage-layout.md) |

## Fresh Workspace bootstrap

```bash
pnpm bootstrap
pnpm check
```

Resolve is optional equipment:

```bash
pnpm check:equipment:resolve
```

## License

Apache-2.0. Production assets may carry their own rights and usage records in Asset metadata.
