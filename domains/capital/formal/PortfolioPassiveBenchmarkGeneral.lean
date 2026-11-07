import Lean

/-!
Finite-list (arbitrary period count) economic transition specification for the
Portfolio passive benchmark. Rat models exact fractions, NOT Python Decimal
context rounding. A separate Python consumer-refinement witness is required.
-/

namespace PortfolioPassiveBenchmark

structure Period where
  deposit : Rat
  strategyReturn : Rat
  benchmarkReturn : Rat
  strategyExpense : Rat
  benchmarkExpense : Rat
  strategyFee : Rat
  benchmarkFee : Rat

structure State where
  strategy : Rat
  benchmark : Rat
  contributed : Rat

def nextValue (capital deposit grossReturn expense fixedFee : Rat) : Rat :=
  ((capital + deposit) * (1 - expense) - fixedFee) * (1 + grossReturn)

def step (s : State) (p : Period) : State :=
  { strategy := nextValue s.strategy p.deposit p.strategyReturn p.strategyExpense p.strategyFee
    benchmark := nextValue s.benchmark p.deposit p.benchmarkReturn p.benchmarkExpense p.benchmarkFee
    contributed := s.contributed + p.deposit }

def replay (s : State) (periods : List Period) : State :=
  periods.foldl step s

def equalDrivers (p : Period) : Prop :=
  p.strategyReturn = p.benchmarkReturn ∧
  p.strategyExpense = p.benchmarkExpense ∧
  p.strategyFee = p.benchmarkFee

-- For every finite sequence, deposits are external contributions, never
-- strategy gains, independently of either strategy's returns and fees.
theorem cash_conservation (s : State) (periods : List Period) :
    (replay s periods).contributed = s.contributed + (periods.map (·.deposit)).sum := by
  induction periods generalizing s with
  | nil => simp [replay, Rat.add_zero]
  | cons p ps ih =>
      change (replay (step s p) ps).contributed =
        s.contributed + (p :: ps |>.map (·.deposit)).sum
      rw [ih]
      simp only [step, List.map_cons, List.sum_cons]
      exact Rat.add_assoc _ _ _

-- Identical driver paths, with the same opening wealth, cannot create an
-- unexplained relative advantage at any period count.
theorem equal_step (s : State) (p : Period)
    (hs : s.strategy = s.benchmark) (hp : equalDrivers p) :
    (step s p).strategy = (step s p).benchmark := by
  rcases hp with ⟨hr, he, hf⟩
  simp only [step]
  rw [hs, hr, he, hf]

theorem equal_paths (s : State) (periods : List Period)
    (hstart : s.strategy = s.benchmark)
    (hdrivers : ∀ p ∈ periods, equalDrivers p) :
    (replay s periods).strategy = (replay s periods).benchmark := by
  induction periods generalizing s with
  | nil => simpa [replay] using hstart
  | cons p ps ih =>
      have hp : equalDrivers p := hdrivers p (by simp)
      have ht : ∀ q ∈ ps, equalDrivers q := by
        intro q hq
        exact hdrivers q (by simp [hq])
      exact ih (step s p) (equal_step s p hstart hp) ht

-- Both reported net gains remove *the same* external contribution baseline.
theorem matched_gain_difference (strategy benchmark contributed : Rat) :
    (strategy - contributed) - (benchmark - contributed) = strategy - benchmark := by
  calc
    (strategy - contributed) - (benchmark - contributed) =
        (strategy + -contributed) + (-benchmark + contributed) := by
      simp only [Rat.sub_eq_add_neg, Rat.neg_add, Rat.neg_neg]
    _ = (strategy + -benchmark) + (-contributed + contributed) := by ac_rfl
    _ = strategy - benchmark := by
      simp [Rat.neg_add_cancel, Rat.add_zero, Rat.sub_eq_add_neg]

-- The declared admission relation is evaluated on the *current* state,
-- rather than assuming a fixed opening balance for every period.
def admitted (s : State) (p : Period) : Prop :=
  0 ≤ ((s.strategy + p.deposit) * (1 - p.strategyExpense) - p.strategyFee) ∧
  0 ≤ (1 + p.strategyReturn) ∧
  0 ≤ ((s.benchmark + p.deposit) * (1 - p.benchmarkExpense) - p.benchmarkFee) ∧
  0 ≤ (1 + p.benchmarkReturn) ∧
  0 ≤ p.deposit

noncomputable def checkedStep (s : State) (p : Period) : Option State := by
  classical
  exact if admitted s p then some (step s p) else none

noncomputable def checkedReplay (s : State) (periods : List Period) : Option State :=
  periods.foldl (fun current p => current.bind (fun st => checkedStep st p)) (some s)

theorem checked_step_nonneg (s : State) (p : Period) (next : State)
    (h : checkedStep s p = some next) :
    0 ≤ next.strategy ∧ 0 ≤ next.benchmark := by
  unfold checkedStep at h
  split at h
  · rename_i hadmit
    cases h
    constructor
    · exact Rat.mul_nonneg hadmit.1 hadmit.2.1
    · exact Rat.mul_nonneg hadmit.2.2.1 hadmit.2.2.2.1
  · cases h

theorem none_absorbing (periods : List Period) :
    periods.foldl (fun current p => current.bind (fun st => checkedStep st p))
      (none : Option State) = none := by
  induction periods with
  | nil => rfl
  | cons p ps ih => simpa [List.foldl_cons] using ih

theorem accepted_nonneg (s : State) (periods : List Period) (final : State)
    (hstart : 0 ≤ s.strategy ∧ 0 ≤ s.benchmark)
    (h : checkedReplay s periods = some final) :
    0 ≤ final.strategy ∧ 0 ≤ final.benchmark := by
  induction periods generalizing s with
  | nil =>
      have heq : s = final := Option.some.inj (by simpa [checkedReplay] using h)
      rw [← heq]
      exact hstart
  | cons p ps ih =>
      cases hs : checkedStep s p with
      | none =>
          simp [checkedReplay, List.foldl_cons, hs, none_absorbing] at h
      | some next =>
          have hn := checked_step_nonneg s p next hs
          apply ih next hn
          simpa [checkedReplay, hs] using h

end PortfolioPassiveBenchmark

#print axioms PortfolioPassiveBenchmark.cash_conservation
#print axioms PortfolioPassiveBenchmark.equal_paths
#print axioms PortfolioPassiveBenchmark.matched_gain_difference
#print axioms PortfolioPassiveBenchmark.accepted_nonneg
