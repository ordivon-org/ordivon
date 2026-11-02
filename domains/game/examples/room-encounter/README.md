# Room Encounter — Native Godot Composition

Original playable graybox prototype with three rooms; not a new engine,
a revived game or a finished commercial product.

From domains/game:
- Run: godot --path examples/room-encounter
- Verify: godot --headless --path examples/room-encounter --script res://assert.gd

Keyboard A/Space attacks, G guards/restores stamina, N/Enter opens cleared
doors, R restarts. Buttons provide the same actions. Native game loop: input
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
authoritative state_changed signal, plays only accepted attack/guard turns,
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

## Real process-restart contract (one native storage port)

`mise run test:encounter` includes a two-process headless acceptance using
`assert_process_restart.gd`: the first Godot process saves a second-room,
turn-2 checkpoint through the existing rule-owned checkpoint and built-in
`ConfigFile`, exits, then a fresh independent Godot process loads the same
temporary file. This new scene must render ROOM 2/3, remain silent on
restore, and continue a legal attack with exactly one accepted-action
sound. The test uses a unique temporary directory and cleans the slot
after both process exits; no file is committed or retained.

This is materially stronger than same-SceneTree save/load and demonstrates
the process lifecycle seam without new game storage code. A packaged
Linux/Windows build, cross-version migration, cloud sync and human player
acceptance remain unverified.

## Real visual LEGO product consumer

Godot TextureRect and Texture2D are the native components. Two actual Kenney
Abstract Platformer CC0 PNG assets, provenance and exact hashes are under
assets/kenney/. The player/foe portraits in both PackedScene HUD variants
display these assets; enemy visibility follows the rule phase through the
same existing state_changed Signal. The alternative HUD swaps blue/green
appearances, and runtime Texture2D replacement leaves authoritative rules
unchanged. Engine import and native acceptance are part of the preexisting
Game test:encounter task; this is not a universal rendering/asset registry.
