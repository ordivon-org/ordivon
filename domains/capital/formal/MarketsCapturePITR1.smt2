; Markets capture-to-Research visibility in integer timestamps (model only).
; This assumes the Markets snapshot has a genuine, independently observed
; capture timestamp; it DOES NOT authenticate that physical-world timestamp,
; vendor source, exchange calendar, price or corporate-action history.
; A model/theory is not an implementation refinement proof.
(set-logic QF_LIA)
(declare-const close-at Int)
(declare-const reported-at Int)
(declare-const captured-at Int)
(declare-const decision-at Int)
(declare-const revision-captured-at Int)
(declare-const basis-before Int)
(declare-const basis-after Int)
(define-fun visible ((decision Int) (captured Int)) Bool
  (>= decision captured))

; 1: a decision before capture can never see an imported historical mark.
(push 1)
(assert (<= close-at reported-at)) (assert (<= reported-at captured-at))
(assert (< decision-at captured-at))
(assert (visible decision-at captured-at))
(check-sat)
(pop 1)

; 2: the incorrect reported-at filter leaks a source-reported earlier timestamp.
(push 1)
(assert (= close-at 0)) (assert (= reported-at 1))
(assert (= decision-at 2)) (assert (= captured-at 3))
(assert (<= reported-at decision-at))
(assert (not (visible decision-at captured-at)))
(check-sat)
(pop 1)

; 3: a later capture cannot rewrite the earlier frozen decision.
(push 1)
(assert (<= captured-at decision-at))
(assert (< decision-at revision-captured-at))
(assert (not (and (visible decision-at captured-at)
                 (not (visible decision-at revision-captured-at)))))
(check-sat)
(pop 1)

; 4: after the newer capture, that revision may become visible.
(push 1)
(assert (< captured-at revision-captured-at))
(assert (<= revision-captured-at decision-at))
(assert (not (visible decision-at revision-captured-at)))
(check-sat)
(pop 1)

; 5: the normalized-return guard forbids a cross-price-basis ratio.
(push 1)
(assert (not (= basis-before basis-after)))
(assert (= basis-before basis-after))
(check-sat)
(pop 1)

; 6: the incorrect unconditional ratio would allow a basis mismatch.
(push 1)
(assert (= basis-before 1)) (assert (= basis-after 2))
(assert (not (= basis-before basis-after)))
(check-sat)
(pop 1)

; RTDSM month-resolution admission. Integers are ordered calendar month
; indices. Availability from the following month is a conservative contract,
; not evidence of exact historical provider publication.
(declare-const vintage-month Int)
(declare-const decision-month Int)
(declare-const later-vintage-month Int)
(define-fun month-visible ((decision Int) (vintage Int)) Bool
  (>= decision (+ vintage 1)))
(push 1)
(assert (>= vintage-month decision-month))
(assert (month-visible decision-month vintage-month))
(check-sat)
(pop 1)
(push 1)
(assert (month-visible decision-month vintage-month))
(assert (>= later-vintage-month decision-month))
(assert (month-visible decision-month later-vintage-month))
(check-sat)
(pop 1)
; Incorrect current-month visibility would leak data during the month.
(push 1)
(assert (= vintage-month decision-month))
(assert (not (month-visible decision-month vintage-month)))
(check-sat)
(pop 1)
