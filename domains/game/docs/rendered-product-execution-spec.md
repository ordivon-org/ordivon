# Game V6 R11 — consumer-bound architecture execution specification

Status: proposed execution cut; R1–R7 merged, #2809 remains under required checks.
Host: Game factory topic, #31596, #31607, #32559, #32644. R2.1:
using problem-specific mathematical obligations. No inferred owner votes.

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

## R14 — immutable hosted-product consumer convergence

Host #32781; #2809 merged 51f78bc50a09af584f47fb7b2ceef201ee87d5dc.
The real consumer of L11 delivery is L12, not an additional build. Adopt
GitHub Actions immutable artifact identity, its REST SHA-256 digest
(https://docs.github.com/en/rest/actions/artifacts), and stdlib zipfile/tarfile
bounded member reads (https://docs.python.org/3/library/tarfile.html).
Do not add artifact storage, scheduler, unpacking engine, or game simulation.

I: locally downloaded exact Actions ZIP, expected outer SHA, expected source
commit and product. O: bound downstream consumer receipt. S: private bounded
scratch, no normal player app data. pre: regular archive, exact outer digest,
five exact regular members, expected READY/source, exactly three manifest
members and digest match, known export templates. post: one native Linux
executable from the verified archive; strict rendered startup for both products,
Room interaction and mixed PCM; bind actual executable hash and child scopes.
inv: reject malformed inventories, duplicates, links, traversal, excessive
member sizes, wrong source or digest, and any failed sub-consumer. No partial PASS.
eff: disposable file materialization and private display execution; no upload,
release, re-export, or mutation of input. c: bounded sizes, one product at a time.
epsilon: tested Linux renderer/geometry/PCM only, no Windows or physical audio.
prov: outer ZIP SHA, source, archive and executable SHA, child receipts.
unfold: existing native consumers and Python stdlib archive decoders. Retain
producer READY meaning and CI workflow; no new required CI check before actual
runner qualification. Existing local direct executables remain useful probes.

## R17 — shared delivery identity, platform-local native execution

Host #33018: keep #2842 in its protected queue, build on R15/R16 source.
The Windows consumer must not copy the Linux implementation or assume
Linux evidence entails Windows. Thought LEGO: immutable identity, effect
boundary, platform adapter, independent observation. L11 outer ZIP, READY,
source and manifest checks remain single authority; L12 Linux tar versus
Windows ZIP materialization; native Windows Runtime owns launch in active
interactive session, Godot Movie Maker owns frames, existing FFmpeg raster
oracle owns decode. No capture of desktop or injection into physical input.

I: exact hosted outer SHA/source/product, explicit platform; O: separate
Windows native startup/recording receipt and decoded raster witness.
S: owned private stage, exact executable digest, native child process;
pre: verified bundle, exact native inventory and regular files, isolated
app-data env, explicit absolute stage; post: Windows process exit zero,
native diagnostic and Movie Maker renderer witness, exact eight PNGs,
decoder nonuniform final and hashes bound to the same executable.
inv: no second manifest parser, no archive path extraction, no unrelated
desktop capture, no global keyboard, no actual audio or human claim.
eff: Windows native process and bounded local files; c: fixed eight frames,
bounded archive/member/time, owned cleanup. epsilon: Windows native
rendered startup only, not physical display presentation or gameplay.
prov: outer/source/native archive/exe SHA, Windows process session and
renderer, frame hashes and existing FFmpeg decoder; unfold: Python
zipfile, Runtime native launch, .NET ProcessStartInfo, Movie Maker
(https://docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html),
existing verify_rasters. No READY expansion or new required CI job.

## R18 — independently qualified hosted runner, not a second factory

Host #33093 / global test blackboard #33105. #2868's existing native PR
gate succeeds; that does not establish display-backed hosted consumption.
Use existing GitHub Actions workflow_dispatch (default workflow already
exists; explicit ref), native runner images and artifact REST metadata.
References: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow ;
https://docs.github.com/en/rest/actions/artifacts ;
https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md .

Thought: consumer-first, exact finite obligations, provenance, capability
qualification; no substitute rebuild or parallel scheduler. L11 selects
a completed successful same-repository main push of the exact Game
workflow and its two unexpired artifacts. L12 consumes each downloaded
original ZIP with the existing hosted_product_acceptance, not its receipt.
Native runner preflight checks Xvfb/Xauth/XTEST/FFmpeg, software GL; actual
render/interaction/PCM is the decisive qualification, not installed tools.

I: explicitly selected positive source run ID; actual workflow/API metadata.
O: one aggregate receipt only after both exact products PASS.
S: exclusive runner scratch; metadata and immutable outer ZIPs.
pre: same-repository head and run identity, main push success, exact
workflow path, exact product names/run/source/repo bindings, bounded sizes
and SHA-256. post: both native consumers complete, hashes and scopes bound.
inv: no fork/PR/failed/expired/substituted artifact, no missing obligation
promoted to PASS; no token in native execution step; no re-export, no
release publication. eff: read API, local downloads, private X11 effects;
c: one bounded manual hosted job, max 256 MiB per archive, timeouts.
epsilon: only selected successful source cut and actual hosted software
renderer; no physical peripherals, Human or Windows execution implied.
prov: source run and artifact metadata, checkout consumer SHA, hosted
run/attempt, runner label and child evidence. Unfold: existing workflow,
GitHub CLI, Python stdlib, existing consumers. Optional dispatch input
consumer_run_id excludes producer matrix; empty preserves existing behavior.
No new required CI gate or READY expansion until actual qualification.
