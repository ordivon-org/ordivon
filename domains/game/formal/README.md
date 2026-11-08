# G07 formal source cut 鈥?Orbit Collector

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
