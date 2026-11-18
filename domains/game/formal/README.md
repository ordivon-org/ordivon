# Game formal verification — active Godot Room consumer

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
