# G07 formal source cut —Orbit Collector

State = (phase, collected, target, lives) on u2/u64/u64/u8 machine sorts.
Constructor: target > 0 and lives > 0. Invariant:
- Playing: collected < target; lives > 0.
- Won: collected == target; lives > 0.
- Lost: collected < target; lives == 0.
Only Playing admits collect or hit. Collect wins at the target; hit loses at
zero lives; terminal states absorb all actions.

## Specification / Model / Proof
formal/verify_orbit_rules.py runs upstream Z3 4.15.4.0 for nine full-width
bitvector one-step inductive obligations. An UNSAT negated property proves
the model property. UNKNOWN/timeout is not PASS. An explicit falsification
control refutes an impossible Playing state.

Run from domains/game: mise run verify:orbit-smt.

The same actual Rust rules.rs source carries four Kani 0.68.0 harnesses,
activated with cfg(kani): valid construction, collection, damage, terminal
absorption. These must actually pass for source-code proof standing.

Run from domains/game: mise run verify:orbit-kani.

The Z3 model proof alone is NOT actual Rust implementation refinement.
Kani proof applies only to harness assumptions and functions checked.

## Implementation and real consumer
RunState is private and only exposes read-only accessors plus controlled
operations. Bevy ECS gameplay.rs uses these real Rust functions.
mise run test:bevy validates the actual ECS consumer; build:bevy builds it.
Godot G09/G11, native packaging and Human play use independent verification.
Source/consumer binding remains in planning/lego-plan-r1.json; Ordivon
Composition already owns the cross-Owner verification obligation mechanism.
Do not create a parallel Game proof registry or claim rendered gameplay from
these mathematical proofs.


## G10 room-rule signed arithmetic / actual Godot consumer

`formal/verify_room_arithmetic.py` reuses the existing upstream Z3 4.15.4.0
environment and signed **64-bit bitvector** semantics. It proves eleven
one-step obligations on an abstract, source-informed state model:
- precondition: capacity > 0, 0 <= stamina <= capacity, restore > 0,
  nonnegative turn, valid attack cost, health and damage tuning;
- guard gain: `min(restore, capacity - stamina)`, then add. The operation
  remains within bounds and never decreases stamina or overflows;
- turn counter: increment only below `INT64_MAX`, otherwise saturate;
- retaliation preserves nonnegative bounded health; attack stamina
  subtraction remains nonnegative when the attack precondition holds.

A falsification control finds a real machine overflow under the former
`min(capacity, stamina + restore)` formula, at maximal stamina and restore=1.
That bug was independently reproduced in Godot 4.7.2; a restored maximum
turn also wrapped on the next legal action. Run `mise run verify:room-smt`.

The solver output includes the SHA-256 of the current
`examples/room-encounter/encounter_rules.gd` but this is merely a source
identity, **not proof that GDScript refines the Z3 model**. Native bounded
implementation evidence comes from `mise run test:encounter`: the real
scene/rule node exercises `guard()`, `attack()` and
`restore_checkpoint()` with machine-maximal tuning and turn, including
the imported ConfigFile consumer. No theorem for arbitrary GDScript
execution, UI, storage durability or Human enjoyment is claimed.

Reuse Composition's task-local verification obligations; do not create
another Game verifier service or proof registry.

## Tactical Trial native forecast source cut

Existing verify_room_arithmetic.py now uses the same full-width signed
i64 model for pre-action third-turn telegraph, saturation at signed MAX,
normal Guard and perfect charged parry, and bounded HP-loss forecasts.
Seventeen obligations pass under the stated model assumptions, with
negative controls for the legacy overflow and for a model that ignores
the charged third turn. Native test:encounter independently exercises
actual GDScript scene transitions and matches accepted pre-action
forecasts to HP outcomes across 243 Trial and 243 Classic bounded traces. Source SHA-256
identifies code only; universal GDScript refinement, actual graphical
visibility and Human experience remain UNKNOWN. Reuse the existing
Composition gate and G10/G11 source/consumer references.

Classic is a real mode=false refinement: the model checks unchanged base strike and Guard behavior; native Godot acceptance explicitly verifies its third turn and old checkpoint shape.
