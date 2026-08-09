# Artifact perception

## Purpose

C6 moves Studio review from “a render exists” toward “a vision-capable Agent can receive a compact, source-bound view of the real rendered artifact.” The objective is not to replace vision with image metrics. It is to prepare the right real pixels, in the right temporal context, with enough identity to support a later semantic judgment.

```text
real video
   ↓
mechanical temporal observation
   ↓
model-view preparation
   ↓
vision-capable Agent
   ↓
semantic / expressive audit
```

## Three layers

### L1 — mechanical observation

Studio may mechanically establish facts such as:

- exact frame/time identity;
- image Blob identity;
- video duration/frame count;
- sampled pixel change between moments;
- contact-sheet layout and frame order.

These facts help decide **where to look**. They do not establish what the work means.

### L2 — model-view preparation

The current video bundle provides a progressive observation surface:

1. **coarse temporal scan** — one ordered contact sheet;
2. **full-resolution frame inspection** — the exact selected PNG frames;
3. **continuous playback** — the original video when timing, pacing, continuity, animation, or audio/image relation remains material.

The contact sheet is a lossy observation view, not a new master. The original video and exact full-resolution frames remain the perceptual evidence behind it.

### L3 — semantic interpretation

Only a vision-capable Agent or other suitable observer should infer questions such as:

- what is visually dominant;
- whether hierarchy is legible;
- whether position implies location or causality;
- whether color implies trust, severity or outcome;
- whether typography is readable;
- whether the sequence feels continuous, abrupt, suspenseful or flat;
- whether an image contradicts the Claim/Focalization boundary.

Mechanical diagnostics must not silently answer these questions.

## Sampling strategy

Hard-cut scene detection was tested against `runtime-request-replay` and rejected as the primary mechanism. The composition uses gradual entrances, lines, reconnect motion and confirmation fades; its FFmpeg scene scores are therefore near zero even when meaningful visual events occur.

C6 instead combines two signals:

```text
coverage sampling
+ temporal change peaks
```

Coverage protects stable but important states such as the opening and final resolved frame. Temporal change peaks find moments where many pixels change between sampled intervals. Neither signal claims that a frame is artistically or semantically important.

The current temporal diagnostic samples every five source frames, constructs a difference image between sampled moments, and uses its mean luma value only for ranking candidate observation moments. Nearby peaks are de-duplicated so one animated entrance does not consume the whole model-view budget.

For the first 180-frame acceptance artifact, automatic selection yielded:

```text
0, 10, 35, 60, 70, 119, 130, 179
```

The set includes opening/final stable states and multiple change peaks without requiring a manually maintained frame list.

## Observation packet

`review-video` now carries one `perception` object rather than a parallel manually-curated `keyframes` surface. The perception bundle contains:

- strategy and frame-rate/frame-count facts;
- the temporal change metric and selected peaks;
- exact selected full-resolution PNG frames with selection reasons and Blob identities;
- one ordered temporal contact sheet with Blob identity and layout;
- a progressive inspection sequence;
- an explicit interpretation boundary.

Manual frame numbers remain optional semantic anchors. They augment automatic perception; they no longer replace it.

## Transport boundary

Studio can decide **which pixels should be available to perception** and can materialize those model views. It should not own the final transport into a model runtime.

The first C6 acceptance exposed a concrete boundary in the WSL MCP surface available at that time: a generated JPEG/PNG could be hashed and Base64-encoded into a text Job Artifact, but the tool surface could not present an arbitrary Workspace image as native `image/jpeg` / `image/png` model content. That experiment remains the historical evidence that motivated the cross-project requirement; Base64 text is not an acceptable long-term perception transport.

As of Runtime source revision `66b87a90d1701c5f04aa42b327024e6aeecc8fb3`, that source-level gap is implemented by generic `workspace.content`: Runtime binds the read to an opened Workspace-confined file descriptor, bounds the bytes, verifies the caller-selected SHA-256 digest and PNG/JPEG signature, and projects the result as native MCP image content. Production deployment and a fresh vision-capable Agent consuming the image remain separate acceptance boundaries; Studio therefore does not claim that the current production MCP session has already delivered these pixels to a model.

The cross-project requirement is therefore:

```text
Studio
  model-view path + MIME + exact Blob bytes
        ↓
Runtime / Host / MCP transport
  preserve MIME and bytes as native model input
        ↓
vision-capable Agent
```

This belongs with Agent transport / artifact exposure, not with aesthetic reasoning. Studio should not embed image Base64 in review JSON or introduce a private vision API merely to bypass that boundary.

The cross-project continuation is registered in Host as `task:studio:c6-native-model-view-transport-20260809` under `goal:agent-perception:native-media-transport`, so Runtime/Host work can resume from the exact requirement without making Studio own the transport implementation.

## Why progressive perception matters

Sending every frame at full resolution is wasteful and can reduce rather than improve Agent judgment. Conversely, reducing a six-second sequence to one attractive frame destroys temporal meaning.

The intended Agent-first path is therefore adaptive:

```text
contact sheet
→ identify uncertain region
→ exact full-resolution frame(s)
→ short/full playback only if temporal meaning remains unresolved
```

Future media may use analogous shapes: waveform/segment overview → exact audio windows → playback; page overview → exact crop → interactive browser state.

## What C6 does not establish

C6 does not establish:

- visual aesthetic correctness;
- OCR as a universal proxy for legibility;
- scene-score importance;
- a universal image embedding or CV stack;
- that contact sheets can replace playback;
- that the currently deployed production MCP session already supplies the Runtime source-level native image capability to a fresh vision-capable Agent;
- that every medium should share the video perception representation.

The accepted result is narrower: **Studio can deterministically compile a real time-based artifact into a bounded, progressive model-view surface while keeping mechanical sampling separate from semantic interpretation.**
