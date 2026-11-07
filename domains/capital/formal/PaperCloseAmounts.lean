import Lean

/- Accounting's integer abstraction. Position and pending-entry bounds are
   projections of nonnegative sums. The Python and PostgreSQL consumers
   are exercised separately. -/

private def maxReceiptMinor : Int := 9223372036854775807

private def valuation (cash payable market receivable : Int) : Int :=
  cash - payable + market + receivable

theorem receipt_fields_fit
    (cash reserve payable market receivable shares buyEntry saleEntry : Int)
    (nonnegative : 0 ≤ reserve ∧ 0 ≤ payable ∧ 0 ≤ shares ∧
      0 ≤ buyEntry ∧ 0 ≤ saleEntry)
    (reserveGuard : reserve ≤ cash - payable)
    (components : shares ≤ market ∧ buyEntry ≤ payable ∧ saleEntry ≤ receivable)
    (cashGuard : cash ≤ maxReceiptMinor)
    (navGuard : valuation cash payable market receivable ≤ maxReceiptMinor) :
    0 ≤ cash ∧ reserve ≤ maxReceiptMinor ∧ payable ≤ maxReceiptMinor ∧
      0 ≤ valuation cash payable market receivable ∧
      receivable ≤ maxReceiptMinor ∧ shares ≤ maxReceiptMinor ∧
      buyEntry ≤ maxReceiptMinor ∧ saleEntry ≤ maxReceiptMinor := by
  unfold valuation at *
  omega

theorem settlement_preserves_valuation
    (cash payable market receivable dueBuy dueSell : Int) :
    valuation (cash - dueBuy + dueSell) (payable - dueBuy)
      market (receivable - dueSell) = valuation cash payable market receivable := by
  unfold valuation
  omega

-- The exact signed ceiling is reachable.
example : valuation maxReceiptMinor 0 0 0 = maxReceiptMinor := by decide

-- NAV alone cannot establish that cash fits the receipt.
example : valuation (maxReceiptMinor + 1) 2 1 0 = maxReceiptMinor := by decide
