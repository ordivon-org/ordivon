; Declared single-asset long-liquidation accounting.
; This PROVES a scoped algebraic identity, not the correctness of any
; broker policy, security valuation, execution timing, margin requirement,
; price provenance or Python implementation.
(set-logic QF_NRA)
(declare-const quantity Real)
(declare-const sold Real)
(declare-const mark Real)
(declare-const fill Real)
(declare-const fee Real)
(declare-const cash Real)
(declare-const loan Real)
(declare-const paydown Real)
(declare-const maintenance-after Real)
(assert (>= quantity 0))
(assert (>= sold 0))
(assert (<= sold quantity))
(assert (> mark 0))
(assert (> fill 0))
(assert (>= fee 0))
(assert (>= cash 0))
(assert (>= loan 0))
(assert (>= paydown 0))
(assert (<= paydown loan))
(assert (>= maintenance-after 0))
(assert (>= (- (+ cash (* sold fill)) fee paydown) 0))
(define-fun W-before () Real (- (+ (* quantity mark) cash) loan))
(define-fun W-after () Real
  (- (+ (* (- quantity sold) mark)
        (- (+ cash (* sold fill)) fee paydown))
     (- loan paydown)))
(define-fun delta () Real (- W-after W-before))
(define-fun execution-loss () Real (- (* sold (- fill mark)) fee))

; No quantity of debt repayment is capable of manufacturing net equity.
(push 1)
(assert (not (= delta execution-loss)))
(check-sat)
(pop 1)

; If every share sells at the common mark and fees are zero, equity is unchanged.
(push 1)
(assert (= fill mark))
(assert (= fee 0))
(assert (not (= W-after W-before)))
(check-sat)
(pop 1)

; A full forced liquidation can leave debt, negative equity and a shortfall.
; This is a required SAT witness against "liquidation always cures margin".
(push 1)
(assert (= quantity 2))
(assert (= sold 2))
(assert (= mark 100))
(assert (= fill 80))
(assert (= fee 5))
(assert (= cash 0))
(assert (= loan 500))
(assert (= paydown 155))
(assert (= maintenance-after 0))
(assert (< W-after 0))
(assert (< (- W-after maintenance-after) 0))
(check-sat)
(pop 1)
