# E0–E7 — Ordivon Equipment World

**Status:** completed on 2026-08-13.

## Objective

M7 established what different media/encounters require. E0–E7 asked the next operational question:

> Which professional instruments should Ordivon actually keep, invoke, or defer, and what evidence justifies their existence?

The experiment deliberately rejected one simplistic ablation rule. A tool is not useless merely because deleting it leaves a fallback path. A specialist may be worth keeping because it removes command complexity, manual handoffs, GUI work, recovery burden, format conversion, or repeated local reinvention. Conversely, a powerful application can remain on-demand when its footprint and state surface exceed current production pressure.

The retained evaluation axes are therefore:

```text
capability gain
friction reduction
quality / editable-master / professional ceiling
observability / recovery
install + dependency + state + license + maintenance cost
```

They are not collapsed into one universal ROI score.

## E0 — Actual equipment landscape

The machine audit established a real baseline rather than a shopping list.

Already present before this round:

```text
DaVinci Resolve Studio 21.0.3.7
OBS Studio 32.2.1
Figma 126.7.10
FFmpeg / FFprobe n9.0
rsvg-convert 2.62.3
```

E0 also confirmed that Windows uninstall-registry discovery is insufficient: Resolve existed at its executable path without appearing in the sampled standard uninstall keys. Equipment discovery therefore uses capabilities/known executable paths/globs and safe version probes rather than one registry source.

Physical presence was bounded to device metadata. Integrated camera, microphone, playback output, display and generic HID were present. No targeted Stream Deck, XR headset, drawing tablet, 3D mouse, specialist MIDI/audio interface, depth camera or haptic wearable was observed. No sensor content was captured.

## E1 — Capability and ownership model

`research/equipment/equipment-world.json` is the first machine-readable Equipment World. It does not expose generic GUI clicks. It describes bounded capabilities such as:

```text
document.compile.pdf
image.resize
scene.render
interactive.run.headless
timeline.conform.otio
live.scene.switch
design.node.write.plugin
audio.multitrack
```

The responsibility split survived dogfood:

```text
Studio
  choose equipment from medium/production need
  compile bounded intent
  declare artifact/inspection expectation

Runtime
  exact executable / argv / environment
  process authority and recovery

Host / Computer
  presence / version / license/configuration projection
  system-level software provisioning

Web
  browser/publication runtime and Web encounter evidence
```

The CLI now exposes `equipment inventory`, `equipment select`, and `equipment plan`. `plan` intentionally stops before execution. A real Typst plan produced `/usr/bin/typst` plus exact `compile` arguments; Runtime remains the execution authority.

## E2 — CLI-native equipment

### Typst

Typst was installed and executed. E6 compiled a tagged one-page PDF in `20.89 ms` for the bounded fixture. The direct package is about `45.37 MiB`, the Typst+ImageMagick transaction about `67.41 MiB` total installed.

**Decision: core equipment.** It introduces a Studio-local deterministic publication compiler and removes the need to route every PDF/report through Web/GUI publication.

### ImageMagick

A controlled resize comparison found:

```text
ImageMagick median  64.0516 ms
FFmpeg median       64.0602 ms
ratio               0.99987
```

There is effectively **no speed advantage**. The result would look like a deletion under a capability-only test because FFmpeg can resize the same image.

But the same operation required:

```text
ImageMagick  4 arguments
FFmpeg      10 arguments
```

and ImageMagick exposes an image-native batch/operator vocabulary. The direct package is only about `21.76 MiB`.

**Decision: core equipment, earned primarily through friction reduction rather than unique capability.** This is the central E7 counterexample to capability-only ablation.

### rsvg-convert

It remains the tiny SVG raster baseline. E6 rendered the 1200×630 fixture in about `37.60 ms`; the separate E7 median was about `64.10 ms` under repeated subprocess measurement.

**Decision: retain core baseline.**

### Inkscape

Inkscape has a legitimate vector-native ceiling, but no performance result is invented. Its actual current dependency closure was `75` packages, about `77.89 MiB` download / `524.97 MiB` installed. The 300-second provisioning attempt timed out before transaction and left an orphan downloader in uninterruptible I/O; the package was not installed.

**Decision: candidate, demand-pulled.** Existing raw SVG + rsvg-convert + installed Figma cover current ordinary work. Revisit only when vector-native local query/edit operations become a real bottleneck.

## E3 — Scripted professional workstations

### DaVinci Resolve Studio

Resolve was not re-proven from documentation. Existing Studio production already has real OTIO conform/editable-master evidence and a version-specific adapter.

**Decision: retained external workstation.** It earns its cost through editable NLE/color/Fusion/Fairlight state and professional finishing that FFmpeg alone does not provide.

### REAPER

Rather than installing another DAW blindly, E3 sampled the official REAPER 7.78 Linux portable package. The executable exposed batch/render/config/project command tokens and the product has ReaScript/OSC control surfaces. The portable binary was about `12.97 MiB`.

The stock headless WSL probe did **not** succeed: `libSwell.so` failed on `gdk_init_check` before application start. The package documentation describes a custom `NOGDK=1` libSwell path for headless use, but that was not built in this round.

**Decision: candidate-headless-integration.** High Audio potential, low package size, but not yet zero-friction equipment and no production render is claimed.

### Figma

Figma 126.7.10 is installed and its plugin model is appropriate for in-editor document mutation, but the Studio repository contains no ordinary Figma production receipt yet.

**Decision: installed external workstation, integration provisional.** Do not create a duplicate design authority merely because the application exists.

## E4 — Realtime equipment

### OBS Studio

OBS 32.2.1 is installed. Safe configuration projection found authenticated WebSocket configuration on port `4455`, with the password retained outside evidence. Crucially, `server_enabled=false`.

**Decision: installed external workstation, integration provisional.** The adapter capability is modeled, but E4 did not silently enable a network listener or move the secret into source/argv. A real Live production should activate and test it when needed.

### TouchDesigner

TouchDesigner remains a strong cross-media candidate for realtime visuals, sensors, installation, OSC/MIDI and projection workflows, but there is no local installation or production evidence.

**Decision: candidate.**

## E5 — Physical equipment

E5 deliberately did not buy hardware merely to complete a taxonomy. Existing camera/microphone/display/HID capability is enough for ordinary capture experiments. Stream Deck, XR and haptics remain demand-pulled.

**Decision:** Stream Deck and bHaptics remain challengers until a real physical encounter exists.

## E6 — Cross-equipment production

One exact proposition was held constant:

> The response was lost. The operation outcome is unknown. Recover the same operation identity before concluding success or failure.

The executed packet used:

```text
Typst          → tagged PDF
rsvg-convert   → 1200×630 visual
ImageMagick    → 600×315 delivery preview
Godot headless → state trajectory JSON
FFmpeg         → 2-second H.264 motion sequence
```

The preview was inspected as actual image content. The interactive trace preserved `unknown → checking → unknown` under one operation identity. The MP4 was verified as H.264 640×360, 30 fps, yuv420p, exactly 2 seconds.

Blender remained unavailable after provisioning pressure, so E6 explicitly used a non-3D fallback for the second motion frame and retained `spatialEquipment=null`. **No 3D production success is claimed.** This matters more than keeping the demo visually symmetrical.

## E7 — Deletion, friction and economics

### Godot versus a trivial Python state machine

```text
Python median  15.7745 ms
Godot median  565.1332 ms
ratio          35.83×
```

A trivial state trace should not use Godot. But Godot adds a genuine non-Web application/game runtime with input, rendering, export and XR paths unavailable to the small Python fixture.

**Decision: specialist-on-demand.** The deletion test changes *where* the engine is used rather than deleting it.

### Blender provisioning pressure

After lightweight tools were installed, the Arch Blender closure still projected about:

```text
743.2 MiB download
3069.84 MiB installed
139-package-class professional 3D stack
```

A 900-second provisioning attempt timed out before package transaction. Blender remained absent.

**Decision: candidate.** Its professional 3D ceiling is obvious, but E7 found current provisioning friction high enough that it should be pulled by a real Spatial/3D production, not preloaded as core equipment.

### System provisioning itself failed the ordinary Runtime abstraction

Typst/ImageMagick and Godot physically installed successfully, but Runtime marked their package-manager jobs `EXECUTABLE_RUNTIME_DRIFT` because the job itself changed executable topology under `/usr/bin`. This is correct behavior for ordinary contained execution.

**Architecture result:** do not weaken Runtime invariants so Studio can install software. Host/Computer should own a distinct provisioning operation with postcondition inventory; Studio should consume the resulting equipment capability.

## Final retention matrix

```text
CORE / CHEAP EQUIPMENT
  FFmpeg
  FFprobe
  rsvg-convert
  Typst
  ImageMagick

SPECIALIST ON DEMAND
  Godot

RETAINED EXTERNAL WORKSTATION
  DaVinci Resolve Studio

INSTALLED, INTEGRATION PROVISIONAL
  OBS Studio
  Figma

CANDIDATES
  Inkscape
  Blender
  REAPER headless integration
  TouchDesigner

PHYSICAL CHALLENGERS
  Stream Deck
  bHaptics / tactile output
```

This is intentionally asymmetric. Professional reputation is not a retention rule, installation is not a production receipt, and fallback capability is not enough to dismiss a low-friction specialist.

## Reproduction

```text
pnpm equipment:inventory
pnpm equipment:e6
pnpm equipment:e7
pnpm python:test:core
```

`out/equipment/` contains machine-local generated artifacts and portable evaluation material and is not promoted into Git truth. The normalized retained ledger is `research/equipment/evidence/e0-e7-20260813.json`.
