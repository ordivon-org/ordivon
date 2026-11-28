; Capital Portfolio multistage monthly 1r / two-scenario self-financing.
; A finite-scenario real-arithmetic representation witness, NOT a SciPy proof.
; All variables are r-valued amounts or dimensionless gross returns.
(set-logic QF_NRA)
(declare-const a0 Real)
(declare-const c0 Real)
(declare-const b0 Real)
(declare-const f0 Real)
(declare-const aA Real)
(declare-const cA Real)
(declare-const bA Real)
(declare-const fA Real)
(declare-const aB Real)
(declare-const cB Real)
(declare-const bB Real)
(declare-const fB Real)
(declare-const GA Real)
(declare-const GB Real)
(declare-const GLA Real)
(declare-const GLB Real)
(declare-const GBA Real)
(declare-const GBB Real)
(declare-const G2A Real)
(declare-const GL2A Real)
(declare-const GB2A Real)
(declare-const G2B Real)
(declare-const GL2B Real)
(declare-const GB2B Real)
(declare-const mA Real)
(declare-const mB Real)

; Root and each child receive exactly one new 1r at the actual decision time.
(assert (= (+ a0 c0 (- b0) f0) 1))
(define-fun preA () Real (+ (* a0 GA) (* c0 GLA) (- (* b0 GBA))))
(define-fun preB () Real (+ (* a0 GB) (* c0 GLB) (- (* b0 GBB))))
(assert (= (+ aA cA (- bA) fA) (+ preA 1)))
(assert (= (+ aB cB (- bB) fB) (+ preB 1)))
(define-fun postA () Real (+ aA cA (- bA)))
(define-fun postB () Real (+ aB cB (- bB)))
(define-fun tA () Real (+ (* aA G2A) (* cA GL2A) (- (* bA GB2A))))
(define-fun tB () Real (+ (* aB G2B) (* cB GL2B) (- (* bB GB2B))))

; P1: Future gross outcomes minus trade costs are consistent with
; before-trade equity plus 1r, not with an extra fictitious profit.
(push 1)
(assert (not (= postA (- (+ preA 1) fA))))
(check-sat)
(pop 1)

; P2: The same conservation holds for another observed child branch,
; whose previous risky holdings are the SAME a0 decision.
(push 1)
(assert (not (= postB (- (+ preB 1) fB))))
(check-sat)
(pop 1)

; P3/P4: Complete terminal wealth factorizes as post-trade equity plus
; actual risky/cash/borrowing gains across the last observed transition.
(push 1)
(assert (not (= tA
  (+ postA (* aA (- G2A 1)) (* cA (- GL2A 1)) (- (* bA (- GB2A 1)))))))
(check-sat)
(pop 1)
(push 1)
(assert (not (= tB
  (+ postB (* aB (- G2B 1)) (* cB (- GL2B 1)) (- (* bB (- GB2B 1)))))))
(check-sat)
(pop 1)

; P5: Contribution 1r at A cannot change the *pre-contribution*
; incoming margin headroom, which is entirely parent-owned.
(define-fun Hbefore () Real (- preA (* mA a0 GA)))
(define-fun HafterHypotheticalRescue () Real (+ Hbefore 1))
(push 1)
(assert (not (= (- HafterHypotheticalRescue Hbefore) 1)))
(check-sat)
(pop 1)

; Wrong-model SAT counterexample: a levered position fails before next 1r
; (margin headroom negative) but would appear eligible if a later deposit
; were illegally used to retroactively cure the earlier failure.
(push 1)
(assert (= a0 2))
(assert (= c0 0))
(assert (= b0 1))
(assert (= f0 0))
(assert (= GA (/ 1 5)))
(assert (= GLA 1))
(assert (= GBA 1))
(assert (= mA (/ 2 5)))
(assert (< Hbefore 0))
(assert (>= HafterHypotheticalRescue 0))
(check-sat)
(pop 1)
