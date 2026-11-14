; Markets XNYS daily-session request completeness and Qlib research label horizon.
; Model-only integer *exchange session ordinals*, conditional on a correct
; external XNYS calendar. This does not verify Python, publisher PIT,
; exchange calendar historic revisions, equities OHLC or execution authority.
(set-logic QF_LIA)
(declare-const requested-first Int)
(declare-const requested-last Int)
(declare-const observed-first Int)
(declare-const observed-last Int)
(declare-const internal-missing Int)
(declare-const invented-extra Int)
(declare-const duplicated Int)
(declare-const observed-unordered Int)
(define-fun exact-request-grid () Bool
  (and (= observed-first requested-first)
       (= observed-last requested-last)
       (= internal-missing 0)
       (= invented-extra 0)
       (= duplicated 0)
       (= observed-unordered 0)
       (<= requested-first requested-last)))

; 1: source truncation at the LAST exchange session cannot qualify.
(push 1)
(assert exact-request-grid)
(assert (< observed-last requested-last))
(check-sat)
(pop 1)

; 2: source truncation at the FIRST exchange session cannot qualify.
(push 1)
(assert exact-request-grid)
(assert (> observed-first requested-first))
(check-sat)
(pop 1)

; 3: source with an interior missing true exchange session cannot qualify.
(push 1)
(assert exact-request-grid)
(assert (> internal-missing 0))
(check-sat)
(pop 1)

; 4: source with a fabricated exchange holiday cannot qualify.
(push 1)
(assert exact-request-grid)
(assert (> invented-extra 0))
(check-sat)
(pop 1)

; 5: counterexample to the OLD method that inferred its endpoint from
; returned data. Observed endpoints look internally continuous but omit
; the requested final session. This is SAT, not a proved market fact.
(push 1)
(assert (= requested-first 0))
(assert (= requested-last 4))
(assert (= observed-first 0))
(assert (= observed-last 3))
(assert (= internal-missing 0))
(assert (= invented-extra 0))
(assert (not exact-request-grid))
(check-sat)
(pop 1)

(declare-const train-end Int)
(declare-const valid-start Int)
(declare-const valid-end Int)
(declare-const test-start Int)
(declare-const holding-horizon Int)
(declare-const exit-next-open Int)
(define-fun last-readable-train () Int
  (+ train-end holding-horizon exit-next-open))
(define-fun last-readable-valid () Int
  (+ valid-end holding-horizon exit-next-open))
(define-fun approved-holding-window () Bool
  (and (>= holding-horizon 1)
       (<= holding-horizon 20)
       (>= exit-next-open 0)
       (<= exit-next-open 1)
       (< last-readable-train valid-start)
       (< last-readable-valid test-start)))

; 6: Approved train -> validation transition cannot leak future labels.
(push 1)
(assert approved-holding-window)
(assert (>= last-readable-train valid-start))
(check-sat)
(pop 1)

; 7: Approved validation -> test transition cannot leak future labels.
(push 1)
(assert approved-holding-window)
(assert (>= last-readable-valid test-start))
(check-sat)
(pop 1)

; 8: The WRONG old H-only rule permits T+H+1 next-open label leakage.
; Train decision 10, H=5, next_open=1, valid start=16:
; H-only test says 10+5 < 16, but actual label end = 16.
(push 1)
(assert (= holding-horizon 5))
(assert (= exit-next-open 1))
(assert (= train-end 10))
(assert (= valid-start 16))
(assert (< (+ train-end holding-horizon) valid-start))
(assert (>= last-readable-train valid-start))
(check-sat)
(pop 1)
