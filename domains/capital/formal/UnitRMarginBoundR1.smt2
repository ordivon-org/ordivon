; Ordivon Capital: static margin leverage algebra (not executable broker proof).
; Opening unit equity is 1r, gross risky exposure=w*r, debt=(w-1)*r
; for w>=1. After spot price drops d, equity/r=1-w*d,
; gross/r=w*(1-d), margin headroom/r=1-w*(m+(1-m)*d).
(set-logic QF_NRA)
(declare-const w Real)
(declare-const d Real)
(declare-const m Real)
(define-fun headroom () Real (- (- 1 (* w d)) (* m w (- 1 d))))
(define-fun factored () Real (- 1 (* w (+ m (* (- 1 m) d)))))

; Abstract symbolic algebra equality in the real numbers.
(push 1)
(assert (not (= headroom factored)))
(check-sat)
(pop 1)

; Under m=40%, d=50%, leverage at most 10/7 implies no breach.
(push 1)
(assert (>= w 1))
(assert (<= w (/ 10 7)))
(assert (= m (/ 2 5)))
(assert (= d (/ 1 2)))
(assert (< headroom 0))
(check-sat)
(pop 1)

; Positive breach witness: 2x leverage / 40% maintenance / 25% fall.
(push 1)
(assert (= w 2))
(assert (= m (/ 2 5)))
(assert (= d (/ 1 4)))
(assert (< headroom 0))
(check-sat)
(pop 1)
