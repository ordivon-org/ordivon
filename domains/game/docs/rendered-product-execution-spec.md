# Game V6 R11 — consumer-bound architecture execution specification

Status: proposed execution cut; R1–R7 merged, #2809 remains under required checks.
Host: Game factory topic, #31596, #31607, #32559, #32644. R2.1:
(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold). No inferred owner votes.

## Goal / reality / change

A product consumer needs correct rule transitions, visible and usable effects,
and evidence of actual consumption. A native exit zero or renderer initialization
is not a pixel witness. Move from headless-only startup evidence to an independent
rendered-startup consumer of the actual exported executable. Preserve the existing
headless gate; do not redefine READY or require new desktop authority.

## Thought / Logic / Capability map (actual source cut)

| Thought LEGO | Logic LEGO, decision owner | Actual capability / source | Change |
|---|---|---|---|
| Mechanic transfer, falsification | advisory source retrieval/relationship projection | knowledge/, src/{knowledge-file,mechanism-relationship-graph,counterexample-projection,query-input}.ts, scripts/*query.ts | retain; no gameplay dependency |
| Fixed-time state and explicit transition | local rule/config, terminal and invalid-input invariants | examples/beacon-relay/{relay_rules,relay_plan}.gd; examples/room-encounter/{encounter_rules,encounter_tuning}.gd; native-composition/grid_rules.gd | retain single rule authority; typed Rust candidate only after real profiling/parity |
| Scene composition, effects as projection | presentation, movement, collision/physics, HUD | Beacon main/player/mob/hud/relay_sites; Room encounter_root/view and .tscn; Godot Node/Resource/Scene | retain native scene ownership |
| Explicit event consequence | audio and narrative effect | encounter_audio_feedback.gd, narrative/{encounter_dialogue,gate_state}.gd; upstream Dialogue Manager; native-composition movement_audio_feedback | retain; separate actual audio evidence |
| Durable continuity | checkpoint, restart, rule state | encounter_save_slot.gd, assert_process_restart.gd | retain; no second store |
| Agent action/observation | action admission, bounded episode | agent_episode.gd, scripts/agent_episode_acceptance.py | retain; no synthetic human |
| Formal refinement and independent falsification | arithmetic, traces, native process/receipt validation | formal/verify_room_arithmetic.py, native_scene_acceptance.py, native_process.py, test_godot_package_contract.py | reuse; independent pixel oracle |
| Immutable delivery | source/template identities, package and READY | native_export_identity.py, mise.toml, GitHub Actions | no receipt scope inflation; separate downstream verifier |
| Consumer qualification | actual render, decoded raster, evidence scope | Godot Movie Maker + Xvfb + FFmpeg | replace attempted ad hoc Win32 capture, optional Linux display-backed gate |
| Human evidence / creative exploration | consent, paired trials, study constraints | research/room_encounter_playtest.py, docs/room-encounter-playtest.md, research/autonomous-interest-r7/ | separate authority, no fabricated trials |

## External substrates and selection

- Godot native Movie Maker, fixed FPS and PNG: https://docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html ; CLI https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html .
- Headless intentionally disables rendering: https://docs.godotengine.org/en/latest/classes/class_renderingserver.html . GdUnit4 scene runner provides mature simulated inputs and frame stepping https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/sceneRunner/ ; use where actual consumer needs richer fixtures; no blanket replacement of proven native suites.
- FFmpeg real decoder: https://ffmpeg.org/ffmpeg.html . Xvfb isolates display; no unrelated desktop capture or OS input.
- Godot + Rust GDExtension https://docs.godotengine.org/en/stable/engine_details/engine_api/gdextension/index.html and https://godot-rust.github.io/ ; Bevy ECS schedule https://docs.rs/bevy/latest/bevy/ecs/schedule/index.html . Prior matched 1536 rule rows support portability, not a full engine migration. Keep Godot scene/export; switch costly pure kernel only with measured workload, actual native binding, deterministic differential replay, cross-platform export and cost win. No parallel equal-authority rule kernel in production.

## Executable contract R11-P0

I: explicit local executable, expected SHA-256, named product, bounded resolution.
S: caller-owned temporary directory, no external user state; O: scoped JSON receipt.
pre: executable exists, exact SHA, Xvfb and FFmpeg available, native display not headless.
post: eight exact indexed PNGs from actual executable (30 fixed FPS), expected dimensions,
real FFmpeg RGB24 decode of all frames, exact byte count, final frame nonuniform,
strict native diagnostics and unchanged executable digest.
inv: fail closed on missing, extra, truncated, wrong-size, uniform final raster,
nonzero exit, timeout or diagnostic; never emit PASS from arbitrary filename/size alone.
eff: isolated display process and temporary output; delete own scratch on termination.
c: eight frames, maximum 1920x1080, maximum 8 MiB each encoded, bounded time.
epsilon: backend-specific pixels; no universal reference image, no aesthetic or physical
input/audio claim. prov: binary SHA, renderer, per-frame encoded/decoded SHA, tool identity.
unfold: reuse native_process.verify_process, Xvfb, Godot CLI and FFmpeg, no new engine.

Acceptance order: actual source rendering probe, actual exported product probe,
real decoder negative/positive contract, both actual product binary checks, owner verify,
publish candidate and read back. Keep #2809 head unchanged while CI is underway.
Next: independently scoped physical input/audio, targeted human study, native profiling
for Rust migration, conditional GdUnit4 trial; no repeated headless-only gate counted as pixels.


## Agent invocation and acceptance separation

Run `mise run test:rendered-product-contract` for the real decoder fixtures;
`mise run test:rendered-product-native-counterexample` builds a separate native
blank project, demonstrates headless exit zero, and requires raster rejection.
For an independently verified native exported executable:

```sh
python3 scripts/rendered_product_acceptance.py --product beacon-relay \
  --executable /absolute/path/to/beacon-relay.x86_64 \
  --sha256 <verified-executable-sha256>
```

The receipt is supplemental downstream evidence, not a producer signature,
release, physical display or sound measurement. Retain the JSON via the existing
Runtime result/artifact route. CI stays unchanged pending actual runner
qualification. The selected startup frames may legitimately be identical;
motion, controls, sound and accessibility are separate next acceptance goals.

## R12 — interaction refinement, not another game engine

Host #32683/#32694; extend downstream L12 consumer. L03 rules and L04 tuning
remain product-owned, L05/06 Godot GUI/InputEvent projection, L07 audio and L08
save remain separate. L09 Agent action API is not a substitute for L06 OS event
delivery. L10 independent metamorphic observation and L11 source-bound binary
delivery feed L12; L13 human quality is not inferred.

Mature substrates: Godot input propagation
https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html ;
XTEST https://www.x.org/releases/X11R7.7/doc/libXtst/xtestlib.html ;
FFmpeg x11grab https://ffmpeg.org/ffmpeg-devices.html#x11grab .
Existing libX11/libXtst, Xvfb, FFmpeg are available; xdotool is absent.
Use a narrow Python ctypes binding to the existing XTEST functions instead of
adding an automation framework or implementing key simulation. No physical
desktop input, no extra production authority, no native dependency pin.

I: actual Room native executable, expected digest; O: named transition witnesses
and scoped JSON. S: owned private Xvfb display, temporary XDG paths, target PID
and window ID. pre: exact input SHA, independent display, unique target window
owned by launched process, stable baseline. post: irrelevant key preserves
raster; A changes the visible status; R restores the source-bound status strip. inv: no input into
existing display, reject ambiguous ownership, no capture of other windows,
bounded execution, strict native diagnostics and same binary SHA. eff: synthetic
OS key press/release and window-local capture; own process and display cleanup.
c: bounded frames/commands/time, 1152x648 RGB. epsilon: backend-specific
metamorphic startup test; no universal pixel golden or human engagement.
prov: executable, window/PID, input sequence, actual captured RGB SHA and
renderer. unfold: Xvfb + Xlib/XTEST + FFmpeg + existing strict process
qualification. Keep separately invocable, no CI gate until runner qualified.

Negative control: a missing/no-effect input must fail the required change
predicate, while an unrelated key must preserve state. Existing native rule
oracle separately covers actual transition meaning; raster relations do not
authenticate exact HP/turn values. The initial whole-frame reset hypothesis was
falsified: 1,850 differing pixels localized to controls, consistent with retained
valid focus. At 1152x648 compare status rows [64,128), preserve full hashes and
require full attack/reset replay equality. Geometry is part of the contract. No physical keyboard, physical audio or
Windows acceptance inferred. Reuse native rule tests, not a second simulator.

Invoke `mise run test:x11-interaction-contract` for the relation negatives.
For the actual verified Room binary, run `python3 scripts/x11_interaction_acceptance.py --executable /absolute/room-encounter.x86_64 --sha256 VERIFIED_SHA`.

## R13 — mixed PCM consequence, independent of play() counts

Host #32731; refine L07 audio and L12 actual consumer. The Room rules emit
action_accepted only for admitted combat turns. Audio feedback is an effect
projection; reset/restoration is not a new accepted action. Native play counts
remain useful but cannot establish non-silent mixed samples.

Reuse Godot Movie Maker's native mixed WAV output
(https://godotengine.org/article/movie-maker-mode-arrives-in-godot-4/;
https://docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html)
and FFmpeg real decoding. AudioEffectCapture/Record are alternative in-engine
substates, not a second mixer. PulseAudio null sink monitor is a later system
output route (https://www.freedesktop.org/projects/pulseaudio/Documentation/User/Modules/);
standalone server unavailable on this runner, do not touch shared audio.

I: exact Room executable SHA, isolated X11 launch; O: scoped PCM receipt.
S: private display, temporary app data, bounded movie output.
pre: correct binary identity, actual target window, decoder, native movie output.
post: no-event/irrelevant-key/reset control is quiet; accepted attack produces
nontrivial mixed PCM, with input delivery and native exit verified.
inv: no inference from stream.play(), file existence, or WAV header alone;
reject silent positive, audible negative, malformed/truncated samples, drift.
eff: temporary XTEST events only to owned window and engine-generated WAV.
c: bounded fixed frames, 30 FPS, bounded audio bytes and duration; cleanup.
epsilon: mixed PCM and controlled contrast, not physical device output or
subjective sound quality; don't assume exact acoustic waveform across backends.
prov: binary SHA, event program, decoded PCM SHA, sample shape and amplitude,
native diagnostic result. unfold: existing X11 input binding + native Movie
Maker + FFmpeg; no new audio engine or dependency. Qualify native probe before
making a production consumer, no READY expansion or CI gate without evidence.
