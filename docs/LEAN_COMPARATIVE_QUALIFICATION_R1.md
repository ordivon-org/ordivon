# LEAN comparative qualification R1 — 2026-09-21

## Exact contracts

LEAN is not treated as one indivisible owner. The audit separates:

1. bounded US-equity execution feasibility/sizing;
2. broader historical backtest, fill, slippage, calendar, and buying-power mechanics.

## Latest candidate

- QuantConnect LEAN master cut: `985ef30`, authored 2026-09-18.
- Source tarball SHA256: `a70653f5a646c7a0e0ca2925ebcff95d52ff4bb71b2a824fcbe988ac4f317cab`.
- .NET SDK: `10.0.401`.
- .NET runtime: `10.0.12`.
- Launcher build: PASS.
- M1 historical fixture: PASS.
- M2 feasibility: PASS.
- M3 provider-origin non-causal data lane: PASS.
- M4 FIX 4.4 order-semantics lane: PASS.
- M6 plan-only shadow precommit: PASS.

Functional qualification therefore does not justify rejecting LEAN.

## Sizing differential

The first local formula used only free-portfolio reserve plus whole-share truncation. Across 19 scenarios / 57 symbol comparisons it produced one mismatch, at the low-price boundary.

Source inspection identified the missing mechanism: LEAN iteratively incorporates its default US-equity InteractiveBrokersFeeModel commission before final target quantity convergence. The local baseline was corrected to include that exact fee-aware loop.

After correction:

- scenarios: 19;
- symbol comparisons: 57;
- mismatches: 0;
- tested free-portfolio reserve weights: 0, 0.01, 0.05, 0.10;
- explicit low-price fee boundary: 10.00 USD -> 3332 shares, matching LEAN.

The admitted local contract remains intentionally narrow: empty USD portfolio, positive long US equities, one-share lot, explicit free-portfolio reserve, and the frozen default LEAN/IB-style equity-fee mechanics. Unsupported mechanics fail closed.

## Supply-chain gate

The latest LEAN candidate builds successfully but the build reports 112 NU190x vulnerability warning lines. Unique current findings include:

- critical: `System.Drawing.Common 4.7.0` / `GHSA-rxg9-xrhp-64gj`;
- high: `System.Net.Http.WinHttpHandler 4.4.0` / `GHSA-6xh7-4v2w-36q6`;
- high: `System.Private.ServiceModel 4.4.0` / `GHSA-jc8g-xhw5-6x46`;
- high: `System.ServiceModel.Primitives 4.4.0` / `GHSA-jc8g-xhw5-6x46`;
- moderate ServiceModel findings are also present.

This blocks current core admission even though functional qualification passed.

## Decision

- Current bounded sizing/feasibility owner: `src/ordivon_capital/market/execution_feasibility.py`.
- LEAN current standing: isolated historical/general trading-engine challenger.
- Historical tag 18074 remains a frozen control only.
- LEAN is not a prerequisite for canonical R0-R5 closure.
- If a future contract requires broader holdings transitions, leverage, options/futures, non-unit lots, different fee/brokerage models, calendars, fills, slippage, or backtest lifecycle, the local bounded sizer does not expand automatically. Re-open comparative qualification.
