(set-logic QF_LIA)
(set-option :produce-models true)

; Abstract one Paper Accounting daily-close transition over exact integer
; USD minor units. Event identities, time qualification, marks and SERIALIZABLE
; SQL effects are outside this arithmetic proof.
(declare-const oldCash Int)
(declare-const oldProtected Int)
(declare-const oldPayable Int)
(declare-const oldReceivable Int)
(declare-const oldMarkValue Int)
(declare-const newMarkValue Int)
(declare-const contribution Int)
(declare-const reserveContribution Int)
(declare-const duePayable Int)
(declare-const dueReceivable Int)
(declare-const newBuyCost Int)
(declare-const newSellProceeds Int)

(assert (and
  (>= oldCash 0)
  (>= oldProtected 0)
  (>= oldPayable 0)
  (>= oldReceivable 0)
  (>= oldMarkValue 0)
  (>= newMarkValue 0)
  (<= oldProtected (- oldCash oldPayable))
  (>= contribution 0)
  (<= 0 reserveContribution contribution)
  (<= 0 duePayable oldPayable)
  (<= 0 dueReceivable oldReceivable)
  (>= newBuyCost 0)
  (>= newSellProceeds 0)))

; Source correspondence (accounting/paper_close.py::value_session):
; cash += previous.cash_minor - sum(due.values()) + settled_sale_proceeds
; payable = sum(pending.values()) = oldPayable - duePayable + newBuyCost
; receivable = sum(pending_sales.values()) = oldReceivable - dueReceivable
;              + newSellProceeds
; protected += previous.protected_minor
(define-fun nextCash () Int (+ oldCash contribution (- duePayable) dueReceivable))
(define-fun nextPayable () Int (+ (- oldPayable duePayable) newBuyCost))
(define-fun nextReceivable () Int (+ (- oldReceivable dueReceivable) newSellProceeds))
(define-fun nextProtected () Int (+ oldProtected reserveContribution))
(define-fun oldNAV () Int (+ (- oldCash oldPayable) oldReceivable oldMarkValue))
(define-fun nextNAV () Int (+ (- nextCash nextPayable) nextReceivable newMarkValue))
(define-fun liquidityAdmissible () Bool
  (>= (- nextCash nextPayable dueReceivable) nextProtected))

(echo "MODEL_NONVACUOUS")
(push 1)
(assert (and (> duePayable 0) (> dueReceivable 0)
             (> newBuyCost 0) (> newSellProceeds 0) liquidityAdmissible))
(check-sat)
(pop 1)

(echo "NET_ASSET_CONSERVATION")
(push 1)
(assert (not (= (- nextNAV oldNAV)
                (+ contribution (- newBuyCost) newSellProceeds
                   (- newMarkValue oldMarkValue)))))
(check-sat)
(pop 1)

(echo "PURE_SETTLEMENT_DOES_NOT_CREATE_NAV")
(push 1)
(assert (= contribution 0))
(assert (= newBuyCost 0))
(assert (= newSellProceeds 0))
(assert (= newMarkValue oldMarkValue))
(assert (not (= nextNAV oldNAV)))
(check-sat)
(pop 1)

(echo "INTRADAY_LIQUIDITY_EXCLUDES_RECEIVABLE")
(push 1)
(assert (not (= liquidityAdmissible
  (>= (+ (- oldCash oldPayable) contribution (- newBuyCost))
      nextProtected))))
(check-sat)
(pop 1)

; Falsification controls: a wrong guard that spends settlement proceeds
; on the same intraday buy has a realizable counterexample.
(echo "FAULTY_LIQUIDITY_ALLOWANCE_COUNTEREXAMPLE")
(push 1)
(assert (> dueReceivable 0))
(assert (>= (- nextCash nextPayable) nextProtected))
(assert (not liquidityAdmissible))
(check-sat)
(pop 1)

; Falsification controls: duplicating settled receivables in the closing
; NAV instead of removing them from pending sales creates phantom wealth.
(echo "FAULTY_RECEIVABLE_RETAIN_COUNTEREXAMPLE")
(push 1)
(assert (> dueReceivable 0))
(assert (not (= (+ (- nextCash nextPayable)
                   (+ oldReceivable newSellProceeds)
                   newMarkValue)
                (+ oldNAV contribution (- newBuyCost)
                   newSellProceeds (- newMarkValue oldMarkValue)))))
(check-sat)
(pop 1)
