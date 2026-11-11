# Finance R3 鈥?Native ETF research consumer

Read-only consumer: OpenBB V5 Cboe historical OHLCV -> Qlib native
StaticDataLoader/DatasetH/LGBModel/Recorder/SignalRecord ->
PyPortfolioOpt EfficientFrontier.max_quadratic_utility.

Reproduce on Windows x64 Python 3.11 in separate env:
  uv venv .venv --python 3.11
  uv pip sync --python .venv/Scripts/python.exe requirements.lock
  .venv/Scripts/python.exe etf_qlib_consumer.py

Local output/ ignored by Git includes normalized provider CSV, parquet
dataset, MLflow Recorder, predictions, native_study_result.json.
2026-11-11 backfill DOES NOT PROVE historical availableAt, total-return
adjustments, corporate action correctness or redistribution rights.
No broker orders, paper fills, capital movement, or PG ledger posting.
Only exactly identical duplicated sessions may be removed.
Signal after today's close for next session is NOT known before close.
Annualized predictions and 120-session covariance are for plumbing only.
MLFLOW_ALLOW_FILE_STORE=true is research-only MLflow 3.18 fallback;
production must use existing qualified experiment-tracking authority.
Old custom consumers remain; new adapter is not canonical trading.
See evidence JSON for run identity, output data hashes and UNKNOWN fields.
