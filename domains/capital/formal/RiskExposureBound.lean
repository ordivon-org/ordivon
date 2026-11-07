import Lean

-- Source-adjacent algebra for Capital Risk build_exposure_ledger.
-- Mathematical integer notionals; does NOT prove Python Decimal refinement,
-- decimal string formatting, external provider data, or broker effects.
namespace Capital.Risk

def net (positions : List Int) : Int := positions.sum
def gross (positions : List Int) : Nat := (positions.map Int.natAbs).sum

-- Independent position sets compose without hidden portfolio-global state.
theorem net_append (xs ys : List Int) :
    net (xs ++ ys) = net xs + net ys := by
  simp [net, List.sum_append]

theorem gross_append (xs ys : List Int) :
    gross (xs ++ ys) = gross xs + gross ys := by
  simp [gross, List.map_append, List.sum_append]

-- Arbitrary finite position lists, not a fixed three-asset sample:
-- netting cannot increase absolute notional exposure.
theorem net_abs_le_gross (positions : List Int) :
    Int.natAbs (net positions) ≤ gross positions := by
  induction positions with
  | nil => simp [net, gross]
  | cons x xs ih =>
      change Int.natAbs (x + xs.sum) ≤
        x.natAbs + (xs.map Int.natAbs).sum
      have tail_bound : Int.natAbs xs.sum ≤
          (xs.map Int.natAbs).sum := by
        simpa only [net, gross] using ih
      exact Nat.le_trans (Int.natAbs_add_le x xs.sum)
        (Nat.add_le_add_left tail_bound x.natAbs)

end Capital.Risk

#print axioms Capital.Risk.net_append
#print axioms Capital.Risk.gross_append
#print axioms Capital.Risk.net_abs_le_gross
