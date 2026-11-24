import Lean

/-! Exact natural-number monetary model. No assumptions about market return,
future income, or real-world completeness of supplied obligations. The list
is the obligations admitted through the chosen horizon, including overdue. -/
namespace PortfolioLiabilityReserve

def reserve (emergency : Nat) (obligations : List Nat) : Nat :=
  emergency + obligations.sum

def contribution (cash required requested : Nat) : Nat :=
  min requested (cash - required)

theorem no_more_than_requested (cash required requested : Nat) :
    contribution cash required requested ≤ requested := by
  exact Nat.min_le_left _ _

theorem no_spending_when_underfunded (cash required requested : Nat)
    (h : cash ≤ required) : contribution cash required requested = 0 := by
  simp [contribution, Nat.sub_eq_zero_of_le h]

theorem protects_reserve (cash required requested : Nat)
    (h : required ≤ cash) : required ≤ cash - contribution cash required requested := by
  have hc : contribution cash required requested ≤ cash - required :=
    Nat.min_le_right _ _
  omega

theorem maximal_feasible (cash required requested candidate : Nat)
    (hr : candidate ≤ requested) (hc : candidate + required ≤ cash) :
    candidate ≤ contribution cash required requested := by
  apply Nat.le_min.mpr
  exact ⟨hr, by omega⟩

theorem extra_obligation_cannot_increase_capacity (cash emergency requested extra : Nat)
    (obligations : List Nat) :
    contribution cash (reserve emergency (extra :: obligations)) requested ≤
      contribution cash (reserve emergency obligations) requested := by
  simp only [contribution, reserve, List.sum_cons]
  apply Nat.le_min.mpr
  constructor
  · exact Nat.min_le_left _ _
  · have h := Nat.min_le_right requested (cash - (emergency + (extra + obligations.sum)))
    omega

end PortfolioLiabilityReserve
