# Portfolio Risk Monitoring R1

Date: 2026-09-19
Status: EXPERIMENTAL / READ-ONLY

## Scope

This path provides portfolio exposure monitoring, historical dependence analysis, and explicit risk-limit evaluation. It is not an allocator, optimizer, hedge selector, or execution path.

## Exposure monitoring

The exposure ledger consumes already-observed private account state and never fetches credentials or persists private reality.

It reports gross and net notional, exposure-to-equity ratios, single-position concentration, available-equity buffer, optional IMR/MMR burden, and explicitly supplied factor-load arithmetic.

These are arithmetic calculations, not quantitative models.

## Historical dependence model

Completed return observations are aligned by timestamp. The dependence analysis uses NumPy/SciPy and reports full-window linear-regression beta/correlation, short and medium trailing estimates, downside estimates, rolling ranges/medians, structural sign-change warnings, and effective overlap sample count.

This component is registered as a quantitative model in the Market Capital model inventory and has status VALIDATION_REQUIRED.

It is permitted for descriptive research and scenario construction. It is not admitted for automatic hedge sizing, return forecasting, causal factor attribution, or live order approval.

Numeric stability classifications require an explicit policy. Without one, raw diagnostics remain unclassified rather than embedding hidden market thresholds.

## Risk-limit evaluation

Risk limits must be explicit. Missing limits produce INCOMPLETE. Historical leverage or the legacy Wave A IPS is not used to infer investor risk tolerance.

The named shock check is first-order arithmetic, not VaR, expected shortfall, liquidation probability, or a forecast.

## OKX public factor adapter

scripts/run-okx-factor-observatory-r1 binds the dependence model to Network v2 and the OKX public REST authority. It fetches completed daily candles, aligns returns by timestamp, and preserves each proxy's effective overlap count.

A requested candle limit is not claimed as a common effective sample size.

## Governance

Model and non-model classifications are maintained in config/quantitative_component_inventory.json and validated by JSON Schema 2020-12. Federal Reserve SR 26-2 is used proportionately as a model-governance reference.

Hard boundaries remain: no allocation, no recommended hedge size, no inferred risk tolerance, no trade recommendation, and no external financial write.
