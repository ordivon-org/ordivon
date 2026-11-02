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
