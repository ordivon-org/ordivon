; Research read-only Qlib H5/H20 label overlap abstraction.
; Sessions and ex-dates are INTEGER calendar indices already qualified by
; native Markets date validation; this DOES NOT authenticate issuer metadata,
; first publisher publication time, holdings, payment/withholding or total return.
(set-logic QF_LIA)
(declare-const decision-index Int)
(declare-const entry-index Int)
(declare-const exit-index Int)
(declare-const ex-date-index Int)
(declare-const horizon Int)
(define-fun same-economic-holding () Bool
  (and (or (= horizon 5) (= horizon 20))
       (= entry-index (+ decision-index 1))
       (= exit-index (+ decision-index horizon 1))))
(define-fun eligible-for-observed-event () Bool
  (and (< entry-index ex-date-index)
       (<= ex-date-index exit-index)))

; 1: Entering at OPEN on ex-date cannot accrue that declared distribution.
(push 1)
(assert same-economic-holding)
(assert (= entry-index ex-date-index))
(assert eligible-for-observed-event)
(check-sat)
(pop 1)

; 2: Ex-date after the next-open exit is not part of the held window.
(push 1)
(assert same-economic-holding)
(assert (> ex-date-index exit-index))
(assert eligible-for-observed-event)
(check-sat)
(pop 1)

; 3: A date before or at entry never qualifies under a buy-at-open contract.
(push 1)
(assert same-economic-holding)
(assert (<= ex-date-index entry-index))
(assert eligible-for-observed-event)
(check-sat)
(pop 1)

; 4: Eligible decision indices for one ex-date must be within an interval
; of H sessions: ex-(H+1) <= T <= ex-2. No single event contaminates
; more than H candidate windows on a complete exchange-session index.
(push 1)
(assert same-economic-holding)
(assert eligible-for-observed-event)
(assert (or (< decision-index (- ex-date-index horizon 1))
            (> decision-index (- ex-date-index 2))))
(check-sat)
(pop 1)

; 5: Selling next-open exactly ON ex-date keeps the already accrued
; entitlement from owning the fund before its ex-date (SAT).
(push 1)
(assert same-economic-holding)
(assert (= ex-date-index exit-index))
(assert eligible-for-observed-event)
(check-sat)
(pop 1)

; 6: Old wrong heuristic "entry <= exDate < exit" would accidentally
; admit buying at the ex-date open (SAT counterexample).
(push 1)
(assert same-economic-holding)
(assert (= entry-index ex-date-index))
(assert (<= entry-index ex-date-index))
(assert (< ex-date-index exit-index))
(assert (not eligible-for-observed-event))
(check-sat)
(pop 1)
