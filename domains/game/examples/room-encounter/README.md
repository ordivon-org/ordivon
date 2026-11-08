# Room Encounter — Native Godot Composition

Original playable graybox prototype with three rooms; not a new engine,
a revived game or a finished commercial product.

From domains/game:
- Run: godot --path examples/room-encounter
- Verify: godot --headless --path examples/room-encounter --script res://assert.gd

Keyboard A/Space attacks, G guards/restores stamina, N/Enter opens
native gate dialogue after room clear, R restarts. Buttons provide the same actions. Native game loop: input
-> encounter state -> state_changed Signal -> replaceable HUD. Built-in Godot
Scene, Resource, Signal, Label and Button are the reused LEGO providers.

encounter_tuning.gd + configs/*.tres controls rooms and combat numbers;
encounter_view.tscn may be substituted by encounter_view_variant.tscn.
The native assert.gd consumer loads the actual PackedScene and explores
bounded transitions, loss/win and replacements. No external asset was copied.
Real art, music, navigation and human playtest belong to follow-on consumers.

## Native sound as a consumer

Original Kenney CC0 sound files and exact license/provenance are recorded
under assets/. The EncounterAudio AudioStreamPlayer observes the existing
authoritative action_accepted signal, plays only accepted attack/guard turns,
and can swap between two AudioStream resources without changing game logic.
This extends the real product input -> rules -> audio/player feedback
consumer, not a new Ordivon sound engine; no physical speaker output or
human enjoyment measurement is asserted by the headless test.

## Save/resume composition using Godot native ConfigFile

Save [S] and Load [L] are real keyboard/button inputs of this runnable
room-encounter consumer. The SaveSlot node delegates all storage to the
built-in Godot ConfigFile API, while authoritative EncounterRules alone
validates the active tuning and checkpoint before restoring state. The
default native slot is user://room_encounter_run.cfg; acceptance uses a
separate temporary slot. No new generic persistence engine is added.

Audio now observes an explicit action_accepted Signal rather than inferring
combat turns from state changes. A restored turn, a reset or alternate HUD
cannot trigger a false attack sound. Source-to-native acceptance checks
checkpoint readback, incompatible tuning and a damaged stored value.
Cloud sync, migration across changed tuning, real sound hardware and
human playtest remain unverified.

## Native branching room narrative

The source-pinned upstream MIT Dialogue Manager 4.2.0 now runs inside
the real room game. Unlock invokes EncounterRules.advance, Leave preserves
game state, while Open Door and N/Enter request native branching dialogue.
The only token predicate is EncounterRules.phase=cleared; no separate ledger.
The upstream addon/unchanged MIT license are located under addons/,
and the real Game consumer under narrative/.

## Native two-process checkpoint qualification

The peer-owned assert_process_restart.gd demonstrates one process writing
a ConfigFile run and a fresh Godot SceneTree reloading that run with
silent state restoration and continued legal gameplay. Game test:encounter
runs both independently and cleans the temporary slot. No duplicated
storage engine or renderer is introduced.

## Human and Agent operation — distinct evidence channels

**Human operator:** Import the addon once with `godot --headless --editor --import --path examples/room-encounter`, then run `godot --path examples/room-encounter` and play through the keyboard/buttons described above. Human enjoyment, usability and accessibility require human evidence; a headless test cannot prove them.

**Agent operator (symbolic, bounded):** After the same editor import, run from `domains/game/`:

    godot --headless --path examples/room-encounter --script res://agent_episode.gd -- --actions attack,advance,attack,attack

The single `GAME_AGENT_EPISODE_JSON=` line uses `schema_version=2`.
By default, `--observation player` projects only what the native
Godot HUD and currently visible dialogue controls show: status, encounter
text, enabled player inputs and visible dialogue response text. It does not expose the authoritative rules snapshot. Each player-mode
step contains only the submitted action and the visible before/after UI.
Private accepted/recognized results and the internal control path are
**debug-only**, not exposed to a player-mode Agent.

For privileged diagnostics, pass `--observation debug` explicitly.
That mode returns the full EncounterRules snapshot in the initial,
before/after and final fields under the label
`authoritative_debug_state_not_pixels`. This mode must never be
claimed as a fair player-information Agent. Both modes use the real
Dialogue Manager `choose_response("unlock")` API and real
`passage_advanced` commit event. The agent no longer waits an
arbitrary number of frames for startup, but native dialogue completion
remains asynchronous. Neither mode proves pixel perception or enjoyment.

Each process starts a new scene and fresh run, does not write save files, and accepts at most 64 actions. Agents may submit a growing action prefix to inspect later states; this is bounded deterministic replay, **not** a persistent online environment, browser controller or visual playtest.

`mise run test:agent-episode` verifies HUD-only default observations, explicit debug mode, native scene transitions, deterministic replay, pre-clear narrative gate rejection, an actual terminal win through the native Unlock choice, and the action limit. `mise run verify` first imports the native dialogue asset through `test:encounter`, then runs this Agent acceptance. Real players and Agents use the same authoritative encounter rules; they do not share an evidence claim about subjective experience.


## Native Linux x86_64 export and package

Run `mise run export:room-linux` from `domains/game/` after installing official **Godot 4.7.2** Linux x86_64 export templates (same engine version as the pinned editor). This is standard Godot export via `export_presets.cfg`, not a custom engine or a project-only packer. It embeds the PCK into the engine executable and invokes that **exported executable** headlessly for a native launch check. Output is ignored by Git under `dist/room-encounter/`: an executable, two upstream asset license notices, and a Linux x86_64 tarball. Set `GAME_EXPORT_DIR` to override the output directory.

A successful export, executable launch, or archive is evidence of a native, platform-specific deliverable. It does **not** establish Human enjoyment, graphics/audio correctness on a physical device, other OS compatibility, signing or game-store release. Those require the relevant Human/target consumer. The upstream Dialogue Manager MIT license and Kenney CC0 asset source notices are copied from their existing source locations.


## Native Windows x86_64 export (Human desktop consumer)

Run `mise run export:room-windows` from `domains/game/` with the official Godot **4.7.2** Windows x86_64 templates installed. It uses the same project source and rule/narrative state as Linux, plus the native Godot Windows Desktop export preset. The ignored output is `dist/room-encounter/windows-x86_64/room-encounter.exe` and a `room-encounter-windows-x86_64.zip` containing the executable and both upstream license notices. No Godot SDK or Ordivon Runtime is needed by the eventual Windows player. Run the exported Windows executable on a real Windows host to verify its launch; a Linux build command alone does not establish Windows runtime readiness.

For both platforms, the Godot export preset excludes the standalone first-party Agent and assertion scripts. They stay available in source for mechanical verification but do not belong in the playable package. Linux and Windows builds are **technical previews**, not Human-validated indie game releases or store-certified products.


## Signed arithmetic and checkpoint invariants

`EncounterRules.guard` restores only the remaining stamina instead
of adding before clamping. The authoritative turn counter is monotone
and saturates at the maximum signed 64-bit value, including after
loading a valid maximal checkpoint.

**Human:** normal Save/Load, combat and UI behavior remain unchanged.
**Agent:** run `mise run verify:room-smt` for the signed-i64 Z3 model,
and `mise run test:encounter` for native Godot implementation checks.
Their evidence scopes are not interchangeable.
