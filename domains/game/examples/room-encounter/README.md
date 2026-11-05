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
