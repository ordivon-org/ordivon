# Godot native LEGO assembly acceptance — not a game product

**Consumer:** Game Agent assembling state/action/time/observation LEGO from a
mature engine and making gameplay/resources/player presentation replaceable.

Use upstream Godot and native Node, Signal, Resource, PackedScene and built-in
UI. This is runnable consumer acceptance, not a generic game or mod platform.

Run from domains/game:
    mise run test:native
    godot --path test/fixtures/native-godot-assembly

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
