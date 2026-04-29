# Alpaca Paper Trade Ledger

Status: **ACTIVE** | Date: 2026-04-29

**⚠ PAPER ONLY — NOT LIVE TRADING. ALL PNL IS SIMULATED.**

| ID | Symbol | Entry | Exit | Paper PnL | Status | Review |
|----|--------|-------|------|-----------|--------|--------|
| [PT-001](PT-001.md) | AAPL | $267.55 | $269.07 | +$1.52 | closed | ✅ | CR-7P-001, CR-7P-002 |
| [PT-002](PT-002.md) | MSFT | $423.88 | $424.14 | +$0.26 | closed | ✅ |
| [PT-003](PT-003.md) | GOOGL | $352.50 | $352.26 | -$0.24 | closed | ✅ |
| [PT-004](PT-004.md) | NFLX | limit $90 (pending) | — | — | **open** | ⏳ |

## Blocked Attempts

| ID | Phase | Scenario | Decision | Order |
|----|-------|----------|----------|-------|
| B1-003 | 7P-5 | Missing reason_not_to_trade | **REJECT** | None |
| H1-001 | 7P-H1 | Stale observation | **HOLD** | None |
| N1-A | 7P-N1 | Live URL | **NO-GO** | None |
| N1-B | 7P-N1 | AI auto-trading | **NO-GO** | None |

## Summary

| Metric | Value |
|--------|-------|
| Total paper trades | 4 |
| Completed round trips | 3 |
| Open positions | 1 (PT-004 pending) |
| Refusals (HOLD/REJECT/NO-GO) | 4 |
| Violations | 0 |
