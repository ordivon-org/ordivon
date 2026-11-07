; Research Unit-R: turnover-adjusted rebalance, modeled over exact reals.
; One-period algebra only: independent of historical price truth, broker margin,
; finite floating point and whether an Agent can execute the trade.
(set-logic QF_NRA)
(set-option :timeout 15000)
(declare-const equity Real)
(declare-const previous Real)
(declare-const target Real)
(declare-const fee Real)
(declare-const initialMargin Real)
(define-fun admitted () Bool
 (and (> equity 0) (>= previous 0)
      (>= target 0) (<= target 2)
      (>= fee 0) (< fee (/ 1 20))
      (> equity (* fee previous))
      (> initialMargin 0) (<= initialMargin 1)
      (<= (* target initialMargin) 1)))
(define-fun buy () Real (/ (* target (+ equity (* fee previous))) (+ 1 (* target fee))))
(define-fun sell () Real (/ (* target (- equity (* fee previous))) (- 1 (* target fee))))
(define-fun buying () Bool (>= (* target equity) previous))
(define-fun afterBuy () Real (- equity (* fee (- buy previous))))
(define-fun afterSell () Real (- equity (* fee (- previous sell))))

; The buying branch is the exact fee-adjusted target equation.
(push 1) (assert admitted) (assert buying)
(assert (not (= buy (* target afterBuy)))) (check-sat) (pop 1)
; Buy region is self-consistent, and net equity stays positive.
(push 1) (assert admitted) (assert buying)
(assert (or (< buy previous) (<= afterBuy 0))) (check-sat) (pop 1)
; The selling branch is the exact fee-adjusted target equation.
(push 1) (assert admitted) (assert (not buying))
(assert (not (= sell (* target afterSell)))) (check-sat) (pop 1)
; Sell region is self-consistent and does not create a short position.
(push 1) (assert admitted) (assert (not buying))
(assert (or (< sell 0) (> sell previous) (<= afterSell 0))) (check-sat) (pop 1)
; Both branches preserve initial margin if the requested target obeys it.
(push 1) (assert admitted) (assert buying)
(assert (> (* initialMargin buy) afterBuy)) (check-sat) (pop 1)
(push 1) (assert admitted) (assert (not buying))
(assert (> (* initialMargin sell) afterSell)) (check-sat) (pop 1)
; Cash/debt split always reconciles position exposure and post-trade equity.
(declare-const gross Real) (declare-const postEquity Real)
(define-fun cash () Real (ite (>= postEquity gross) (- postEquity gross) 0))
(define-fun debt () Real (ite (> gross postEquity) (- gross postEquity) 0))
(push 1) (assert (>= postEquity 0)) (assert (>= gross 0))
(assert (not (= (- (+ gross cash) debt) postEquity))) (check-sat) (pop 1)
; Nonvacuous buy and sell examples must exist under these assumptions.
(push 1) (assert admitted) (assert buying) (assert (> buy previous))
(assert (> fee 0)) (check-sat) (pop 1)
(push 1) (assert admitted) (assert (not buying)) (assert (< sell previous))
(assert (> fee 0)) (check-sat) (pop 1)
