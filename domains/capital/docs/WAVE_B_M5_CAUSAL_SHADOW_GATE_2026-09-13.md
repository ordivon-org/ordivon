# Market Capital Clean-Room — Wave B / M5 Causal Shadow Gate

Date: 2026-09-13

## Gate standing

**PASS_BOUNDED_GATE_IMPLEMENTED**.

Current observed standing: **WAITING_FOR_POST_DECISION_DATA**.

The distinction is intentional: the causal gate itself is implemented and destructively tested, but no causal market evidence exists yet for the current decision artifact.

## Decision boundary

The conservative decision boundary is the canonical Wave A close commit:

- commit: `4d2a779664f4216207e9b41c87bad01463b3a68f`;
- commit time: `2026-09-12T14:59:29Z`;
- target portfolio SHA-256: `137265667683455c302adff94466eaf38444ed7d51b5959c4ad065505792c14d`.

The target portfolio is treated as fixed at that boundary. Earlier market data may validate mechanics, but it can never be promoted to causal shadow evidence for this decision.

## Causality rule

Nasdaq's public historical endpoint provides daily session dates rather than an execution-grade event timestamp. M5 therefore uses a conservative daily-bar rule:

`session_date > decision_date_in_America/New_York`.

A causal cut is admitted only if **all required series** contain the same eligible post-decision session date:

- AAPL;
- MSFT;
- NVDA;
- SPY benchmark.

Union-of-dates, partial-symbol availability, same-day/pre-decision data and caller-authored PASS labels are rejected.

## Current observation

At the 2026-09-13 observation, the provider returned HTTP 200 for all four required series but zero rows for the 2026-09-12 through 2026-09-13 query window. Therefore:

- `causalEvidenceAvailable = false`;
- `eligibleCommonSessionDates = []`;
- `standing = WAITING_FOR_POST_DECISION_DATA`.

No LEAN execution is launched by the M5 probe while the gate is waiting.

## Transition condition

The gate can transition to `POST_DECISION_DATA_ADMITTED` only when at least one complete common session date exists strictly after the decision session date. That admission is a prerequisite for a causal shadow execution lane; it does not itself authorize paper brokerage, live brokerage or external financial writes.

## Safety / authority boundary

- FIX 4.4 semantic admission remains required;
- M2 execution-feasibility admission remains required;
- broker credentials: forbidden;
- broker/venue session: not opened by this gate;
- external financial writes: none;
- production/live authorization: none.

## Tests

The M5 unit cases prove:

1. same-day and prior bars remain WAITING;
2. one missing required series remains WAITING;
3. a complete post-decision common cut is admitted;
4. common-cut intersection is used instead of date union.
