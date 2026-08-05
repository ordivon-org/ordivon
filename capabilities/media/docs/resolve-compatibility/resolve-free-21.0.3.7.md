# DaVinci Resolve Free 21.0.3.7 compatibility profile

This profile records behavior observed on the installed Windows build of **DaVinci Resolve Free 21.0.3.7**, executed through an internal Workspace menu script. It is version-specific evidence, not a claim about other Resolve versions, Resolve Studio, macOS, or Linux.

The machine-readable profile is [`resolve-free-21.0.3.7.json`](resolve-free-21.0.3.7.json).

## Test boundary

The probe used one disposable Resolve project, one 1920×1080 H.264/AAC fixture at 30 fps and 90 frames, and one OTIO timeline containing:

```text
24-frame clip
→ 6-frame gap
→ 30-frame clip
```

The operation was bound to the exact installed Developer Package README, media fixture, and OTIO document by SHA-256. It restored the previously open project and deleted the disposable project after all cases completed.

## Verified results

All six cases completed:

| Case | Result |
|---|---|
| `AppendToTimeline(clip)` | 90-frame item at timeline offset 0 |
| `AppendToTimeline([clip])` | 90-frame item at timeline offset 0 |
| positioned full-media append | 90-frame item at requested offset 30 |
| append source range `0…23` | item duration reported as 23, despite the installed example describing 24 frames |
| OTIO with existing Media Pool source | 24-frame clip, 6-frame gap, 30-frame clip; total 60 |
| OTIO with `sourceClipsPath` import | same 24 + 6 + 30 layout; total 60 |

Returned TimelineItem handles carried usable unique IDs and matched items recovered by scanning V1. MediaPoolItem unique IDs and media IDs were also available.

## Time semantics

For timeline placement in this build:

```text
TimelineItem.GetDuration()
=
TimelineItem.GetEnd() - TimelineItem.GetStart()
```

`GetEnd()` is therefore an **exclusive timeline boundary**. It must not receive `+1`.

Source boundaries are route-dependent:

- full-media Append reported source `0…89` for a 90-frame item, behaving like an inclusive source end;
- OTIO import reported source `0…24` for a 24-frame item and `24…54` for a 30-frame item, behaving like an exclusive source end;
- source-range Append `0…23` produced only 23 timeline frames.

These APIs do not share one universal source-end convention. Ordivon Studio must not infer duration from `GetSourceEndFrame()` without considering the operation route.

## Production decision

The supported Runtime Introduction assembly path for this profile is:

```text
Production Manifest + selected Assets + canonical OTIO
→ compile a Resolve-facing OTIO with local media references
→ preimport verified media into controlled Bins
→ ImportTimelineFromFile(..., importSourceClips=False, sourceClipsFolders=[...])
→ scan and verify the resulting Timeline
```

Manual full-media Append remains useful as a diagnostic. Append with explicit source `startFrame/endFrame` is excluded from production assembly on this profile.

A future Resolve update must run the compatibility probe again before reusing this profile.

## Full Assembly v0 acceptance

The version-level OTIO probe was followed by a full 11-clip Runtime Introduction conform acceptance. Resolve preserved every requested start and duration, produced a 2340-frame Timeline with no extra or missing items, restored the prior project, and deleted the disposable test project.

The normalized result is [`runtime-introduction-assembly-conform-21.0.3.7.json`](runtime-introduction-assembly-conform-21.0.3.7.json). This upgrades native OTIO conform from a small compatibility result to an accepted real-production assembly path for this profile.
