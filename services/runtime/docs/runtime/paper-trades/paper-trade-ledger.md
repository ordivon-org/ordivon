# Alpaca Paper Trade Ledger

Status: **ACTIVE** (Phase 7P-L)
Date: 2026-04-29
Last updated: 2026-04-29

**⚠ PAPER ONLY — NOT LIVE TRADING. ALL PNL IS SIMULATED.**

## Active Trades

| ID | Phase | Symbol | Entry | Exit | Paper PnL | Status | Review | Next? |
|----|-------|--------|-------|------|-----------|--------|--------|-------|
| [PT-001](#pt-001) | 7P-3 | AAPL | $267.55 | $269.07 | +$1.52 | closed | [✅](phase-7p-z-formal-review.md) | after review |

## PT-001 — First Paper Trade (7P-3, completed 7P-Z)

| Field | Value |
|-------|-------|
| trade_id | PT-001 |
| phase | 7P-3 (entry) → 7P-Z (closeout + review) |
| symbol | AAPL |
| entry_side | buy |
| entry_price | $267.55 |
| entry_order_id | `84dcf528...` |
| entry_filled_at | 2026-04-29T13:30:50Z |
| exit_side | sell (close) |
| exit_price | $269.07 |
| exit_order_id | `44d87140...` |
| exit_filled_at | 2026-04-29T13:52:13Z |
| holding_period | ~22 minutes |
| paper_pnl | +$1.52 (simulated) |
| paper_only | true |
| live_order | false |
| intake_complete | ✅ phase-7p-3-first-paper-trade-intake.md |
| plan_receipt_complete | ✅ entry + closeout |
| execution_receipt_complete | ✅ entry + closeout |
| fill_reconciliation_complete | ✅ |
| outcome_complete | ✅ |
| review_complete | ✅ phase-7p-z-formal-review.md |
| boundary_violations | 0 |
| next_action_allowed | only after review confirmed + human GO |
| candidate_rules | [CR-7P-001](../alpaca-paper-candidate-rule-handling.md#cr-7p-001-market-hours-awareness-gate), [CR-7P-002](../alpaca-paper-candidate-rule-handling.md#cr-7p-002-pre-trade-review-completion-gate) |

## Summary

| Metric | Value |
|--------|-------|
| Total paper trades | 1 |
| Completed round trips | 1 |
| Open positions | 0 |
| Reviews complete | 1 |
| Boundary violations | 0 |
| CandidateRules | 2 (advisory only) |
| Next trade allowed? | After review confirmed + human GO |
