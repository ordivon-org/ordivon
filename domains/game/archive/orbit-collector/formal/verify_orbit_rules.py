"""SMT-bitvector specification proof for Orbit Collector (not Rust code refinement).

Finite-width *full-domain* one-step inductive invariants:
  S=(phase:u2, collected:u64, target:u64, lives:u8).
  pre=(target>0, playing=>collected<target and lives>0, ...).
  Actions: collect, take_hit. They are deterministic and absorbing when terminal.

This proves the mathematical model for all 2^64 values of unsigned counters;
it does NOT establish that the Rust implementation refines this model.
Actual Rust code has Kani proof harnesses and separate engine-native tests.
"""
from z3 import (
    And, BitVec, BitVecVal, If, Not, Or, Solver,
    UGT, ULE, ULT, unsat, sat,
)

PLAYING = BitVecVal(0, 2)
WON = BitVecVal(1, 2)
LOST = BitVecVal(2, 2)
ZERO64 = BitVecVal(0, 64)
ONE64 = BitVecVal(1, 64)
ZERO8 = BitVecVal(0, 8)
ONE8 = BitVecVal(1, 8)
MAX64 = BitVecVal((1 << 64) - 1, 64)

phase = BitVec("phase", 2)
collected = BitVec("collected", 64)
target = BitVec("target", 64)
lives = BitVec("lives", 8)


def inv(p, c, t, l):
    return And(
        UGT(t, ZERO64), ULE(c, t),
        Or(
            And(p == PLAYING, ULT(c, t), UGT(l, ZERO8)),
            And(p == WON, c == t, UGT(l, ZERO8)),
            And(p == LOST, ULT(c, t), l == ZERO8),
        ),
    )


def step_collect(p, c, t, l):
    pc = If(p == PLAYING, c + ONE64, c)
    pp = If(And(p == PLAYING, pc == t), WON, p)
    return pp, pc, t, l


def step_hit(p, c, t, l):
    pl = If(p == PLAYING, l - ONE8, l)
    pp = If(And(p == PLAYING, pl == ZERO8), LOST, p)
    return pp, c, t, pl


def prove(label, premises, property_):
    s = Solver()
    s.set(timeout=30000)
    s.add(premises, Not(property_))
    result = s.check()
    if result != unsat:
        raise AssertionError(f"{label}: {result}; counterexample/unknown: {s.model() if result == sat else s.reason_unknown()}")
    print(f"GAME_ORBIT_SMT_PROVED {label} bitvectors=u64/u8")


def main():
    base = inv(phase, collected, target, lives)
    tpos = UGT(target, ZERO64)
    lpos = UGT(lives, ZERO8)
    prove("valid_initialization", And(tpos, lpos), inv(PLAYING, ZERO64, target, lives))
    prove("collect_invariant", base, inv(*step_collect(phase, collected, target, lives)))
    prove("hit_invariant", base, inv(*step_hit(phase, collected, target, lives)))
    prove("collect_no_overflow", And(base, phase == PLAYING), collected != MAX64)
    prove("hit_no_underflow", And(base, phase == PLAYING), lives != ZERO8)
    prove("win_iff_last_goal", And(base, phase == PLAYING), (step_collect(phase, collected, target, lives)[0] == WON) == (collected == target - ONE64))
    prove("lost_iff_last_life", And(base, phase == PLAYING), (step_hit(phase, collected, target, lives)[0] == LOST) == (lives == ONE8))
    for name, step in (("collect", step_collect), ("hit", step_hit)):
        out = step(phase, collected, target, lives)
        prove(f"terminal_absorbs_{name}", And(base, phase != PLAYING),
              And(out[0] == phase, out[1] == collected, out[2] == target, out[3] == lives))
    # Falsification control: the model must refute a false safety claim.
    s = Solver()
    s.add(inv(phase, collected, target, lives), phase == PLAYING, collected == target)
    if s.check() != unsat:
        raise AssertionError("falsification control did not refute illegal Playing boundary")
    print("GAME_ORBIT_SMT_PASS proved=9 source_refinement=NOT_CLAIMED")


if __name__ == "__main__":
    main()
