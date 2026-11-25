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

; Sparse gradient resource admission: zero is initially in budget.
; At an arbitrary coordinate, an update either checks its new bit length
; or leaves the old value unchanged. This obligation is about locality,
; not a model of Python integer arithmetic or its execution time.
(declare-const bitsBefore Real)
(declare-const bitsAfter Real)
(declare-const touched Bool)
(push)
(assert (and (<= 0 bitsBefore) (<= bitsBefore 16384)
             (=> touched (<= bitsAfter 16384))
             (=> (not touched) (= bitsAfter bitsBefore))))
(assert (> bitsAfter 16384))
(check-sat)
(pop)
; Counterexample: an updated coordinate without its local gate can exceed budget.
(push)
(assert (and touched (= bitsBefore 1) (= bitsAfter 16385)))
(check-sat)
(pop)

; Structured cap V2: shared weighted margin budget, nonnegative debt,
; and borrow >= lend. Scalar terms compose by summation over assets.
(declare-const R1 Real)
(declare-const R2 Real)
(declare-const M1 Real)
(declare-const M2 Real)
(declare-const G1 Real)
(declare-const G2 Real)
(declare-const K Real)
(push)
(assert (and (>= R1 0) (>= R2 0) (> M1 0) (<= M1 1)
             (> M2 0) (<= M2 1) (>= G1 0) (>= G2 0)
             (> lend 0) (>= borrow lend) (>= K 0)
             (>= c 0) (>= d 0)
             (= equity (+ R1 R2 c (- d)))
             (>= equity (+ (* M1 R1) (* M2 R2)))
             (>= funded equity)
             (>= (* K M1) (- G1 lend))
             (>= (* K M2) (- G2 lend))))
(assert (> (+ (* G1 R1) (* G2 R2) (* lend c) (- (* borrow d)))
           (* (+ lend K) funded)))
(check-sat)
(pop)

; Canonical debt cap: K >= 1/m_i-1 for each margin; shared margin sum.
(push)
(assert (and (>= R1 0) (>= R2 0) (> M1 0) (<= M1 1)
             (> M2 0) (<= M2 1) (>= K 0)
             (>= C 0) (>= D 0) (= (* C D) 0)
             (= equity (+ R1 R2 C (- D)))
             (>= equity (+ (* M1 R1) (* M2 R2)))
             (>= funded equity)
             (>= (* (+ K 1) M1) 1)
             (>= (* (+ K 1) M2) 1)))
(assert (> D (* K funded)))
(check-sat)
(pop)

; A due payment and nonnegative fees reduce the next decision cap.
(declare-const incomingEquity Real)
(declare-const due Real)
(declare-const fees Real)
(push)
(assert (and (>= funded incomingEquity) (>= due 0) (>= fees 0)
             (= equity (+ 1 incomingEquity (- due) (- fees)))))
(assert (> equity (+ 1 funded (- due))))
(check-sat)
(pop)

; Negative control: insufficient debt cap fails even with legal margin.
(push)
(assert (and (= R1 2) (= R2 0) (= M1 (/ 1 2))
             (= C 0) (= D 1) (= equity 1) (= funded 1)
             (= equity (+ R1 R2 C (- D))) (>= equity (* M1 R1))))
(assert (> D (* 0 funded)))
(check-sat)
(pop)

; Negative control: dropping the borrow >= lend premise is unsound.
(push)
(assert (and (= R1 0) (= R2 0) (= c 1) (= d 1)
             (= equity 0) (= funded 0) (= lend 1) (= borrow 0)
             (= K 0)))
(assert (> (+ (* lend c) (- (* borrow d))) (* (+ lend K) funded)))
(check-sat)
(pop)

; An exact positive scaling of the proposal objective preserves order.
; This is not a claim of binary64 equality or solver convergence.
(declare-const objectiveA Real)
(declare-const objectiveB Real)
(declare-const scale Real)
(push)
(assert (and (> scale 0) (<= objectiveA objectiveB)))
(assert (> (* scale objectiveA) (* scale objectiveB)))
(check-sat)
(pop)

; Selecting a smaller separately certified bound cannot weaken validity.
(declare-const exactGap Real)
(declare-const baselineUpper Real)
(declare-const proposalUpper Real)
(declare-const selectedUpper Real)
(push)
(assert (and (>= exactGap 0) (>= baselineUpper exactGap)
             (>= proposalUpper exactGap)
             (= selectedUpper (ite (< proposalUpper baselineUpper)
                                   proposalUpper baselineUpper))))
(assert (or (< selectedUpper exactGap) (> selectedUpper baselineUpper)))
(check-sat)
(pop)

; A numerically smaller unverified value can understate the exact gap.
(push)
(assert (and (>= exactGap 0) (>= baselineUpper exactGap)
             (>= proposalUpper 0) (< proposalUpper baselineUpper)
             (= selectedUpper proposalUpper)))
(assert (< selectedUpper exactGap))
(check-sat)
(pop)
