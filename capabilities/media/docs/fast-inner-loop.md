# Fast inner loop

## Purpose

Studio should make bounded creative iteration cheap enough that an Agent can revise from real artifacts rather than from source-code intuition alone.

C4 establishes the first narrow loop for programmatic motion:

```text
bounded source revision
        ↓
supported render entrypoint
        ↓
real video artifact
        ↓
technical QC + exact keyframes + source digests
        ↓
Agent semantic / expressive inspection
        ↓
revise / no-op / promote
```

This is not a workflow engine. Runtime still owns durable execution, process supervision and execution evidence. Studio owns what constitutes useful creative render/review evidence for a medium.

## Mechanical preconditions should not live in Agent memory

The first real C4 run exposed two hidden prerequisites:

1. Remotion attempted to acquire a browser from the network when no browser executable was declared;
2. a fresh Workspace lacked generated identity token outputs required by `@ordivon/identity/tokens.css`.

Both are mechanical facts, not creative judgment. Supported Studio motion entrypoints now build identity tokens before rendering, and Remotion resolves an already provisioned local Chrome/Chromium executable before it considers any network download. Browser download is opt-in through `ORDIVON_REMOTION_ALLOW_BROWSER_DOWNLOAD=1`; an exact local path may be supplied with `ORDIVON_REMOTION_BROWSER`.

A repeated render exposed a third hidden assumption: Remotion could emit H.264 with the BT.709 matrix/range present but transfer and primaries absent. The supported entrypoint therefore applies `h264_metadata` as a stream-copy normalization step before review/QC. No picture re-encode is performed; Studio owns the complete media signalling contract rather than trusting a renderer's incidental VUI output.

The principle is broader than Remotion:

> If a repeatable creative operation has a deterministic machine precondition, satisfy it automatically or fail fast with the missing dependency. Do not make an Agent remember ritual setup steps between iterations.

## Review packet

`ordivon-studio review-video` builds **disposable review evidence** for one rendered Production video. It currently records:

- Production and cognition source references;
- rendered video Blob identity;
- normalized ffprobe facts;
- structural video QC result;
- materially responsible source-file Blob identities;
- exact requested keyframe indices, PNG paths and Blob identities;
- Production/Cognition/Claim decision-context paths plus Blob identities;
- semantic-audit status.

Review output belongs under ignored working directories such as `out/reviews/`. It is not automatically registered as an Asset, Production Output, Claim, Receipt, or durable research result.

## Fact / judgment boundary

The packet deliberately ends at:

```text
semanticAudit.status = pending-agent-inspection
```

Technical QC can prove dimensions, frame rate, codec, pixel format, color signalling, audio-stream expectations and exact artifact identity. Exact keyframes can prove which pixels were selected for review. Neither proves that the sequence is clear, truthful, beautiful, persuasive, suspenseful, trustworthy, or otherwise aesthetically correct.

An Agent must still inspect the artifact against the Production cognition and relevant medium profiles. Human/expert calibration remains conditional on a residual human-response claim, exactly as in the shared Expression Protocol.

## First acceptance case

The first C4 change tightened one sentence in `runtime-request-replay`:

```text
old:
No silent redispatch. The recorded identity survives the client interaction.

new:
Exact replay returns the recorded Job. It does not admit a second Job.
```

The change was motivated by the Runtime Claim boundary: the film should describe exact replay/admission identity without inviting a stronger interpretation about universal external-effect idempotency.

The first loop failed before rendering because the browser dependency silently required network access. A second attempt with a local browser reached bundling and exposed the missing generated token dependency. After the browser and token preconditions became explicit, the supported loop completed locally:

```text
pnpm motion:loop:replay
```

A later repeat then falsified one more assumption: raw renderer output did not always preserve complete H.264 BT.709 VUI signalling. Studio added a stream-copy metadata normalization boundary and repeated the complete loop twice. Both repetitions produced the same final MP4 digest and the same five keyframe digests, passed complete BT.709 structural QC, and emitted a review packet bound to the composition source and selected Runtime Receipt.

Those failures are part of the C4 result: accelerating the inner loop means removing hidden setup, network dependence, and renderer-specific metadata drift—not merely making the renderer faster.

## What C4 does not establish

C4 does not establish:

- autonomous aesthetic correctness;
- automatic promotion after QC;
- a generic cross-medium review schema;
- persistent review history for every iteration;
- a new execution scheduler;
- mandatory keyframe counts or locations for all video work.

The current packet is deliberately video-specific and disposable. Other media should earn their own observation bundle from real production pressure.
