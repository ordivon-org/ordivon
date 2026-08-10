# Media model

Studio keeps a small set of objects because each answers a different irreversible question.

## Blob

A Blob is one exact byte sequence.

```json
{
  "digest": "sha256:<hex>",
  "sizeBytes": 123,
  "mediaType": "video/x-matroska"
}
```

Digest keys are immutable. A Blob has no editorial meaning by itself.

## Asset

An Asset gives one or more Blobs a stable production role and provenance.

Important fields:

- semantic `id`;
- selected Blob and optional alternatives;
- origin: capture, human-created, generated, imported, rendered, or transformed;
- parent Asset IDs;
- technical facts obtained from inspection;
- rights and attribution;
- selected generation receipt when AI is materially involved.

An Asset can select a new Blob without pretending the old bytes never existed.

**Blob identity and Blob durability are separate facts.** A `selectedBlob.digest` proves which bytes were selected; it does not by itself prove those bytes still exist after a disposable render or Workspace disappears. A selected payload therefore needs one exact durable byte authority. For large/binary media that authority is normally the verified content-addressed byte store; for an exact Git-tracked text/code payload, Git itself may already be the durable byte authority. Do not duplicate every digested Output into media CAS merely for uniformity. The invariant is recoverability of the exact selected bytes, not one universal storage mechanism.

## Claim

A Claim binds public wording to one owning source revision.

It contains:

- source repository and exact commit;
- the bounded meaning Studio is allowed to express;
- an evidence target or executable demonstration;
- prohibited or misleading extensions;
- the productions that consume it.

Claims are production inputs, not new product authority.

## TimedText

TimedText is the internal source for narration alignment, subtitles, captions, chapters, and synchronized interactive text.

Each cue has:

- stable cue ID;
- language;
- start and end in integer time units;
- time base;
- text;
- optional speaker and semantic kind;
- translation or source-cue relationship;
- provisional or locked timing status.

WebVTT, SRT, ASS, transcript Markdown, and platform caption formats are derived outputs.

## Editorial source

A Production may have several editorial sources:

- Resolve project export or archive for proprietary NLE state;
- OTIO snapshot for open cut structure and markers;
- Remotion source for deterministic motion;
- MDX for article and interactive structure;
- audio stems and raw capture Assets.

No interchange file is assumed to preserve every editor-specific effect.

## Receipt

A Production may retain selected Receipts when the consequence of an execution, review, generation, or other external step matters to later work. `schemaVersion` and `kind` form the shared envelope; **kind-specific semantics remain owned by that receipt kind**. Runtime Demo Receipts therefore use the Runtime-specific schema and identity checks, while a Web review Receipt is not coerced into Runtime Job/Attempt fields merely because both are called Receipts.

A Receipt is evidence consumed by a Production, not a universal event schema or a new owner of the source system.

Human/expert calibration follows the same rule. Do not create a pending or ceremonial approval Receipt merely because a person could review an artifact. If an actual human-response judgment materially changes or closes a Production decision, retain only the consequential evidence needed to recover that decision: the exact reviewed artifact digest, the bounded question/claim being calibrated, the supplied judgment, and enough context to avoid treating one observation as universal taste authority. Until such a judgment exists, the Production/Cognition state may truthfully remain `review` without fabricating a human Receipt.

## Production

A Production ties claims, assets, editable sources, medium-applicable working state, and outputs together.

It declares:

- semantic production ID and title;
- source projects and revisions;
- editorial intent and audiences;
- only the technical working-profile fields the actual medium uses (for example frame rate/canvas/color/audio for video; no invented AV profile for semantic-text-only work);
- required Claims and Assets;
- planned or completed outputs;
- selected source files and external editor artifacts.

The Production manifest does not track every creative thought or temporary generation.

A Production may point to one lightweight `cognition` Markdown source when current creative judgment must be recoverable across Agent/session replacement. That record indexes the six-stage `FRAME → BIND → EXPRESS → RENDER → AUDIT → DECIDE` protocol plus scoped post-decision `LEARNING`; it does not duplicate Claims, Assets, Timeline state, or evidence. See [`production-cognition.md`](production-cognition.md).

## Output

An Output is a deterministic or manually approved delivery object derived from a Production.

Examples:

- YouTube 16:9 MP4;
- Douyin 9:16 MP4;
- Web article package;
- Upwork cover and project film;
- WebVTT caption track;
- audio-only master.

Every published Output records its Blob digest and source Production revision. Its exact bytes must also remain recoverable from the appropriate durable authority for that medium: source control for an exact canonical text/code artifact, or a verified byte/object store for payloads intentionally kept outside Git.

## Canonical versus generated

```text
canonical in Git
  DTCG token source
  production manifest
  claims
  selected Asset records
  TimedText source
  MDX and code
  OTIO snapshots

canonical outside Git
  immutable raw and selected media Blobs
  Resolve/Figma and other binary editable masters at named milestones

generated
  CSS and TypeScript tokens
  WebVTT, SRT, ASS
  proxies
  thumbnails
  delivery encodes
  indexes and search databases
```
