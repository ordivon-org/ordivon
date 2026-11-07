; IEEE-754 binary64 model of Media's selected loudness acceptance comparison.
; This is a SPECIFICATION MODEL, not a Python implementation-refinement proof.
; Query 1: the old comparison-only decision admits a NaN target (SAT).
; Query 2: the strengthened finite-parameter admission cannot admit a
;          nonfinite selected limit (UNSAT).
; Query 3: the strengthened predicate still admits ordinary valid inputs (SAT).
(set-logic QF_FP)
(define-sort F64 () (_ FloatingPoint 11 53))
(define-fun finite ((x F64)) Bool
  (and (not (fp.isNaN x)) (not (fp.isInfinite x))))
(declare-const target F64)
(declare-const tolerance F64)
(declare-const peakLimit F64)
(define-fun measuredLufs () F64 ((_ to_fp 11 53) RNE -23.0))
(define-fun measuredPeak () F64 ((_ to_fp 11 53) RNE -2.0))
(define-fun zero () F64 ((_ to_fp 11 53) RNE 0.0))
(define-fun oldAccept () Bool
  (and
    (not (fp.lt tolerance zero))
    (not (fp.gt (fp.abs (fp.sub RNE measuredLufs target)) tolerance))
    (not (fp.gt measuredPeak peakLimit))))
(define-fun finiteAdmission () Bool
  (and (finite target) (finite tolerance) (finite peakLimit)))
(define-fun newAccept () Bool (and finiteAdmission oldAccept))

(push 1)
(assert (fp.isNaN target))
(assert (fp.eq tolerance ((_ to_fp 11 53) RNE 1.0)))
(assert (fp.eq peakLimit ((_ to_fp 11 53) RNE -1.0)))
(assert oldAccept)
(check-sat)
(pop 1)

(push 1)
(assert newAccept)
(assert (not finiteAdmission))
(check-sat)
(pop 1)

(push 1)
(assert (fp.eq target ((_ to_fp 11 53) RNE -23.0)))
(assert (fp.eq tolerance ((_ to_fp 11 53) RNE 1.0)))
(assert (fp.eq peakLimit ((_ to_fp 11 53) RNE -1.0)))
(assert newAccept)
(check-sat)
(pop 1)
