# Provider-First Studio Equipment — PF0

Status: equipment-boundary synthesis — 2026-08-14

## Conclusion

Studio is substantially Provider-First. E0–E7 established the original equipment economics; E8 adds a necessary complement: a mature provider can also deserve proactive admission when it exposes a genuinely new medium-native world or durable editable state that Studio otherwise cannot observe or act on.

The current direction is therefore **bounded provider consumption + normalization**: admit a new world through real dogfood, then make its authority/lifecycle/friction legible to Agents instead of growing a parallel Studio engine.

## Existing resource states

Based on `research/equipment/evidence/e0-e7-20260813.json`:

### PROVEN / retained core equipment

- FFmpeg / ffprobe;
- rsvg-convert;
- Typst;
- ImageMagick.

These have real cross-equipment production evidence.

### PROVEN specialist-on-demand

- Godot;
- Blender 5.2 LTS portable;
- REAPER 7.78 portable.

Godot preserves a real non-Web application/game/input/export/XR ceiling. Blender now adds native spatial scene/camera/light/material/geometry state. REAPER adds scriptable multitrack/item/mix project state. None should become ambient core when the task is cheaper in Python/FFmpeg/2D tooling.

### External professional equipment retained

- DaVinci Resolve Studio;
- OBS Studio, default-off.

Resolve has real OTIO conform/editable-master production evidence. OBS now has bounded authenticated scene observe/mutate/cleanup evidence and is retained as a Live state/action world, while its WebSocket listener remains disabled by default.

### MATERIALIZED but user authority still pending

- Figma.

Figma is installed and the official Remote MCP endpoint is configured locally, but OAuth consent has not yet been granted. No MCP design read/write is claimed until that human authority boundary is crossed and a real round succeeds.

### Candidate / not materialized

- Inkscape;
- TouchDesigner.

Inkscape currently adds low incremental information beyond raw SVG/rsvg + the pending Figma design world. TouchDesigner would add a real realtime operator/dataflow/OSC/MIDI world, but first Non-Commercial use requires user account/key authority and therefore remains explicitly pending rather than silently installed.

## Resource economics already validated

E7 contains the desired Provider-First behavior:

- ImageMagick and FFmpeg image-resize speed was effectively tied, while ImageMagick retained value through lower command/semantic friction;
- Godot had a large cost for trivial state traces but retained a unique capability ceiling;
- the original Blender Linux dependency closure prevented casual persistence, but an official verified Windows portable later reduced the retained footprint to ~911 MiB and enabled real Spatial dogfood;
- REAPER proved that a ~156 MiB portable DAW can add native editable audio state without replacing FFmpeg;
- Inkscape never reached an executable, so no fabricated benchmark was created.

Studio should keep these cost dimensions typed rather than collapse them into one score.

## Ownership split

### Studio owns

- creative and expressive intent;
- claims and asset provenance;
- source-to-publication transformation semantics;
- medium-aware evaluation;
- technical QC plus perception evidence;
- editable-master and review requirements;
- production-package identity;
- cross-medium creative research.

### Providers own

- codec implementation;
- image/vector rendering engines;
- 3D/game/render engines;
- NLE internals;
- generic timeline interchange;
- live-production scene/stream mechanics;
- professional design-editor mechanics.

## OpenTimelineIO

OTIO remains the preferred generic editorial timeline interchange owner. Studio should extend OTIO only where an exact tool/pipeline adapter is missing; it should not create a competing generic timeline format.

## OBS

OBS Studio 32.2.1 + obs-websocket 5.7.4 now have real E8 consumer evidence. A Windows-loopback authenticated client observed scene state, created and removed a temporary scene, preserved the program scene, then Studio restored the exact prior configuration and verified port 4455 was no longer listening.

Prefer owner-native obs-websocket protocol and machine-readable request/event state over GUI automation. Authentication, native Windows working directory, workstation process lifetime and asynchronous state convergence are explicit equipment semantics.

Keep OBS WebSocket **disabled by default**. A bounded Live production may enable it temporarily and must restore/verify the prior listener state afterward.

## Equipment acquisition boundary

E0–E7 also showed that host-level package provisioning can conflict with Runtime executable-drift invariants after the physical package transaction changes executable topology.

Therefore Studio should not become a package manager. Acquisition belongs to Workstation/Computer Equipment providers; Studio asks for an exact capability and consumes the resulting binding.

Target shape:

```text
Studio production need
→ EquipmentCandidate
→ acquisition owner
→ exact EquipmentBinding
→ Studio dogfood
→ PROVEN / PREFERRED / RETIRED
```

## Freeze

Do not add Studio-local generic installers, render engines, NLE abstractions, browser daemons, or device-control frameworks when mature owners already exist.

New custom code must represent Studio semantics or a measured impedance mismatch, not merely wrap a command in Studio vocabulary.
