# Portfolio Risk External Owner Audit R6

Date: 2026-09-19

| Responsibility | Mature candidate | Current upstream | Local standing |
| --- | --- | --- | --- |
| broad portfolio risk / CVaR / risk parity / factor optimization | Riskfolio-Lib | 7.3.0 | CANDIDATE_NOT_INSTALLED |
| covariance shrinkage / semicovariance / HRP / efficient frontier | PyPortfolioOpt | 1.6.0 | CANDIDATE_NOT_INSTALLED |
| pricing / derivative analytics / instrument risk | QuantLib | 1.43 | CANDIDATE_NOT_INSTALLED |
| research lineage | MLflow | local 3.16.1 | ACTIVE |
| dataframe validation | Pandera | local 0.33.1 | ACTIVE |
| analytical interchange | Parquet / PyArrow | local PyArrow 25.0.1 | ACTIVE |
| independent analytical readback | DuckDB | local 1.5.5 | ACTIVE |
| distributed telemetry | OpenTelemetry | libraries present, no collector authority | DEFERRED |

Decision: do not add local covariance optimizers, CVaR optimizers, risk-parity engines, derivative pricers, or a provenance database while these mature owners exist. New dependencies are admitted only against an active requirement and a qualification test.
