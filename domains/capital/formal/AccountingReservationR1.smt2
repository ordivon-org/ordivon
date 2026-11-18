; Capital Accounting reservation and two-phase settlement, exact integer model.
; Owner: domains/capital/accounting. MODEL only, not proof of Python/PG/ broker.
(set-logic QF_LIA)
(set-option :timeout 15000)
(declare-const budget Int)
(declare-const spent Int)
(declare-const pending Int)
(declare-const amount Int)
(declare-const status Int)
(define-fun inv ((b Int) (s Int) (p Int)) Bool
  (and (>= b 0) (>= s 0) (>= p 0) (<= (+ s p) b)))
(define-fun reserve-pending ((b Int) (s Int) (p Int) (a Int)) Int
  (ite (and (> a 0) (<= (+ s p a) b)) (+ p a) p))
(define-fun post-status ((st Int)) Int (ite (= st 1) 2 st))
(define-fun void-status ((st Int)) Int (ite (= st 1) 3 st))

; 1: conditional reserve preserves all balances and budget constraints.
(push 1)
(assert (inv budget spent pending)) (assert (> amount 0))
(assert (not (inv budget spent (reserve-pending budget spent pending amount))))
(check-sat)
(pop 1)

; 2: rejected reservation leaves pending balances unchanged.
(push 1)
(assert (inv budget spent pending)) (assert (> amount 0))
(assert (> (+ spent pending amount) budget))
(assert (not (= (reserve-pending budget spent pending amount) pending)))
(check-sat)
(pop 1)

; 3: posting a previously reserved amount preserves the available-funds fence.
(push 1)
(assert (inv budget spent pending)) (assert (> amount 0))
(assert (<= amount pending))
(assert (not (inv budget (+ spent amount) (- pending amount))))
(check-sat)
(pop 1)

; 4: voiding a pending amount restores reservation headroom.
(push 1)
(assert (inv budget spent pending)) (assert (> amount 0))
(assert (<= amount pending))
(assert (not (inv budget spent (- pending amount))))
(check-sat)
(pop 1)

; 5: POST moves pending to spent without creating/destroying counted funds.
(push 1)
(assert (inv budget spent pending)) (assert (> amount 0))
(assert (<= amount pending))
(assert (not (= (+ (+ spent amount) (- pending amount)) (+ spent pending))))
(check-sat)
(pop 1)

; 6: POST replay does not make a second transition.
(push 1)
(assert (<= 0 status)) (assert (<= status 3))
(assert (not (= (post-status (post-status status)) (post-status status))))
(check-sat)
(pop 1)

; 7: POST -> VOID cannot create a second successful resolution.
(push 1)
(assert (<= 0 status)) (assert (<= status 3))
(assert (not (= (void-status (post-status status)) (post-status status))))
(check-sat)
(pop 1)

; 8: deliberately wrong unconditional RESERVE overdrafts budget: SAT witness.
(push 1)
(assert (= budget 1000)) (assert (= spent 0)) (assert (= pending 300))
(assert (= amount 800))
(assert (not (inv budget spent (+ pending amount))))
(check-sat)
(pop 1)

; 9: deliberately wrong unconditional POST creates negative pending: SAT witness.
(push 1)
(assert (= budget 1000)) (assert (= spent 0)) (assert (= pending 300))
(assert (= amount 800))
(assert (not (inv budget (+ spent amount) (- pending amount))))
(check-sat)
(pop 1)
