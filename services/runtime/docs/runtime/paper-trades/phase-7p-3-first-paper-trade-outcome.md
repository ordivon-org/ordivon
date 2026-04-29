# Phase 7P-3 — First Paper Trade Outcome (Reconciled 7P-3F — FILLED)

Status: **FILLED — AWAITING REVIEW** (Phase 7P-3F)
Date: 2026-04-29
Trade ID: 7P-3-001

## Outcome

| Field | Value |
|-------|-------|
| Order ID | `84dcf528...` |
| Symbol | AAPL |
| Side | buy |
| Type | market |
| Quantity | 1 share |
| **Status** | **filled** |
| **Filled at** | 2026-04-29T13:30:50Z (market open, +6 min from submit) |
| **Fill price** | **$267.55** |
| Submitted at | 2026-04-29T13:24:31Z |
| Environment | paper |
| Live Order | False |

## Paper PnL

| Metric | Value |
|--------|-------|
| Entry price | $267.55 |
| Position | 1 AAPL (long) |
| Current price | Unknown (need market data snapshot) |
| Unrealized PnL | TBD (no exit yet) |
| Realized PnL | N/A (position open) |

## Fees / Slippage

| Metric | Value |
|--------|-------|
| Commission | $0.00 (Alpaca commission-free) |
| Expected entry | ~$255.77 (after-hours bid from intake) |
| Actual fill | $267.55 |
| Slippage | +$11.78 (4.6%) — market opened higher |

**Note**: The $11.78 slippage is not a loss. It's the market gap between after-hours bid and opening price. This is a paper account — slippage characteristics differ from live trading.

## Plan Followed?

✅ Yes — intake, readiness gate, plan receipt, execution all per plan.
The after-hours intake vs market-open fill gap is expected behavior for a
pipeline test submitted outside market hours.

## Deviation?

None. Pipeline executed as designed.

## ⚠ PAPER ONLY — NOT REAL PNL

This is simulated paper trading. No real capital was used. The $267.55 fill price
is from Alpaca's paper matching engine and may not reflect actual market liquidity.
