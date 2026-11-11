"""Read-only native OpenBB V5 -> Qlib DatasetH/Recorder -> PyPortfolioOpt ETF study.

No broker order, PG posting, or point-in-time historical availability claim.
Data is captured NOW; a retrospective backfill does not prove what was known THEN.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import qlib
from openbb import obb
from pypfopt import EfficientFrontier
from qlib.constant import REG_US
from qlib.contrib.model.gbdt import LGBModel
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP
from qlib.data.dataset.loader import StaticDataLoader
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
os.chdir(ROOT)
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"  # isolated reproducibility proof only; production uses existing PG tracking authority
os.environ["MLFLOW_TRACKING_URI"] = (OUT / "mlruns").resolve().as_uri()
SYMBOLS = ("SPY", "QQQ", "IWM")
START = "2023-01-01"
END = "2026-10-31"

frames: list[pd.DataFrame] = []
prices: dict[str, pd.Series] = {}
provider_receipts: list[dict] = []
for symbol in SYMBOLS:
    requested = datetime.now(timezone.utc).isoformat()
    response = obb.cboe.equity.historical(
        symbol=symbol, start_date=START, end_date=END, provider="cboe"
    )
    received = datetime.now(timezone.utc).isoformat()
    raw_normalized = response.to_dataframe().sort_index()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(raw_normalized.columns):
        raise ValueError(f"Provider {symbol} missing columns {required - set(raw_normalized.columns)}")
    duplicate_rows = int(raw_normalized.index.duplicated(keep=False).sum())
    if duplicate_rows:
        conflict_dates = []
        for date, group in raw_normalized[raw_normalized.index.duplicated(keep=False)].groupby(level=0):
            if not (group.nunique(dropna=False) <= 1).all():
                conflict_dates.append(str(date))
        if conflict_dates:
            raise ValueError(f"Provider {symbol} conflicting duplicate session records: {conflict_dates}")
        raw_normalized = raw_normalized.loc[~raw_normalized.index.duplicated(keep="first")]
        print("EXACT_DUPLICATE_REMOVED", symbol, "rows", duplicate_rows, "same_values_verified", True)
    if len(raw_normalized) < 400 or raw_normalized.index.has_duplicates:
        raise ValueError(f"Provider {symbol} insufficient/duplicate rows: {len(raw_normalized)}")
    snapshot = OUT / f"openbb_cboe_{symbol}_normalized.csv"
    raw_normalized.to_csv(snapshot, index_label="session_date")
    provider_receipts.append({
        "symbol": symbol,
        "provider": str(response.provider),
        "requested_at": requested,
        "received_at": received,
        "first_session": str(raw_normalized.index.min()),
        "last_session": str(raw_normalized.index.max()),
        "rows": len(raw_normalized),
        "normalized_sha256": sha256(snapshot.read_bytes()).hexdigest(),
        "source_raw_wire_captured": False,
        "historical_available_at": "UNKNOWN",
        "adjustment_provenance": "UNKNOWN",
        "corporate_actions_completeness": "UNKNOWN",
        "rights_for_redistribution": "UNKNOWN"
    })
    x = raw_normalized
    dates = pd.to_datetime(x.index)
    index = pd.MultiIndex.from_arrays(
        [dates, [symbol] * len(x)], names=["datetime", "instrument"]
    )
    close = x["close"].astype(float)
    vol = x["volume"].astype(float)
    feature = pd.DataFrame({
        "RET1": close.pct_change(fill_method=None).to_numpy(),
        "MOM5": close.pct_change(5, fill_method=None).to_numpy(),
        "HILO": ((x["high"] - x["low"]) / close).to_numpy(),
        "VOL5": (vol / vol.rolling(5).mean() - 1.0).to_numpy(),
    }, index=index)
    label = pd.DataFrame({
        "LABEL0": (close.shift(-1) / close - 1.0).to_numpy()
    }, index=index)
    frames.append(pd.concat({"feature": feature, "label": label}, axis=1))
    prices[symbol] = pd.Series(close.to_numpy(), index=dates, name=symbol)

data = pd.concat(frames).sort_index()
data = data.replace([np.inf, -np.inf], np.nan).dropna()
dataset_snapshot = OUT / "qlib_static_dataset.parquet"
data.to_parquet(dataset_snapshot)
dataset_digest = sha256(dataset_snapshot.read_bytes()).hexdigest()

provider_root = OUT / "qlib_provider"
provider_root.mkdir(exist_ok=True)
qlib.init(provider_uri=str(provider_root), region=REG_US)
loader = StaticDataLoader(data)
handler = DataHandlerLP(instruments=None, data_loader=loader)
dataset = DatasetH(
    handler=handler,
    segments={
        "train": ("2023-02-01", "2024-12-30"),
        "valid": ("2025-01-01", "2025-09-29"),
        "test": ("2025-10-01", "2026-10-29"),
    },
)
train = dataset.prepare("train", col_set=["feature", "label"])
valid = dataset.prepare("valid", col_set=["feature", "label"])
test = dataset.prepare("test", col_set=["feature", "label"])
if min(len(train), len(valid), len(test)) < 50:
    raise ValueError(f"Qlib segments insufficient: {[len(train), len(valid), len(test)]}")
model = LGBModel(
    loss="mse",
    num_boost_round=60,
    early_stopping_rounds=10,
    learning_rate=0.05,
    num_leaves=10,
    max_depth=4,
    num_threads=2,
    verbosity=-1,
)
with R.start(experiment_name="ordivon_finance_r3_openbb_qlib_native_etf"):
    R.log_params(
        symbols=",".join(SYMBOLS),
        source="openbb-v5-cboe",
        data_digest=dataset_digest,
        point_in_time_qualified=False,
        purpose="research_only_backfilled_no_order",
    )
    model.fit(dataset)
    recorder = R.get_recorder()
    SignalRecord(model=model, dataset=dataset, recorder=recorder).generate()
    predictions = model.predict(dataset, segment="test")
    recorder_id = getattr(recorder, "id", None)
    if recorder_id is None and hasattr(recorder, "info"):
        recorder_id = getattr(recorder.info, "id", None)

if isinstance(predictions, pd.DataFrame):
    predictions = predictions.iloc[:, 0]
prediction_snapshot = OUT / "qlib_test_predictions.csv"
predictions.to_csv(prediction_snapshot, header=["predicted_next_close_return"])
pred_table = predictions.unstack("instrument").dropna()
decision_at = pd.Timestamp(pred_table.index.max())
expected_daily = pred_table.loc[decision_at].reindex(SYMBOLS).astype(float)
history = pd.concat(prices.values(), axis=1).sort_index()
prior_returns = history.loc[:decision_at].pct_change(fill_method=None).tail(120).dropna()
if len(prior_returns) < 90:
    raise ValueError("Insufficient trailing return observations for covariance")
cov_annual = prior_returns.cov() * 252.0
mu_annual = expected_daily * 252.0
optimizer = EfficientFrontier(mu_annual, cov_annual, weight_bounds=(0, 1))
weights = optimizer.max_quadratic_utility(risk_aversion=10.0)
if abs(sum(weights.values()) - 1.0) > 1e-6:
    raise AssertionError("Native optimizer weights do not sum to one")
result = {
    "kind": "ordivon.finance.r3.native-etf-research-only",
    "source_cut": "c883db3bbe211b8a963a3236599e1dc3cfe362ac",
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "provider_receipts": provider_receipts,
    "qlib_version": qlib.__version__,
    "qlib_dataset_sha256": dataset_digest,
    "qlib_split_rows": {"train": len(train), "valid": len(valid), "test": len(test)},
    "qlib_recorder_id": str(recorder_id),
    "qlib_prediction_rows": len(predictions),
    "optim_date": str(decision_at.date()),
    "pypfopt_native_weights": {k: float(v) for k, v in weights.items()},
    "prediction_values_annualized": {k: float(v) for k, v in mu_annual.items()},
    "dataset_is_historically_point_in_time": False,
    "order_effect": "NONE",
    "accounting_effect": "NONE",
    "economic_performance_verified": False,
}
(OUT / "native_study_result.json").write_text(
    json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
)
print("NATIVE_ETF_STUDY", json.dumps(result, sort_keys=True))
