# Godot native composition example — not a registered game product

**Consumer:** Game Agent assembling state/action/time/observation LEGO from a
mature engine and making gameplay/resources/player presentation replaceable.

Use upstream Godot and native Node, Signal, Resource, PackedScene and built-in
UI. This is runnable consumer acceptance, not a generic game or mod platform.

Run from domains/game:
    mise run test:native
    godot --path examples/native-composition

Keyboard: left/right through the Godot project InputMap (actions
`move_left` / `move_right`); bindings can be remapped without changing rules.
`configs/base.tres` defines default goal, energy, step cost and turn limit. The test substitutes configs/player_variant.tres
and view_variant.tscn without changing the state transition implementation.
A player may edit native resources or select another native presentation.
A new ruleset may instead supply its own scene and rule semantics.

**Strict LEGO R2.1 game-rule consumer (this fixture only):** the gameplay
responsibility consumes a typed native Godot config Resource and legal
action, and produces bounded state plus a state-change Signal. Its admission
guarantee is that a candidate outside the actual config script type or
base numeric parameter invariants is rejected, preserving snapshot,
events and UI. A valid native subclass remains replaceable; overriding
is_valid() cannot self-certify an invalid subclass. Admitted Resources are
deep-copied, so later caller mutation does not silently rewrite live rules
without an explicit reset. This reuses Godot native capabilities, not a
second Mod Runtime or configuration registry.

**Exact bounded test:** load a real Godot PackedScene, reject illegal actions
and invalid substitutions without state changes, check a winning path,
run the same rules with player-supplied data, substitute a native presentation
scene, then explore all 2^6 length-6 left/right action sequences under the
default configuration and check position, energy, turn and phase invariants.
This is bounded executable evidence, not a mathematical proof of arbitrary
game rules, accessibility, or human enjoyment.

**Natural Owners:** Godot owns scene, render, input, signal and Resource
execution. A game product owns its own rules and goals. UI, media and audio
assets come from their natural domains; introduce concrete consumers before
wiring new packages. No universal rules registry was created.


## Exact composition and replaceable seams

| Role | Native component | Exposed contract | Replacement point |
| --- | --- | --- | --- |
| Composition root/input | project.godot InputMap + composition_root.gd + main.tscn | Native named actions drive rule port; root wires state signal to view | Remap native InputMap/device without rewriting rules, audio or view |
| Rule/state | grid_rules.gd | reset_game(Resource), move(int), snapshot(), state_changed(Dictionary) | Replace rules with another valid game contract |
| Configuration | grid_config.gd + configs/base.tres | Typed, validated bounds/energy/goal parameters | configs/player_variant.tres |
| Presentation | grid_state_view.gd + grid_state_view.tscn | render_state(Dictionary) | grid_state_view_variant.tscn |
| Native audio feedback | main.tscn + movement_audio_feedback.gd + two Kenney CC0 WAV clips | accepted turn via state_changed -> AudioStreamPlayer.play() | swap AudioStream without editing grid_rules.gd |
| Native source-licensed UI action | grid_state_view.tscn + one Kenney CC0 PNG + composition_root.gd | TextureButton.pressed -> grid_rules.move(1) -> existing state/audio consumers | swap button visual/scene without editing rules or MovementAudio |
| Consumer falsifier | assert.gd | Native scenario/state/Resource/view substitution checks | Extend only for a real changed contract |

This is an executable end-to-end **input -> state transition -> Signal -> UI**
composition; it does not claim to be a generic engine or a complete game.
Run `mise run test:native` from domains/game to exercise both the default
and the player-supplied configuration and alternate presentation, including
physical-key and remapped-key native input dispatch. For a visible scene run `godot --path examples/native-composition` from domains/game.

**Composition recipe A (existing, executed):** default grid configuration +
native rule node + default presentation. Right moves advance toward a goal;
left moves modify position under energy/turn constraints.

**Composition recipe B (existing, executed):** identical rule implementation +
player_variant.tres + grid_state_view_variant.tscn. Acceptance asserts
bounded invariants and observable behavior while substituting source-native
data and presentation; this demonstrates modularity without maintaining a
parallel wrapper or copy of the game logic.

**Now executed:** `main.tscn` installs native source-licensed audio feedback in
the ordinary interactive scene. `assert_audio.gd` verifies actual keyboard
input, sound routing, rejection and clip replacement. A future game can
replace remaining rules, scenes, artwork and writing through mature providers;
this example still is not a shipped game.


## Real external media composition without duplicate subsystem

One 192 x 64 PNG from the **Kenney UI Pack 2.0**, CC0 at
https://kenney.nl/assets/ui-pack, is obtained from the public source mirror
https://github.com/shorepine/kenney at immutable Git commit
`3694c6879e487c108f55677be7dd2ca75b07cc3b`, upstream relative path
`ui/UI Pack/Blue/button_rectangle_depth_border.png`. Local source:
`assets/kenney-ui-art/button_rectangle_depth_border.png`, SHA256
`19dd881d5c38d58e93db451152356a8ecb1375b247615d4e340b678233398b01`.
The original author is Kenney; source mirror packaging and credit do not
transfer artistic ownership.

The existing native `MovementAudio` system and its pinned Kenney CC0 clips
(`click1.wav`, `click2.wav`) remain the **only** audio feedback producer.
The default view owns one `TextureButton`. The existing composition root
binds its pressed event to existing grid rules, which notify both the view
and existing `MovementAudio` through the state-change signal. Alternate
presentation may omit the button. There is no duplicate AudioStreamPlayer,
audio file, rules provider or Game UI engine.

The existing `assert_audio.gd` exercises native button press → game-state
change → rendered board → existing audio feedback, with real Godot resources.
`Image.load_from_file` supports source/headless fixture tests; Godot's 4.7
docs recommend properly imported textures for exported packaged games, which
are not established here. This is not a shipped game or human UX result.
