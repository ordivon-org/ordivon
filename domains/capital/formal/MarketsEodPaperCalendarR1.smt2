; Finance Markets ETF daily close -> Accounting durable PG acceptance
; Abstract source-calendar implication ONLY. Actual XNYS date/open/close facts
; must come from independent exchange_calendars native consumer tests.
; This does NOT prove dataclass construction, Python/Pandas implementation,
; source publication PIT, corporate actions, issuer authorization, or PG atomicity.
(set-logic QF_LIA)
(declare-const exchange-session-open Bool)
(declare-const observed-close-utc-second Int)
(declare-const exchange-close-utc-second Int)
(declare-const snapshot-admitted Bool)
(declare-const pg-paper-close-committed Bool)
(declare-const operator-asserted-close Bool)

(define-fun calendar-qualifies () Bool
  (and exchange-session-open
       (= observed-close-utc-second exchange-close-utc-second)))

; Exact Markets validator contract: qualification follows the venue calendar,
; not the requested SHA, operator market_source string or a Python dataclass.
; 1: A closed day cannot be an admissible snapshot.
(push 1)
(assert (= snapshot-admitted calendar-qualifies))
(assert snapshot-admitted)
(assert (not exchange-session-open))
(check-sat)
(pop 1)

; 2: A valid open-session mark cannot use an incorrect UTC close (early-close
; and DST are separate native exchange_calendars positive/negative examples).
(push 1)
(assert (= snapshot-admitted calendar-qualifies))
(assert snapshot-admitted)
(assert (distinct observed-close-utc-second exchange-close-utc-second))
(check-sat)
(pop 1)

; 3: Abstract Accounting consumer obligation: no durable PG close may
; consume a typed EOD market snapshot that fails actual date qualification.
(push 1)
(assert (= snapshot-admitted calendar-qualifies))
(assert (=> pg-paper-close-committed snapshot-admitted))
(assert pg-paper-close-committed)
(assert (not calendar-qualifies))
(check-sat)
(pop 1)

; 4: Old bad boundary: a client can claim a valid market close on a
; closed day with a wrong clock. These assertions are satisfiable.
(push 1)
(assert operator-asserted-close)
(assert (not exchange-session-open))
(assert (= observed-close-utc-second 75600))
(assert (= exchange-close-utc-second 64800))
(check-sat)
(pop 1)

; 5: True early close (in UTC seconds since midnight) remains accepted.
; Only the abstract equality is proved: the actual 18:00 UTC date identity
; comes from the independent native XNYS calendar consumer.
(push 1)
(assert exchange-session-open)
(assert (= observed-close-utc-second 64800))
(assert (= exchange-close-utc-second 64800))
(assert (= snapshot-admitted calendar-qualifies))
(assert snapshot-admitted)
(check-sat)
(pop 1)
