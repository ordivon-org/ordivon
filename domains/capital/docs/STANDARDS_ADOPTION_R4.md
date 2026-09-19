# Market Capital Standards Adoption R4

Date: 2026-09-19
Status: SUPERSEDED BY STANDARDS_ADOPTION_R5

## Objective

Continue the decomposition -> external owner -> substitution -> evidence loop, now applied to the only active quantitative model and to tail-risk measurement.

## Dependence model development testing

`portfolio-dependence-analysis` remains the only active component classified as an SR 26-2 model.

The development-testing path now uses mature scikit-learn components already present in the frozen research environment:

- `TimeSeriesSplit` for ordered walk-forward out-of-time splits;
- `LinearRegression` as the primary linear estimator;
- `HuberRegressor` as a robust alternative-method challenger.

The validator emits per-fold train/test time boundaries, beta/intercept, OOS mean absolute error, residual variance, and variance reduction versus the unhedged base-return variance. It does not invent a pass/fail threshold, select a hedge, size a hedge, forecast return, or approve an order.

SR 26-2 is used proportionately as a governance reference. The current standing is deliberately:

`DEVELOPMENT_TESTED + VALIDATION_REQUIRED`

Developer-run walk-forward evidence is not represented as independent model validation.

## Live public development evidence

A read-only OKX public-data run on 2026-09-19 used completed 1D candles for `SNDK-USDT-SWAP` and three explicit proxies.

| Proxy | Overlap returns | Full corr | Full beta | Median OOT variance reduction (OLS) | Negative OOT folds |
| --- | ---: | ---: | ---: | ---: | ---: |
| MU-USDT-SWAP | 178 | 0.843824 | 1.075095 | 0.698779 | 0/5 |
| SMH-USDT-SWAP | 92 | 0.750325 | 2.140356 | 0.422479 | 1/5 |
| QQQ-USDT-SWAP | 178 | 0.610721 | 3.177404 | 0.363001 | 1/5 |

These measurements demonstrate why full-sample correlation or beta is not promoted into hedge truth: later folds can degrade and can even show negative variance reduction.

Canonical evidence: `evidence/acceptance/dependence-model-oot-validation-r1.json`.

## Historical expected shortfall primitive

`historical_expected_shortfall` is added as a `NON_MODEL_CALCULATION`.

It computes:

1. empirical loss quantile using NumPy;
2. arithmetic mean of observations at or beyond that loss threshold.

The output explicitly records that:

- no distribution is fitted;
- no liquidity-horizon scaling is applied;
- no regulatory-capital calculation is performed.

The Basel market-risk framework is used only as a terminology/method reference. Market Capital is not implementing a Basel IMA capital engine.

## Runtime hygiene

`run-okx-factor-observatory-r1` now executes through the canonical `run-capability-python` environment rather than system Python. This prevents mature numerical dependencies such as SciPy from silently disappearing outside the controlled capability environment.

## Remaining work

1. Independent or structurally separated validation/effective challenge for the dependence model.
2. Repeated out-of-time outcomes monitoring and drift evidence over time.
3. Explicit data-quality/freshness checks on the validation sample.
4. Standard stress/scenario primitives and liquidity-horizon metadata without inventing a local risk score.
5. Bind empirical ES into portfolio reporting only after its sample/window semantics are explicit.
6. Keep hedge sizing, allocation, and execution authority outside the dependence model.
