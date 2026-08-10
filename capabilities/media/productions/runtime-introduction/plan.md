# Runtime introduction production plan

This plan is derived from the Runtime implementation bound in `production.json` and from the media actually materialized during production.

## The one proof

> After delivery becomes uncertain, one admitted operation retains a stable recorded Job identity, can be recovered without blindly admitting a second Job, exposes bounded execution evidence, and can close only the exact Workspace state that was reviewed.

The selected Runtime proof remains `evidence/runtime-demo.receipt.json`, digest `sha256:c612500db2312fc956e0b9dc801853aab3ae31f7f182f3cce6a7649c02ccdbe1`.

## Presentation boundary

Runtime's product surface is MCP/service execution rather than a presentation CLI. The film therefore uses clearly labeled receipt-derived evidence views plus deterministic explanatory motion. It does not stage a fake terminal recording.

## Current 78-second picture

| Time | Image responsibility |
| --- | --- |
| 0–6 s | uncertain-delivery hook |
| 6–13 s | RuntimeFlow |
| 13–24 s | exact source + guarded Patch evidence view |
| 24–37 s | Job/Attempt + observation evidence view |
| 37–43 s | exact request replay motion |
| 43–48 s | same recorded Job recovery evidence view |
| 48–59 s | bounded terminal evidence |
| 59–65 s | exact reviewed-state close motion |
| 65–67 s | one-path diff |
| 67–74 s | Runtime boundary framing |
| 74–78 s | end statement |

The current picture Blob is `sha256:77d8eae832a3cac47c641211aa8c9019c04c542faf0ae87a9ae0e82d37acc736`.

## Voice materialization

English narration is generated from `timed-text/narration.en.json` through the bounded workstation adapter:

```text
scripts/build_sapi_narration.py
→ scripts/synthesize-sapi-cues.ps1
→ Windows System.Speech
→ Microsoft Zira Desktop · rate 1
→ cue-fit validation
→ 48 kHz mono PCM 24-bit 78-second stem
```

A repeated full build produced exact byte equality:

```text
sha256:798c8f90f9eeb90d6407d78329e88e71dab6d4aa5d38831568c7e14f445d828d
```

Real voice duration changed the previous editorial plan. The old Boundary and End slots were too short at the selected consistent rate. The final narration tail is therefore:

```text
59–67  source effect + compare-and-close
67–74  Runtime boundary
74–78  recover the same work / inspect the evidence
```

The tightest selected cue occupies `6.927937s` of a `7.0s` slot. No cue exceeds its interval.

## A/V candidate

The picture stream is muxed without re-encoding with AAC 48 kHz mono narration. Two independent muxes produced the same exact bytes:

```text
sha256:7d994f80627968f4e64a3a53c08d5241bb8f398e17d52c24080f935e7c716430
```

The candidate is exactly 78.000 seconds. Video remains 1920×1080 / 30 fps / H.264 / yuv420p / complete BT.709. Audio measures `-20.5 LUFS` integrated loudness and `-2.2 dBFS` true peak.

`timeline/assembly.v2.otio` is the active picture+narration review snapshot.

## Selected-byte durability and recovery gate

A committed Asset digest is not enough if its selected bytes disappear with a disposable Workspace. For selected media whose canonical payload is outside Git, Studio uses a symmetric local pair:

```bash
uv run ordivon-studio archive <path> --cache-root /mnt/d/OrdivonStudio/cache
uv run ordivon-studio materialize <sha256:digest> <working-path> --cache-root /mnt/d/OrdivonStudio/cache
```

`archive` verifies and admits immutable cache bytes without overwrite. `materialize` verifies the requested cache object before copying, verifies the working copy, and never overwrites different destination bytes. Picture, narration stem, and final A/V candidate passed the archive side in P2; P3 then recovered the final A/V candidate from a fresh Workspace after the P2 Workspace was gone. First recovery created the working copy, exact replay converged to the existing bytes, and a conflicting destination failed closed.

## Current acceptance

Established:

- current Runtime claim/proof binding;
- exact picture bytes and complete video/color QC;
- exact narration bytes, deterministic repeated synthesis, cue fit, sample format, loudness and peak;
- exact deterministic repeated A/V mux;
- durable local content-addressed copies of all selected media plus exact fresh-Workspace recovery of the final candidate through `materialize`;
- cue-bound visual review showing proof phases in the same semantic order as narration;
- focused 65–78 second inspection confirming Diff → Boundary → End under the revised edit.

Not established:

- whether the selected synthetic voice sounds natural, appropriately paced, or publication-worthy to human listeners.

Therefore the film remains `rendered / review`. Approval now requires only a bounded audition of the exact current candidate; it does not justify another workflow framework or architecture layer.
