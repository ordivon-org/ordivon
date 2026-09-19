# Market Capital Standards Adoption R6

Date: 2026-09-19
Status: CURRENT ARCHITECTURE BASELINE

## Objective

Replace ad-hoc model-monitoring persistence with mature research lineage components and explicitly stop local portfolio-risk algorithm growth where mature external owners already exist.

## Monitoring lineage

The dependence-model monitoring path now materializes through:

Pandera dataframe validation -> Parquet -> DuckDB independent readback -> MLflow run/artifact lineage.

The local code is only an adapter that maps the registered monitoring evidence into these upstream mechanisms. It does not implement a provenance database, experiment tracker, dataframe validator, or analytical storage engine.

The accepted real run produced three monitoring rows, DuckDB independently read back all three rows, and MLflow assigned a run identity. The MLflow backend is local SQLite and is therefore research lineage, not a distributed telemetry or market-truth system.

## OpenTelemetry boundary

OpenTelemetry packages are present transitively, but no authoritative collector/exporter path is currently configured for Market Capital. R6 therefore does not create a local tracing protocol or synthetic trace IDs. OTel remains deferred until an actual collector/backend ownership boundary exists.

## External portfolio-risk owners

Riskfolio-Lib 7.3.0 is the primary future candidate for broad portfolio risk/optimization because it already owns CVaR, semivariance, drawdown risk, risk parity, factor models and many convex risk measures.

PyPortfolioOpt 1.6.0 is a narrower candidate for covariance/risk-model estimation and allocation primitives, including shrinkage covariance, semicovariance and hierarchical methods.

QuantLib 1.43 is a mature future owner for instrument pricing and derivative risk/scenario valuation rather than a reason to duplicate those mechanisms locally.

None is installed in R6. The present workload does not yet require a multi-asset optimizer or derivative-pricing engine, and installing a CVXPY/solver or valuation stack before a real use case would increase dependency surface without replacing active local code.

## Stress/scenario boundary

No new local stress engine is introduced. Existing scenario analysis remains explicit caller-supplied what-if arithmetic. Future multi-asset covariance/tail aggregation must first qualify a mature owner such as Riskfolio-Lib or PyPortfolioOpt. Future derivative scenario valuation must first qualify QuantLib or another mature valuation engine.

## Current quantitative composition

The active quantitative path is now:

authoritative public/provider data -> BCBS-239-style quality checks -> one registered dependence model -> walk-forward development testing -> outcomes/drift monitoring -> Pandera/Parquet/DuckDB/MLflow lineage -> read-only risk report.

Execution policy, accounting and venue truth remain separate.

## Next targets

1. Independent effective challenge for the sole active quantitative model.
2. Repeated monitoring runs over time using the same Parquet/MLflow schema.
3. Add an OpenTelemetry binding only when a real collector/exporter is authoritative.
4. Qualify Riskfolio-Lib/PyPortfolioOpt only when a real multi-asset portfolio-risk requirement appears.
5. Qualify QuantLib when derivative valuation or instrument-level scenario risk becomes active.
