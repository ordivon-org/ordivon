# Alpaca Paper Trades — Phase 7P Record

This directory records supervised Alpaca Paper trades executed through Ordivon's
paper-only execution adapter. Each trade is a governed dogfood event, not a
profitability test.

**⚠ PAPER ONLY — NOT LIVE TRADING. NOT REAL MONEY. NOT FINANCIAL ADVICE.**

## Trade Records

| Trade | Date | Symbol | Side | Status | Outcome |
|-------|------|--------|------|--------|---------|
| [7P-3-001](phase-7p-3-first-paper-trade-intake.md) | 2026-04-29 | AAPL | buy | pending | — |

## Lifecycle

Each trade follows the full Ordivon governance loop:

```
Intake → Plan Receipt → Execution Receipt → Outcome → Review
```

All documents in this directory follow this naming convention:
`phase-7p-X-{trade-id}-{stage}.md`

## Non-Goals

- These trades are not live trading evidence.
- Paper PnL is not real profitability.
- Paper success does not authorize live trading.
- Reviews produce CandidateRules only, not Policies.
