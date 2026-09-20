# Market Capital Standards Adoption R5

Date: 2026-09-19
Status: SUPERSEDED BY STANDARDS_ADOPTION_R6

## Objective

Complete the first standards-first quantitative-model lifecycle without creating a new local model or lens layer.

The active dependence model now has separate development testing, outcomes monitoring, drift measurement, risk-data quality measurement, and tail-risk reporting seams.

## SR 26-2 lifecycle mapping

The single active model remains portfolio-dependence-analysis.

- Development testing uses ordered walk-forward TimeSeriesSplit with OLS primary and Huber challenger.
- Outcomes analysis freezes a reference sample and evaluates strictly later realized observations.
- Ongoing monitoring measures parameter drift, residual-risk drift, and return-distribution drift.
- Model inventory keeps purpose, assumptions, limitations, validation standing, monitoring requirements and prohibited uses centralized.

The model remains VALIDATION_REQUIRED. Developer-run testing and monitoring are not represented as independent validation.

## BCBS 239 proportional risk-data controls

Dependence monitoring records paired-sample base/proxy counts, overlap and union counts, overlap ratios, first/last overlapping timestamps, interval regularity, and optional latest-observation age.

These are data-quality measurements, not traffic-light classifications.

## Mature monitoring methods

The implementation delegates mechanics to mature libraries:

- sklearn.metrics.mean_absolute_error
- scipy.stats.wasserstein_distance
- scipy.stats.ks_2samp
- sklearn.linear_model.LinearRegression
- sklearn.linear_model.HuberRegressor

No locally invented drift score or severity threshold is introduced.

## Public SNDK monitoring canary

A read-only OKX public-data canary used a 30-return strictly later holdout.

| Proxy | Overlap | Overlap/union | Realized variance reduction | Beta delta | Correlation delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| MU-USDT-SWAP | 178 | 1.000000 | 0.693459 | +0.120935 | -0.007439 |
| SMH-USDT-SWAP | 92 | 0.516854 | 0.053946 | -1.058329 | -0.300484 |
| QQQ-USDT-SWAP | 178 | 1.000000 | -0.104148 | -2.183189 | -0.446142 |

The canary demonstrates that historical full-sample dependence is not sufficient evidence of stable future hedge effectiveness. QQQ produced negative realized variance reduction in the current holdout.

Canonical evidence: evidence/acceptance/dependence-model-monitoring-r1.json.

## Tail-risk reporting

The empirical historical expected-shortfall primitive is composable into the portfolio risk report through a registered tail-risk-report adapter.

For the same SNDK completed-1D public sample:

- confidence: 0.975
- observations: 178
- empirical loss VaR fraction: 0.13205251
- empirical ES loss fraction: 0.13934722
- tail observations: 5
- liquidity-horizon scaling: not applied
- regulatory-capital calculation: false

This is descriptive tail-risk evidence only.

## Architecture after R5

The quantitative path is:

authoritative data -> risk-data quality -> model -> development test -> outcomes/drift monitoring -> risk report

Model measurement remains separate from hedge sizing, allocation, trade recommendation, OPA execution policy, and external financial writes.

## Next substitution targets

1. Structurally independent effective challenge for the dependence model.
2. Persist monitoring history as a standard time series rather than ad-hoc evidence snapshots.
3. Bind model run identity, inputs and monitoring artifacts through MLflow/OpenTelemetry where useful.
4. Add standard named stress scenarios and liquidity-horizon metadata without local risk scores.
5. Evaluate mature portfolio-risk libraries before writing any additional covariance/tail aggregation logic.
