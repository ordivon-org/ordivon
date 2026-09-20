# Editorial timeline

[`assembly.v0.otio`](assembly.v0.otio) is the first selected Runtime Introduction editorial snapshot.

## Assembly v0

```text
11 V1 clips
2340 frames
78 seconds at 30 fps
01:00:00:00 start timecode
3 selected motion anchors
8 explicit replacement placeholders
```

The sequence is:

1. hook placeholder — 180 frames;
2. Runtime flow motion — 210 frames;
3. source patch placeholder — 330 frames;
4. execution and observation placeholder — 390 frames;
5. request replay motion — 180 frames;
6. replay terminal placeholder — 150 frames;
7. evidence placeholder — 330 frames;
8. exact-close motion — 180 frames;
9. diff placeholder — 90 frames;
10. boundary placeholder — 210 frames;
11. end placeholder — 90 frames.

This snapshot is an **assembly review skeleton**, not picture lock and not a final cut. Placeholder clips deliberately reserve editorial duration and identify the real OBS or product evidence that must replace them.

The canonical OTIO references Assets by Ordivon identity. The Resolve adapter compiles a local Resolve-facing OTIO with verified media references; that compiled file is ephemeral and is not a second Production authority.

DaVinci Resolve Free 21.0.3.7 native OTIO import has been verified to preserve clip durations, gaps, record positions, and timeline start timecode. Explicit `AppendToTimeline` source ranges are excluded from the production path for this version.

Future milestones may add:

```text
picture-lock.otio
publication-master.otio
```

Resolve project exports or archives remain binary Assets outside Git. OTIO does not promise to preserve every Resolve title, effect, color node, Fairlight process, or generator.

## Resolve acceptance

A disposable Resolve Free 21.0.3.7 project imported a locally compiled form of this OTIO and reproduced all eleven clips exactly. Start positions, durations, media identities, timeline start timecode, and the 2340-frame total were verified through the scripting API. The probe restored the previously open project and deleted itself afterward.

Assembly v0 is therefore no longer only a repository model: its native Resolve conform path has passed real execution. It remains an editorial review skeleton because eight visual placeholders still require replacement with real product evidence.
