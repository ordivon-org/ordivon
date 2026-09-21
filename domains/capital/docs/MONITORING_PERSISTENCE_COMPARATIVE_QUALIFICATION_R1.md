# Monitoring persistence comparative qualification R1 — 2026-09-21

## Exact current contract

The active Market contract is:

bounded 11-field monitoring-row validation
-> typed PyArrow table
-> Apache Parquet
-> independent DuckDB readback
-> content-addressed manifest

There is no active experiment-tracking server, UI, run search, model registry, cross-run
comparison service, or lineage graph.

## Pandera

The historical implementation used one Pandera 0.33.1 DataFrameSchema. A bounded local
validator was compared against that schema on 400 randomized valid/invalid cases.

- Pandera accepted: 320
- local validator accepted: 320
- acceptance mismatches: 0

The current single-schema contract therefore does not justify retaining a dataframe-validation
framework. Pandera remains a candidate if multiple evolving schemas or materially richer
validation becomes active.

## MLflow

The historical adapter created an MLflow run, logged four params, two metrics, and three
artifacts. No current code consumes the run ID, performs search, uses an MLflow server/UI,
or relies on a registry.

MLflow is therefore removed from the current Market dependency graph. Historical acceptance
evidence containing MLflow run IDs is preserved as historical evidence.

## Dependency subtraction

Removing MLflow, Pandera, and pandas reduced the synced research/test environment from roughly
102 packages to 20 packages. The migration also exposed a hidden ownership bug: scikit-learn
was directly imported by Market code but not directly declared; it had been supplied
transitively through MLflow. scikit-learn 1.9.1 is now an explicit dependency.

## Retained mature primitives

PyArrow 25.0.1 remains the Parquet materialization owner. DuckDB 1.5.5 remains the independent
readback owner. Reimplementing either Parquet encoding or an independent SQL/Parquet engine
locally would enlarge, not reduce, the trusted mechanics surface.
