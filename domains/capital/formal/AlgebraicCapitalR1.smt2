; Algebraic Capital owner — structural real-number obligations, NO risk thresholds.
; This model represents a normalized 1r equity and two long risky assets.
; Not a broker, market data, or floating-point Python implementation proof.
(set-logic QF_NRA)
(declare-const w1 Real)
(declare-const w2 Real)
(declare-const c Real)
(declare-const b Real)
(declare-const k1 Real)
(declare-const k2 Real)
(declare-const t1 Real)
(declare-const t2 Real)
(declare-const d1 Real)
(declare-const d2 Real)
(declare-const m1 Real)
(declare-const m2 Real)
(declare-const U Real)
(declare-const N Real)
(declare-const F Real)
(declare-const deltaN Real)
(declare-const mu Real)
(declare-const lending Real)
(declare-const gamma Real)
(declare-const variance Real)
(declare-const exposure Real)
(assert (and (>= w1 0) (>= w2 0) (>= c 0) (>= b 0)))
(assert (and (>= k1 0) (>= k2 0) (>= t1 0) (>= t2 0)))
(assert (and (>= d1 0) (<= d1 1) (>= d2 0) (<= d2 1)))
(assert (and (>= m1 0) (<= m1 1) (>= m2 0) (<= m2 1)))
; Exact normalized self-financing budget (all quantities measured in 1r).
(define-fun fees () Real (+ (* k1 t1) (* k2 t2)))
(define-fun initial_budget () Real (- (+ w1 w2 c fees) b))
(assert (= initial_budget 1))
; Short-horizon zero-interest downside mark; interest is separate in implementation.
(define-fun equity_after () Real
  (- (+ (* w1 (- 1 d1)) (* w2 (- 1 d2)) c) b))
(define-fun eq_factored () Real
  (- 1 fees (* w1 d1) (* w2 d2)))
(define-fun headroom () Real
  (- equity_after
     (+ (* m1 w1 (- 1 d1)) (* m2 w2 (- 1 d2)))))
(define-fun headroom_factored () Real
  (- 1 fees
     (* w1 (+ d1 (* m1 (- 1 d1))))
     (* w2 (+ d2 (* m2 (- 1 d2))))))

; P1: Post-trade equity and shock P&L must conserve 1r.
(push 1)
(assert (not (= equity_after eq_factored)))
(check-sat)
(pop 1)

; P2: Asset-wise provider-maintenance postshock inequality factorization.
(push 1)
(assert (not (= headroom headroom_factored)))
(check-sat)
(pop 1)

; P3: A fresh external contribution F=U*deltaN changes shares/units only.
(push 1)
(assert (> U 0))
(assert (>= N 0))
(assert (>= F 0))
(assert (>= deltaN 0))
(assert (= F (* U deltaN)))
(assert (not (= (+ (* U N) F) (* U (+ N deltaN)))))
(check-sat)
(pop 1)

; P4: No positive Merton interior derivative when risky drift <= cash rate.
(push 1)
(assert (> gamma 0))
(assert (> variance 0))
(assert (>= exposure 0))
(assert (<= mu lending))
(assert (> (- (- mu lending) (* gamma variance exposure)) 0))
(check-sat)
(pop 1)

; P5: With a positive loan and no protective cash, a possible simultaneous
; total loss of risky assets makes solvent continuous margin impossible.
(push 1)
(assert (> (+ w1 w2) 1))
(assert (= c 0))
(assert (= d1 1))
(assert (= d2 1))
(assert (>= headroom 0))
(check-sat)
(pop 1)

; Counterexample witness: such an underwater leveraged state actually exists.
(push 1)
(assert (> (+ w1 w2) 1))
(assert (= c 0))
(assert (= d1 1))
(assert (= d2 1))
(assert (< headroom 0))
(check-sat)
(pop 1)
