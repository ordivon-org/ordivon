; Local proof obligations for exact canonical-gap evidence.
; These scalar checks compose by sum/induction; they are not a proof
; of SciPy, floating-point feasibility, or the Python implementation.
(set-logic QF_NRA)
(declare-const c Real)
(declare-const d Real)
(declare-const C Real)
(declare-const D Real)
(declare-const lend Real)
(declare-const borrow Real)

; With no simultaneous cash/debt and no less net balance,
; canonical financing weakly dominates the original on every edge.
(push)
(assert (and (>= c 0) (>= d 0) (>= C 0) (>= D 0)
             (= (* C D) 0) (>= (- C D) (- c d))
             (> lend 0) (>= borrow lend)))
(assert (< (- (* C lend) (* D borrow)) (- (* c lend) (* d borrow))))
(check-sat)
(pop)

; Caps: nonnegative equity with initial margin and bounded funding.
(declare-const a Real)
(declare-const m Real)
(declare-const equity Real)
(declare-const funded Real)
(push)
(assert (and (>= a 0) (> m 0) (<= (* m a) equity) (<= equity funded)))
(assert (> (* m a) funded))
(check-sat)
(pop)

; A canonical cash/debt pair cannot exceed these local caps.
(declare-const risky Real)
(push)
(assert (and (>= C 0) (>= D 0) (= (* C D) 0)
             (>= risky 0) (= equity (- (+ risky C) D))
             (>= equity 0) (<= equity funded)))
(assert (or (> C funded) (> D risky)))
(check-sat)
(pop)

; Actual turnover is bounded by sum of previous/current position caps.
(declare-const old Real)
(declare-const acap Real)
(declare-const ocap Real)
(push)
(assert (and (<= 0 a) (<= a acap) (<= 0 old) (<= old ocap)))
(assert (> (ite (>= a old) (- a old) (- old a)) (+ acap ocap)))
(check-sat)
(pop)

; Per-coordinate residual correction works for arbitrary signed residual.
(declare-const r Real)
(declare-const x Real)
(declare-const cap Real)
(push)
(assert (and (<= 0 x) (<= x cap)))
(assert (> (* r x) (* (ite (>= r 0) r 0) cap)))
(check-sat)
(pop)

; One-row/one-coordinate weak duality with residual correction.
; The vector form follows by summing the scalar inequalities.
(declare-const g Real)
(declare-const A Real)
(declare-const E Real)
(declare-const b Real)
(declare-const rhs Real)
(declare-const y Real)
(declare-const lam Real)
(push)
(assert (and (<= 0 x) (<= x cap) (>= y 0)
             (<= (* A x) b) (= (* E x) rhs)
             (= g (+ (* A y) (* E lam) r))))
(assert (> (* g x) (+ (* y b) (* lam rhs) (* (ite (>= r 0) r 0) cap))))
(check-sat)
(pop)

; Counterexample: ignoring positive residual is not a valid upper bound.
(push)
(assert (= x 1))
(assert (= cap 1))
(assert (= r 1))
(assert (> (* r x) 0))
(check-sat)
(pop)

; Counterexample: borrow below lend breaks canonical financing dominance.
(push)
(assert (and (= c 1) (= d 1) (= C 0) (= D 0) (= lend 2) (= borrow 1)))
(assert (< (- (* C lend) (* D borrow)) (- (* c lend) (* d borrow))))
(check-sat)
(pop)

; Interval tangent correction, independently of the source of the interval.
(declare-const lo Real)
(declare-const hi Real)
(declare-const z Real)
(push)
(assert (and (<= lo g) (<= g hi) (<= 0 x) (<= x cap) (<= 0 z) (<= z cap)))
(assert (> (* g (- z x)) (+ (* lo (- z x)) (* (- hi lo) (- cap x)))))
(check-sat)
(pop)
; Positive square root ordering (compose for powers of two).
(push)
(assert (and (<= 0 lo) (<= 0 g) (<= 0 hi)
             (<= (* lo lo) (* g g)) (<= (* g g) (* hi hi))))
(assert (or (< g lo) (> g hi)))
(check-sat)
(pop)
; Omitting interval uncertainty can understate the true tangent.
(push)
(assert (and (= lo 0) (= hi 1) (= g 1) (= x 0) (= z 1) (= cap 1)))
(assert (> (* g (- z x)) (* lo (- z x))))
(check-sat)
(pop)
