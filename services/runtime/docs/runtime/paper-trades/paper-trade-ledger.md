# Alpaca Paper Trade Ledger

Status: **ACTIVE** | Date: 2026-04-29 | Last updated: 2026-04-29

**⚠ PAPER ONLY — NOT LIVE TRADING. ALL PNL IS SIMULATED.**

| ID | Symbol | Entry | Exit | Paper PnL | Review | Boundary |
|----|--------|-------|------|-----------|--------|----------|
| [PT-001](phase-7p-z-formal-review.md) | AAPL | $267.55 | $269.07 | +$1.52 | ✅ | — |
| [PT-002](PT-002.md) | MSFT | $423.88 | $424.14 | +$0.26 | ✅ | — |
| [PT-003](PT-003.md) | GOOGL | $352.50 | $352.26 | **-$0.24** | ✅ | Preflight REJECT |

## Blocked Attempts

| ID | Phase | Scenario | Decision | Order |
|----|-------|----------|----------|-------|
| H1-001 | 7P-H1 | Stale observation (freshness=missing) | **HOLD** | None |

## Summary

| Metric | Value |
|--------|-------|
| Total paper trades | 3 |
| Completed round trips | 3 |
| Positive PnL trades | 2 |
| Negative PnL trades | 1 |
| Cumulative paper PnL | +$1.54 (simulated) |
| Reviews complete | 3 |
| Boundary violations | 0 |
| Boundary preflights | 1 (PT-003: missing reason → REJECT → corrected) |
| CandidateRules | 2 (advisory only) |
| Next trade allowed? | After review + protocol + human GO |
