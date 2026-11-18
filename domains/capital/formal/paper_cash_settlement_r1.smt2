; Finance Paper Accounting R1: cash/receivable/payable conservation.
; Natural source owner: accounting/paper_close.py value_session.
; Solver: upstream Z3, QF_LIA exact unbounded mathematical integers.
; This model aggregates identities only AFTER upstream fill/clock/admission.
; Model proof != Python implementation refinement or deployed PG proof.
(set-logic QF_LIA)
(set-option :produce-models true)

; State at preceding close: settled cash, open payable/receivable,
; mark-to-market position value, and protected reserve (all minor units).
(declare-const c0 Int)
(declare-const p0 Int)
(declare-const r0 Int)
(declare-const v0 Int)
(declare-const q0 Int)

; Today: payment/receivable maturity, deposit and reserve increase,
; new buys/sells, and the current-session mark-to-market decomposition.
(declare-const due-p Int)
(declare-const due-r Int)
(declare-const deposit Int)
(declare-const reserve-add Int)
(declare-const buy-cost Int)
(declare-const sale-proceeds Int)
(declare-const held-price-delta Int)
(declare-const bought-mark Int)
(declare-const sold-mark Int)

; Abstract semantics and finance admission assumptions (QF Presburger).
(assert (and (>= c0 0) (>= p0 0) (>= r0 0) (>= v0 0) (>= q0 0)
             (>= due-p 0) (>= due-r 0) (>= deposit 0) (>= reserve-add 0)
             (>= buy-cost 0) (>= sale-proceeds 0)
             (>= bought-mark 0) (>= sold-mark 0)
             (<= due-p p0) (<= due-r r0)
             (<= p0 c0) (<= q0 (- c0 p0))
             (<= reserve-add deposit)
             (<= sold-mark (+ v0 held-price-delta))))

; These definitions mirror pure Accounting value_session, NOT a new ledger.
(define-fun cash1 () Int (+ c0 deposit (- due-p) due-r))
(define-fun payable1 () Int (+ (- p0 due-p) buy-cost))
(define-fun receivable1 () Int (+ (- r0 due-r) sale-proceeds))
(define-fun protected1 () Int (+ q0 reserve-add))
(define-fun position-value1 () Int (+ v0 held-price-delta bought-mark (- sold-mark)))
(define-fun nav0 () Int (+ c0 (- p0) r0 v0))
(define-fun nav1 () Int (+ cash1 (- payable1) receivable1 position-value1))
(define-fun new-economic-nav () Int
  (+ nav0 deposit held-price-delta (- bought-mark buy-cost)
     (- sale-proceeds sold-mark)))

; PROOF 1: all arbitrary eligible due amounts cancel from economic NAV.
; If sat, Z3 has found a counterexample. Expected: unsat.
(push 1)
(assert (not (= nav1 new-economic-nav)))
(check-sat)
(pop 1)

; PROOF 2: pure settlement (no investment/deposit/price change)
; cannot create or destroy net asset value, irrespective of how much matures.
(push 1)
(assert (= deposit 0))
(assert (= reserve-add 0))
(assert (= buy-cost 0))
(assert (= sale-proceeds 0))
(assert (= held-price-delta 0))
(assert (= bought-mark 0))
(assert (= sold-mark 0))
(assert (not (= nav1 nav0)))
(check-sat)
(pop 1)

; PROOF 3: current source's intraday buying-power fence subtracts
; newly settled sale proceeds before checking protected reserves.
; If it accepts, then unencumbered cash without unsettled receivables
; is nonnegative after the day close. Expected: unsat.
(push 1)
(assert (>= (- cash1 payable1 due-r) protected1))
(assert (< (- cash1 payable1) protected1))
(check-sat)
(pop 1)

; WITNESS 1: omitting unsettled sale receivables from NAV gives a
; different economic valuation; the wrong formula is refutable.
; Expected: sat; the witness means the hypothetical broken model exists.
(push 1)
(assert (> receivable1 0))
(assert (not (= (- nav1 receivable1) nav1)))
(check-sat)
(pop 1)

; WITNESS 2: allowing newly received cash from a settled sale to fund
; an intraday buy passes a weaker check while the actual fenced check rejects.
; This is intentionally SAT, demonstrating the fence is not redundant.
(push 1)
(assert (> due-r 0))
(assert (>= (- cash1 payable1) protected1))
(assert (< (- cash1 payable1 due-r) protected1))
(check-sat)
(pop 1)
