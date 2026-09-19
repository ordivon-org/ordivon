# Portfolio Risk Observatory R1

Date: 2026-09-19
Status: EXPERIMENTAL / READ-ONLY P1-P4 IMPLEMENTATION

## Scope

R1 implements the first four nodes of the Portfolio Risk LEGO contract:

1. **P1 Exposure Ledger**
2. **P2 Factor Observatory**
3. **P3 Regime-Conditioned Dependence**
4. **P4 Risk Budget**

It deliberately does not implement an allocator, optimizer, hedge selector, or execution path.

## P1 Exposure Ledger

The ledger consumes already-observed private account state. It never fetches credentials or persists private reality.

Inputs:

- equity USD;
- available equity USD;
- optional IMR/MMR;
- signed position notionals;
- optional explicit factor loadings.

Outputs distinguish:

- gross versus net notional;
- gross/net to equity;
- single-position concentration;
- available-equity buffer;
- IMR/MMR burden;
- overlapping named factor exposures.

Factor exposures are explicitly marked non-additive because loadings can overlap.

## P2/P3 Factor Observatory and dependence

Completed return observations are aligned by timestamp. A proxy analysis emits:

- full-window correlation and minimum-variance regression beta;
- short and medium trailing-window statistics;
- downside statistics conditional on negative base-instrument returns;
- rolling beta/correlation ranges and medians;
- explicit instability reasons.

The observatory does not contain universal numeric definitions of "stable", "high correlation", or "wide beta range". Without an explicit `stabilityPolicy`, it emits raw diagnostics and only categorical structural warnings such as correlation/beta sign changes, with standing `UNCLASSIFIED_NO_STABILITY_POLICY`.

If a caller supplies a complete stability policy, numeric classification becomes a policy comparison rather than a hidden market assumption.

The minimum-variance beta is descriptive only. It is never emitted as a recommended hedge size.

## P4 Risk Budget

Risk budget values must be explicit.

Required R1 inputs:

- `maxGrossToEquity`;
- `maxLargestPositionGrossShare`;
- `minAvailableEquityRatio`;
- `shockMagnitudePct`;
- `maxEquityLossPctAtShock`.

If any are absent, standing is `INCOMPLETE`. The system does not infer tolerance from past leverage, position size, or the old Wave A IPS.

The named-shock check is a simple first-order single-position sensitivity:

`largest_position_equity_multiple × shock_pct`.

It is a stress coordinate, not VaR, expected shortfall, liquidation probability, or a return forecast.

## OKX public factor adapter

`scripts/run-okx-factor-observatory-r1` binds the factor observatory to Network v2's OKX public REST authority. It fetches only completed 1D candles, aligns returns by timestamp, preserves per-proxy overlap counts, and does not use broker credentials or private account data.

A requested candle limit is not a claimed common sample size: each proxy carries its own `overlapReturnCount`.

## Composition

`build_portfolio_risk_observatory()` composes P1-P4 into a single read-only artifact.

Hard guards:

- `allocationProduced = false`
- `hedgeSizeRecommended = false`
- `riskToleranceInferred = false`
- `tradeRecommendationProduced = false`
- `externalFinancialWriteAttempted = false`

## Relationship to legacy portfolio.py

`portfolio.py` remains a bounded Wave A equal-weight validation fixture. It is not promoted into a live portfolio-construction authority.

The observatory is a separate path because risk observation and live allocation have different authority, evidence and validation requirements.

## Next boundary

P5/P6 should consume P1-P4 evidence and produce **counterfactual risk deltas**, not orders:

- de-risk counterfactual;
- factor hedge counterfactual;
- diversification counterfactual;
- hold/reconcile standing;
- resulting gross/margin/funding/liquidity constraints.

No P5/P6 work should begin by choosing a ticker or trade size before P4 risk budget is explicit.
