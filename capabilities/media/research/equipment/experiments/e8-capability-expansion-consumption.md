# E8 — Capability Expansion Through Real Equipment Consumption

Date: 2026-08-14
Baseline Studio revision: `1061d740c01aec9272fd3bc50bdbf8a32da2c1b1`
Evidence: [`../evidence/e8-capability-expansion-20260814.json`](../evidence/e8-capability-expansion-20260814.json)

## Question

The earlier equipment rounds were deliberately conservative: do not install a professional application merely because it has a larger feature list. Ordinary production then exposed the complementary risk: if a tool gives Studio a genuinely new way to observe or act on media, waiting for a narrowly preselected work can make the world model artificially small.

E8 therefore changes the admission question from “is this tool required right now?” to:

> Does this equipment expose a new medium-native state/action world, preserve editable state that our simpler tools flatten, or materially reduce repeated Agent friction enough to justify its cost and authority boundary?

A positive answer still requires real execution. Vendor capability claims alone do not graduate equipment.

## REAPER — Audio becomes a project-state world

The official REAPER 7.78 Windows payload was SHA-256 verified. Two silent installer invocations returned `199`, but later reconciliation found that both had produced delayed full installations in Program Files / the user Programs directory. Those duplicate effects were removed through their uninstallers and the registry was verified clean. Independently, the verified NSIS payload had been materialized into a reversible user-local portable instance; that single portable instance is now the retained REAPER authority.

A first launch established an important workstation boundary: Runtime timed out while the Windows REAPER process remained alive. A later `-nonewinst` invocation delivered a Lua ReaScript into that running instance and produced a marker, proving Agent → workstation → ReaScript control.

The next script created a real two-track `.rpp`: two independent media items at different times, named tracks, independent pan and volume, and render state. The interactive instance was then closed. A separate `-renderproject` invocation reconstructed a 48 kHz / 24-bit stereo 2.5-second WAV from the persisted project and exited cleanly.

**Decision: specialist-on-demand, proven.** REAPER does not replace FFmpeg or Resolve Fairlight. Its new value is a lightweight scriptable DAW world with durable track/item/mix state and a path to routing, envelopes, MIDI and automation.

## OBS — Live becomes an observable/actionable world

OBS 32.2.1 was started only after byte-exact backup of the authenticated obs-websocket configuration. The WebSocket server was temporarily enabled, while authentication remained required.

Launching OBS from a WSL UNC working directory exposed a real equipment friction: the Windows GUI process existed, but its relative resource lookup was not healthy. Relaunching from the native Windows application directory produced a working OBS instance and obs-websocket 5.7.4 listener.

WSL could not safely consume Windows loopback directly, so no firewall rule was opened. A Windows-local PowerShell `ClientWebSocket` instead authenticated on `127.0.0.1`, observed the current scene list, created a temporary scene, preserved the current program scene, and requested removal. The first immediate read was too early; a later reconnect showed the scene had converged away.

OBS then exited, the original configuration bytes were restored exactly, `server_enabled=false` was re-established, and no 4455 listener remained.

**Decision: retained external workstation, default-off.** Live media is now a real Studio world. Equipment lifecycle, native working directory, loopback topology, authentication, asynchronous convergence and exact cleanup are part of the medium boundary rather than incidental shell details.

## Blender — Spatial/3D becomes a real medium

The previous Linux package-manager path projected roughly 743 MiB download and ~3 GiB installed state and never completed. E8 used the official Blender 5.2.0 LTS Windows x64 portable ZIP instead: 387 MiB archive, ~911 MiB extracted, SHA-256 verified, no system package transaction.

A background Python run created a real spatial scene with editable geometry, a curve path, named source/expression objects, materials, a camera and three lights. Blender saved the native `.blend`, rendered a 640×360 EEVEE PNG, and exported the same scene as GLB.

The first script also falsified two stale assumptions. Blender 5.2 exposes `BLENDER_EEVEE`, not the older `BLENDER_EEVEE_NEXT` enum. More importantly, the Python traceback still left the Blender process with exit code zero. A professional-equipment Job therefore needs domain artifact/state postconditions; process success alone is insufficient.

**Decision: specialist-on-demand, proven.** Studio now has a true spatial scene world: geometry, viewpoint, lighting, material and spatial composition are no longer approximated as 2D frames.

## Figma — admitted conceptually, user OAuth is the correct boundary

Figma 126.7.10 is already installed. The current official Remote MCP endpoint was added to the local Codex MCP configuration and correctly initiated OAuth. The browser consent step cannot be substituted by Studio or Runtime.

**Decision: external workstation, OAuth pending.** Figma’s native node/variable/component/auto-layout world is worth consuming, but no MCP connectivity or mutation is claimed until the user grants access and a real read/write round succeeds.

## TouchDesigner — real world gain, but license authority precedes installation

Current TouchDesigner 2025 adds a realtime operator/dataflow world that Blender and OBS do not provide: GPU visual/data operators, TOP/CHOP/DAT/POP composition, OSC/MIDI, Python, sensors and Perform Mode. That is a genuine world-model expansion.

However, first Non-Commercial use requires a Derivative account/key and carries explicit non-commercial/resolution constraints. Installing a multi-hundred-megabyte application while knowingly unable to complete licensing would recreate the exact dormant-tool failure E8 is meant to remove.

**Decision: candidate at user account/license authority boundary.** Once that authority exists, TouchDesigner deserves a bounded realtime dogfood rather than another documentation-only review.

## Inkscape — still not admitted

Inkscape has a legitimate vector-native editing/query ceiling, but its incremental information gain is currently lower. Raw SVG + `rsvg-convert` already cover deterministic vector source/delivery, and Figma is the higher-information design-native frontier.

**Decision: remain candidate.** Re-open only when local vector-native query/edit becomes repeated production friction.

## Updated rule

```text
new medium-native world
OR durable editable state lost by simpler tools
OR repeated friction reduction
        ↓
real bounded equipment dogfood
        ↓
authority / lifecycle / licensing / recovery evidence
        ↓
retain, specialize, or reject
```

This changes Studio’s reachable world without turning software inventory into an end in itself.
