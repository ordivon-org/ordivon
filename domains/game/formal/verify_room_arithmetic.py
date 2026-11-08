"""Full signed-i64 proof for the bounded Game room-rule arithmetic *model*.

The goal is machine-arithmetic obligations, not a blanket GDScript proof.
The separate native Godot test executes the actual Rules Node and its
restore/guard/attack consumer with extremal valid tuning and checkpoint state.
A passing solver result does not imply bytecode refinement or frame/GUI effects.
"""
from pathlib import Path
import hashlib

from z3 import And, BitVec, BitVecVal, If, Not, Solver, sat, unsat

WIDTH = 64
ZERO = BitVecVal(0, WIDTH)
ONE = BitVecVal(1, WIDTH)
MAX = BitVecVal((1 << 63) - 1, WIDTH)
capacity = BitVec("capacity", WIDTH)
stamina = BitVec("stamina", WIDTH)
regain = BitVec("regain", WIDTH)
turn = BitVec("turn", WIDTH)
health = BitVec("health", WIDTH)
enemy_damage = BitVec("enemy_damage", WIDTH)
guard_block = BitVec("guard_block", WIDTH)
attack_cost = BitVec("attack_cost", WIDTH)

# This is the actual accepted tuning's relevant signed-i64 domain, together
# with the state invariant maintained by reset/attack/guard/restore.
valid = And(
    capacity > ZERO,
    stamina >= ZERO,
    stamina <= capacity,
    regain > ZERO,
    turn >= ZERO,
    health > ZERO,
    enemy_damage >= ZERO,
    guard_block >= ZERO,
    attack_cost > ZERO,
    attack_cost <= capacity,
)

remaining = capacity - stamina
gain = If(regain < remaining, regain, remaining)
guard_stamina = stamina + gain
next_turn = If(turn < MAX, turn + ONE, turn)
damage_taken = If(enemy_damage > guard_block, enemy_damage - guard_block, ZERO)
next_health = If(health > damage_taken, health - damage_taken, ZERO)


def prove(name, premise, proposition):
    solver = Solver()
    solver.set(timeout=30000)
    solver.add(premise, Not(proposition))
    result = solver.check()
    if result != unsat:
        detail = solver.model() if result == sat else solver.reason_unknown()
        raise AssertionError(f"{name}: {result}, counterexample/unknown={detail}")
    print(f"GAME_ROOM_SMT_PROVED {name} i64=full_width")


def main():
    prove("remaining_is_nonnegative", valid, And(remaining >= ZERO, remaining <= capacity))
    prove("restoration_respects_remaining_capacity", valid,
          And(gain >= ZERO, gain <= remaining, gain <= regain))
    prove("guard_stamina_in_range", valid,
          And(guard_stamina >= ZERO, guard_stamina <= capacity))
    prove("guard_stamina_monotonic", valid, guard_stamina >= stamina)
    prove("guard_exact_saturation", valid,
          If(regain >= remaining, guard_stamina == capacity,
             guard_stamina == stamina + regain))
    prove("turn_monotone_and_nonnegative", valid,
          And(next_turn >= turn, next_turn >= ZERO, next_turn <= MAX))
    prove("turn_exactly_increments_or_saturates", valid,
          If(turn == MAX, next_turn == turn, next_turn == turn + ONE))
    prove("retaliation_nonnegative_damage", valid,
          And(damage_taken >= ZERO, damage_taken <= enemy_damage))
    prove("retaliation_health_bound", valid,
          And(next_health >= ZERO, next_health <= health))
    prove("retaliation_terminal_condition", valid,
          (next_health == ZERO) == (damage_taken >= health))
    attack_valid = And(valid, stamina >= attack_cost)
    after_attack = stamina - attack_cost
    prove("attack_stamina_nonnegative", attack_valid,
          And(after_attack >= ZERO, after_attack <= capacity))

    # Negative control: the previous implementation overflowed at the exact
    # admissible extreme independently observed in native Godot 4.7.2.
    old_guard = If(capacity < stamina + regain, capacity, stamina + regain)
    witness = Solver()
    witness.add(valid, capacity == MAX, stamina == MAX, regain == ONE,
                old_guard < ZERO)
    if witness.check() != sat:
        raise AssertionError("legacy guard arithmetic overflow falsification control failed")
    print("GAME_ROOM_SMT_FALSIFIED legacy_guard_math i64_max_plus_one_wraps_negative")
    # No guard against silent source edits: include the exact implementation
    # identity in the evidence, but never call a source hash a refinement proof.
    source = Path(__file__).resolve().parents[1] / "examples/room-encounter/encounter_rules.gd"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    print(f"GAME_ROOM_SMT_PASS proved=11 source_sha256={digest} implementation_refinement=NATIVE_BOUNDARY_ONLY")


if __name__ == "__main__":
    main()
