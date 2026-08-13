# Ordivon Equipment World

## Purpose

Studio's Media World Model says **what kind of observer relation and expressive consequence a production needs**. Equipment World says **which professional instrument is worth invoking to realize and inspect that consequence**.

The core rule is deliberately economic rather than taxonomic:

> A tool can earn retention by adding otherwise unavailable capability, by materially reducing operational friction, by raising a professional quality/editability ceiling that is actually used, or by improving observability/recovery. Removing a tool without losing nominal capability does not prove the tool was useless.

This means `ffmpeg` and ImageMagick can coexist even when both resize images: the relevant question is whether the specialist reduces command complexity, batch friction or failure surface enough to justify its small cost. Conversely, a very powerful tool such as Blender or Godot can remain specialist/on-demand when ordinary tasks are cheaper in simpler equipment.

## Responsibility split

```text
Media World Model
    what the production/encounter needs
            ↓
Studio Equipment World
    capability selection
    equipment-specific artifact/inspection expectations
    typed ROI evidence
            ↓
Runtime
    exact executable + argv + environment
    Windows authority / process lifecycle
    immutable inputs / execution evidence / recovery
            ↓
real equipment
    CLI / script API / plugin / WebSocket / OSC / physical device
```

Host/Computer should own host-level provisioning and device presence. E0 produced direct evidence for this boundary: package-manager transactions change executable topology while running, which intentionally triggers Runtime's normal Workspace executable-drift protection even after a package effect physically succeeded. Studio therefore detects and plans equipment; it does not redefine package provisioning as an ordinary production Job.

## Equipment classes

### Deterministic CLI equipment

Examples: FFmpeg/FFprobe, rsvg-convert, Typst, ImageMagick.

Prefer this class when it can express the production operation because it provides the cheapest exact argv, easy batchability, deterministic replay and low state coupling.

### Scripted professional workstations

Examples: DaVinci Resolve, Blender, REAPER, Figma plugin runtime.

Use when editable masters, domain-native project structure, professional finishing, complex scene/session state or specialized tooling changes the production ceiling enough to justify the larger state surface.

### Realtime equipment

Examples: OBS, TouchDesigner, Godot runtime, OSC/MIDI-connected systems.

The artifact includes event/scene/runtime state and currentness, not just one exported file. Secrets and network listeners remain separate authority from Studio source.

### Physical equipment

Examples: camera, microphone, display, Stream Deck, XR headset, MIDI/control surface, depth camera, haptic output.

Physical equipment graduates only from verified device/encounter evidence. A standards SDK or simulated event trace is not evidence that tactile, embodied or low-latency physical consequences were actually observed.

## Agent-facing interface

The first shared interface is intentionally small:

```bash
uv run ordivon-studio equipment inventory
uv run ordivon-studio equipment select image.resize --local
uv run ordivon-studio equipment plan typst document.compile.pdf \
  --parameters '{"source":"brief.typ","output":"brief.pdf"}'
```

`equipment plan` **does not execute** the tool. It compiles a narrow Studio intent into a Runtime-ready proposal or into a bounded external transport (`obs-websocket`, Figma plugin, Resolve adapter, ReaScript/OSC). Runtime remains the process authority.

## Retention test

E7 does not compute one scalar score. Each tool keeps typed evidence on four axes:

```text
capability gain
friction reduction
quality / editable-master ceiling
cost / maintenance / failure surface
```

Deletion therefore asks three different questions:

1. **Capability ablation** — what can no longer be done?
2. **Friction ablation** — what extra steps, argument complexity, manual handoffs, state assumptions or recovery burden return?
3. **Ceiling ablation** — what domain-native editable or professional finishing boundary disappears?

A tool may survive only the second test. This is intentional.

## Evidence

- `equipment-world.json` — machine-readable registry/capability map.
- `sources.json` — official-control-surface source ledger.
- `evidence/e5-hardware-20260813.json` — bounded hardware-presence evidence.
- `experiments/e0-e7-equipment-world.md` — completed E0–E7 program and decisions.
- `scripts/run-e6-equipment-dogfood.py` — real cross-equipment production packet.
- `scripts/run-e7-equipment-economics.py` — deletion/friction/ceiling/cost comparison.

Large generated artifacts, portable evaluation binaries and machine-specific inventories stay under `out/` rather than becoming Git truth.
