# Phase 7P-Z — Round-Trip Outcome

Status: **COMPLETED** (Phase 7P-Z)
Date: 2026-04-29

## Round-Trip Summary

| Metric | Entry | Exit |
|--------|-------|------|
| Order ID | `84dcf528...` | `44d87140...` |
| Symbol | AAPL | AAPL |
| Side | buy | sell |
| Quantity | 1 | 1 |
| Price | $267.55 | $269.07 |
| Time | 13:30 UTC | 13:52 UTC |
| Holding period | — | ~22 minutes |

## Realized Paper PnL

| Metric | Value |
|--------|-------|
| Gross PnL | +$1.52 |
| Commission | $0.00 |
| Net PnL | **+$1.52 (simulated paper profit)** |

## Slippage

| Metric | Value |
|--------|-------|
| After-hours bid reference | $255.77 |
| Entry fill | $267.55 |
| Entry gap | +$11.78 (market opened higher) |
| Mark at close | ~$268.38 |
| Exit fill | $269.07 |
| Exit vs mark | +$0.69 (standard market order spread) |

## Plan Followed?

✅ Yes. Closeout plan: sell 1 AAPL. Executed as planned.

## Deviation?

None.

## What Worked

1. Full round-trip pipeline: intake → entry receipt → entry fill → position tracking → closeout receipt → exit fill → outcome → review
2. AlpacaPaperExecutionAdapter correctly handled both buy and sell orders
3. All paper-only guards held (no live API, no live keys)
4. PaperExecutionAdapter remained separate from ReadOnlyAdapterCapability
5. Position was correctly tracked and closed

## What Could Be Improved

1. After-hours intake should flag market-hours expectations
2. Holding period was only 22 minutes — too short for meaningful review, but sufficient for pipeline validation
3. Paper fill prices ($267.55 / $269.07) vs after-hours bid ($255.77) show large market-open gaps

## ⚠ PAPER PNL IS SIMULATED — NOT REAL

This +$1.52 is Alpaca Paper simulated profit. It does NOT represent real trading capability, real market conditions, or a profitable strategy. It is a governance pipeline test artifact.
