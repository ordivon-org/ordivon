# Market Capital Clean-Room — Wave B / M2 Acceptance

Date: 2026-09-13

## Standing

**PASS_BOUNDED_FEASIBILITY** — target intention is now lowered through LEAN's own buying-power/order-sizing machinery before the historical validation orders are emitted.

## Why M2 exists

Wave B / M1 proved that a portfolio target is not an executable guarantee. The Wave A target sums to gross exposure 1.0 with cash target 0.0, but later fill prices plus fees and modeled slippage caused the margin backtest to finish with negative cash.

M2 does not invent a parallel Ordivon sizing engine. It delegates sizing to QuantConnect LEAN:

`target weight -> Settings.FreePortfolioValuePercentage -> CalculateOrderQuantity -> MarketOrder -> LEAN buying-power/fill/fee/slippage models`.

## Validation policy

The validation execution reserve is 1% of portfolio value. This is an **execution reserve for this bounded validation**, not an investment allocation, alpha claim, or production risk rule. It exceeds the approximately 0.54% negative-cash shortfall observed in M1's deterministic fixture and demonstrates the contract without claiming that 1% is universally sufficient.

## Evidence

With the same Wave A target portfolio and same deterministic price fixture:

- M1 quantities: AAPL 332, MSFT 664, NVDA 1329; final cash about USD -539.03.
- M2 LEAN-sized quantities: AAPL 329, MSFT 659, NVDA 1319.
- M2 fills retain `InteractiveBrokersFeeModel`, `VolumeShareSlippageModel(0.30, 0.05)`, and `EquityFillModel`.
- M2 total fees: USD 11.54.
- M2 final portfolio value: USD 104036.84.
- M2 final cash: USD 268.84.
- M2 margin used: USD 51884.00.
- data requests: 5 succeeded / 0 failed.
- engine errors: 0.

## Boundary

This proves mechanical pre-trade feasibility on deterministic historical fixture data only. Production symbol bars, real liquidity, broker-specific buying power, account state, taxes, borrow, corporate actions and real execution uncertainty remain future admissions.

No broker credentials are used and no external financial write is authorized or attempted.
