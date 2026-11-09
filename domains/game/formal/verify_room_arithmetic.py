"""Full signed-i64 proof for the bounded Game room-rule arithmetic *model*.

The goal is machine-arithmetic obligations, not a blanket GDScript proof.
The separate native Godot test executes the actual Rules Node and its
restore/guard/attack consumer with extremal valid tuning and checkpoint state.
A passing solver result does not imply bytecode refinement or frame/GUI effects.
"""
from pathlib import Path
import hashlib

from z3 import And, BitVec, BitVecVal, Bool, If, Not, Solver, sat, unsat

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
# The player-visible intent is derived *before* the action: every third
# turn (turn % 3 == 2) adds one damage, but a zero-damage enemy stays
# harmless and signed i64 maximum saturates rather than overflowing.
THREE = BitVecVal(3, WIDTH)
TWO = BitVecVal(2, WIDTH)
trial_mode = Bool("trial_mode")
charged = turn % THREE == TWO
threat = If(And(trial_mode, charged, enemy_damage > ZERO, enemy_damage < MAX),
            enemy_damage + ONE, enemy_damage)
effective_block = If(And(trial_mode, charged), threat, guard_block)
damage_taken = If(threat > effective_block, threat - effective_block, ZERO)
guard_loss = If(health > damage_taken, damage_taken, health)
next_health = health - guard_loss
foes = BitVec("foes", WIDTH)
enemy_health = BitVec("enemy_health", WIDTH)
attack_damage = BitVec("attack_damage", WIDTH)
final_kill = And(foes == ONE, enemy_health <= attack_damage)
attack_loss = If(final_kill, ZERO, If(health > threat, threat, health))


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
    prove("telegraph_machine_range", valid,
          And(threat >= enemy_damage, threat >= ZERO, threat <= MAX))
    prove("telegraph_exact_schedule_and_saturation", valid,
          If(And(trial_mode, charged, enemy_damage > ZERO, enemy_damage < MAX),
             threat == enemy_damage + ONE, threat == enemy_damage))
    prove("retaliation_nonnegative_damage", valid,
          And(damage_taken >= ZERO, damage_taken <= threat))
    prove("retaliation_health_bound", valid,
          And(next_health >= ZERO, next_health <= health))
    prove("retaliation_terminal_condition", valid,
          (next_health == ZERO) == (damage_taken >= health))
    prove("guard_forecast_equals_hp_delta", valid,
          And(guard_loss >= ZERO, guard_loss <= health,
              next_health == health - guard_loss))
    prove("charged_perfect_parry_absorbs_threat", And(valid, trial_mode, charged),
          And(damage_taken == ZERO, guard_loss == ZERO))
    prove("classic_preserves_historical_damage_and_block", And(valid, Not(trial_mode)),
          And(threat == enemy_damage,
              effective_block == guard_block,
              damage_taken == If(enemy_damage > guard_block,
                                 enemy_damage - guard_block, ZERO)))
    combat_valid = And(valid, foes > ZERO, enemy_health > ZERO, attack_damage > ZERO)
    prove("attack_forecast_in_hp_bounds", combat_valid,
          And(attack_loss >= ZERO, attack_loss <= health,
              If(final_kill, attack_loss == ZERO,
                 attack_loss == If(health > threat, threat, health))))
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
    # A pre-action forecast based solely on enemy_damage would be false for
    # the real charged third turn. Independently force this counterexample.
    bad_intent = Solver()
    bad_intent.add(valid, trial_mode, turn == TWO, enemy_damage == TWO, guard_block == ONE,
                   threat != enemy_damage)
    if bad_intent.check() != sat:
        raise AssertionError("constant-damage forecast negative control not falsified")
    print("GAME_ROOM_SMT_FALSIFIED untelegraphed_third_turn baseline_damage_is_wrong")
    # No guard against silent source edits: include the exact implementation
    # identity in the evidence, but never call a source hash a refinement proof.
    source = Path(__file__).resolve().parents[1] / "examples/room-encounter/encounter_rules.gd"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    print(f"GAME_ROOM_SMT_PASS proved=17 source_sha256={digest} implementation_refinement=NATIVE_BOUNDARY_ONLY")


if __name__ == "__main__":
    main()
