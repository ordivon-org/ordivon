# Alpaca Paper Trade Ledger

Status: **ACTIVE** (Phase 7P-L)
Date: 2026-04-29
Last updated: 2026-04-29

**⚠ PAPER ONLY — NOT LIVE TRADING. ALL PNL IS SIMULATED.**

## Active Trades

| ID | Phase | Symbol | Entry | Exit | Paper PnL | Status | Review | Next? |
|----|-------|--------|-------|------|-----------|--------|--------|-------|
| [PT-001](#pt-001) | 7P-3 | AAPL | $267.55 | $269.07 | +$1.52 | closed | ✅ | after review |
| [PT-002](#pt-002) | 7P-4 | MSFT | $423.88 | $424.14 | +$0.26 | closed | ✅ | after review |

## PT-001 — First Paper Trade

AAPL buy 1 @ $267.55, sell 1 @ $269.07, +$1.52 simulated. After-hours entry (13:24), market-open fill (13:30). 22 min hold. [Full review](phase-7p-z-formal-review.md). CR-7P-001, CR-7P-002.

## PT-002 — Second Paper Trade

MSFT buy 1 @ $423.88, sell 1 @ $424.14, +$0.26 simulated. Market-hours entry (14:13), immediate fill (< 1s). 37 sec hold. [Full review](PT-002.md). CR-7P-001 validated (no after-hours gap). CR-7P-002 followed.

## Summary

| Metric | Value |
|--------|-------|
| Total paper trades | 2 |
| Completed round trips | 2 |
| Open positions | 0 |
| Reviews complete | 2 |
| Boundary violations | 0 |
| CandidateRules | 2 (advisory only) |
| Next trade allowed? | After review confirmed + human GO |
