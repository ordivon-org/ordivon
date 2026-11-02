# Godot native composition example — not a registered game product

**Consumer:** Game Agent assembling state/action/time/observation LEGO from a
mature engine and making gameplay/resources/player presentation replaceable.

Use upstream Godot and native Node, Signal, Resource, PackedScene and built-in
UI. This is runnable consumer acceptance, not a generic game or mod platform.

Run from domains/game:
    mise run test:native
    godot --path examples/native-composition

Keyboard: left/right. configs/base.tres defines default goal, energy,
step cost and turn limit. The test substitutes configs/player_variant.tres
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
| Composition root/input | composition_root.gd + main.tscn | Receives left/right and connects state signal to view | Supply another root/engine input mapping |
| Rule/state | grid_rules.gd | reset_game(Resource), move(int), snapshot(), state_changed(Dictionary) | Replace rules with another valid game contract |
| Configuration | grid_config.gd + configs/base.tres | Typed, validated bounds/energy/goal parameters | configs/player_variant.tres |
| Presentation | grid_state_view.gd + grid_state_view.tscn | render_state(Dictionary) | grid_state_view_variant.tscn |
| Consumer falsifier | assert.gd | Native scenario/state/Resource/view substitution checks | Extend only for a real changed contract |

This is an executable end-to-end **input -> state transition -> Signal -> UI**
composition; it does not claim to be a generic engine or a complete game.
Run `mise run test:native` from domains/game to exercise both the default
and the player-supplied configuration and alternate presentation. For a visible
scene run `godot --path examples/native-composition` from domains/game.

**Composition recipe A (existing, executed):** default grid configuration +
native rule node + default presentation. Right moves advance toward a goal;
left moves modify position under energy/turn constraints.

**Composition recipe B (existing, executed):** identical rule implementation +
player_variant.tres + grid_state_view_variant.tscn. Acceptance asserts
bounded invariants and observable behavior while substituting source-native
data and presentation; this demonstrates modularity without maintaining a
parallel wrapper or copy of the game logic.

**Next actual consumer:** a new game may reuse the composition boundary and
replace rules, scene, artwork, audio and writing with native Godot providers.
Do not describe that future combination as implemented until its own scene,
resources and actual integration have executed. Do not import speculative
third-party packages into this example merely to grow the inventory.
