import Lean

-- Kernel-checked, all-finite-list integer apportionment algebra for Portfolio.
-- Independent of the number of assets; denominators are strictly positive
-- for conservation, and balances are mathematical Nats rather than Python
-- executable values. This does not establish Python implementation refinement.
-- No axioms, sorry, or custom theorem prover are introduced.

namespace Portfolio

theorem quotient_remainder_total (amount denom qsum rsum : Nat)
    (hdenom : denom > 0)
    (hidentity : amount * denom = qsum * denom + rsum) :
    qsum + rsum / denom = amount := by
  have hmod : rsum % denom = 0 := by
    have h : (qsum * denom + rsum) % denom = 0 := by
      rw [← hidentity]
      simp
    simpa [Nat.add_mod] using h
  have hresidual : rsum = (rsum / denom) * denom := by
    simpa [hmod, Nat.mul_comm] using (Nat.mod_add_div rsum denom).symm
  have hmul : amount * denom = (qsum + rsum / denom) * denom := by
    rw [hidentity, Nat.add_mul]
    omega
  have hcancel := Nat.eq_of_mul_eq_mul_right hdenom hmul
  omega

theorem quotient_remainder_list (amount denom : Nat) (gaps : List Nat) :
    ((gaps.map fun g => (amount * g) / denom).sum) * denom +
    ((gaps.map fun g => (amount * g) % denom).sum) =
    amount * gaps.sum := by
  induction gaps with
  | nil => simp
  | cons g gs ih =>
      simp only [List.map_cons, List.sum_cons, Nat.add_mul, Nat.mul_add]
      have h : (amount * g / denom) * denom + (amount * g % denom) = amount * g := by
        simpa [Nat.add_comm, Nat.mul_comm] using (Nat.mod_add_div (amount * g) denom)
      omega

theorem remainder_sum_bound (amount denom : Nat) (gaps : List Nat)
    (hdenom : denom > 0) :
    ((gaps.map fun g => (amount * g) % denom).sum) + gaps.length ≤
    denom * gaps.length := by
  induction gaps with
  | nil => simp
  | cons g gs ih =>
      simp only [List.map_cons, List.sum_cons, List.length_cons, Nat.mul_succ]
      have hg : (amount * g) % denom < denom := Nat.mod_lt _ hdenom
      omega

theorem base_quota_plus_leftover_conserves (amount denom : Nat)
    (gaps : List Nat) (hdenom : denom > 0)
    (hdenominator : gaps.sum = denom) :
    ((gaps.map fun g => (amount * g) / denom).sum) +
    ((gaps.map fun g => (amount * g) % denom).sum) / denom = amount := by
  have h := quotient_remainder_list amount denom gaps
  rw [hdenominator] at h
  exact quotient_remainder_total amount denom _ _ hdenom h.symm

theorem leftover_lt_asset_count (amount denom : Nat)
    (gaps : List Nat) (hdenom : denom > 0) (hne : gaps ≠ []) :
    ((gaps.map fun g => (amount * g) % denom).sum) / denom < gaps.length := by
  have hbound := remainder_sum_bound amount denom gaps hdenom
  have hpos : gaps.length > 0 := by
    cases gaps with
    | nil => exact False.elim (hne rfl)
    | cons _ _ => simp
  have hlt : ((gaps.map fun g => (amount * g) % denom).sum) <
      denom * gaps.length := by omega
  exact (Nat.div_lt_iff_lt_mul hdenom).mpr (by simpa [Nat.mul_comm] using hlt)

end Portfolio

#print axioms Portfolio.base_quota_plus_leftover_conserves
#print axioms Portfolio.leftover_lt_asset_count
