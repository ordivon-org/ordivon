"""Read-only native OpenBB V5 -> Qlib DatasetH/Recorder -> PyPortfolioOpt ETF study.

No broker order, PG posting, or point-in-time historical availability claim.
Data is captured NOW; a retrospective backfill does not prove what was known THEN.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from io import BytesIO
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
# A pinned normalized capture is an offline reproducibility input only; it
# never retroactively proves historical PIT availability or adjustment basis.
capture_path = os.environ.get("ORDIVON_FINANCE_R3_CAPTURE_DIR")
capture_dir = Path(capture_path).resolve() if capture_path else None
if capture_dir is not None:
    prior_result = json.loads((capture_dir / "native_study_result.json").read_text(encoding="utf-8"))
    if prior_result.get("kind") != "ordivon.finance.r3.native-etf-research-only":
        raise ValueError("Capture manifest kind does not match this consumer")
    expected_sources = {r["symbol"]: r for r in prior_result["provider_receipts"]}
    if set(expected_sources) != set(SYMBOLS):
        raise ValueError("Pinned capture must cover the entire declared ETF universe")

frames: list[pd.DataFrame] = []
prices: dict[str, pd.Series] = {}
provider_receipts: list[dict] = []
for symbol in SYMBOLS:
    if capture_dir is None:
        requested = datetime.now(timezone.utc).isoformat()
        response = obb.cboe.equity.historical(
            symbol=symbol, start_date=START, end_date=END, provider="cboe"
        )
        received = datetime.now(timezone.utc).isoformat()
        provider_name = str(response.provider)
        raw_normalized = response.to_dataframe().sort_index()
    else:
        origin = expected_sources[symbol]
        pinned_file = capture_dir / f"openbb_cboe_{symbol}_normalized.csv"
        pinned_bytes = pinned_file.read_bytes()
        if sha256(pinned_bytes).hexdigest() != origin["normalized_sha256"]:
            raise ValueError(f"Capture hash mismatch: {symbol}")
        requested = origin["requested_at"]
        received = origin["received_at"]
        provider_name = str(origin["provider"])
        if provider_name != "cboe":
            raise ValueError(f"Unexpected pinned provider: {provider_name}")
        raw_normalized = pd.read_csv(BytesIO(pinned_bytes), index_col="session_date").sort_index()
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
    if capture_dir is None:
        raw_normalized.to_csv(snapshot, index_label="session_date")
    elif snapshot.resolve() != pinned_file.resolve():
        # Parse and persist exactly the SAME hash-admitted immutable bytes.
        # Re-opening the source path would reintroduce check/use TOCTOU.
        snapshot.write_bytes(pinned_bytes)
    if capture_dir is not None and sha256(snapshot.read_bytes()).hexdigest() != origin["normalized_sha256"]:
        raise ValueError(f"Immutable capture was altered during replay: {symbol}")
    provider_receipts.append({
        "input_mode": "hash_verified_local_replay" if capture_dir is not None else "OpenBB_native_provider_capture",
        "symbol": symbol,
        "provider": provider_name,
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
    dates = pd.DatetimeIndex(pd.to_datetime(x.index)).as_unit("ns")
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
    # A post-T-close decision filled at next-session OPEN is exposed to
    # next-session OPEN -> CLOSE price change, not T close -> T+1 close.
    # This is a *research label* only, not proof of opening fill quality.
    next_open = x["open"].astype(float).shift(-1)
    label = pd.DataFrame({
        "LABEL0": (close.shift(-1) / next_open - 1.0).to_numpy()
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
predictions.to_csv(prediction_snapshot, header=["predicted_next_open_to_close_fractional_return"])
pred_table = predictions.unstack("instrument").dropna()
decision_at = pd.Timestamp(pred_table.index.max())
expected_daily = pred_table.loc[decision_at].reindex(SYMBOLS).astype(float)
history = pd.concat(prices.values(), axis=1).sort_index()
prior_returns = history.loc[:decision_at].pct_change(fill_method=None).tail(120).dropna()
if len(prior_returns) < 90:
    raise ValueError("Insufficient trailing return observations for covariance")
cov_annual = prior_returns.cov() * 252.0
# Semantic gate: a retrospective, uncalibrated Qlib regression score is
# NOT an admitted expected-return vector. Demonstrate the optimizer only on
# independent historical covariance; no executable portfolio target emerges.
assert all(receipt["historical_available_at"] == "UNKNOWN" for receipt in provider_receipts)
optimizer = EfficientFrontier(None, cov_annual, weight_bounds=(0, 1))
weights = optimizer.min_volatility()
if abs(sum(weights.values()) - 1.0) > 1e-6:
    raise AssertionError("Native min-variance demonstration weights do not sum to one")
result = {
    "kind": "ordivon.finance.r3.native-etf-research-only",
    "audited_capital_source_cut": "c883db3bbe211b8a963a3236599e1dc3cfe362ac",
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "data_input_mode": "hash_verified_local_replay" if capture_dir is not None else "OpenBB_native_provider_capture",
    "replay_is_historical_pit": False,
    "provider_receipts": provider_receipts,
    "qlib_version": qlib.__version__,
    "session_index_unit": "datetime64[ns] canonical date label",
    "qlib_dataset_sha256": dataset_digest,
    "qlib_split_rows": {"train": len(train), "valid": len(valid), "test": len(test)},
    "qlib_recorder_id": str(recorder_id),
    "qlib_prediction_rows": len(predictions),
    "optim_date": str(decision_at.date()),
    "native_math_only_min_variance_weights": {k: float(v) for k, v in weights.items()},
    "optimizer_input_kind": "trailing_120_session_sample_covariance",
    "optimizer_policy_eligible": False,
    "forecast": {
        "kind": "uncalibrated_next_session_open_to_close_fractional_regression",
        "predicted_next_open_to_close_fractional_returns": {k: float(v) for k, v in expected_daily.items()},
        "target_horizon": "new_entry_next_session_open_to_close",
        "signal_first_available": "UNKNOWN (source backfilled, EOD fields required)",
        "point_in_time_eligible": False,
        "calibrated_conditional_distribution": False,
        "usable_as_optimizer_expected_return": False,
    },
    "portfolio_target": None,
    "dataset_is_historically_point_in_time": False,
    "order_effect": "NONE",
    "accounting_effect": "NONE",
    "economic_performance_verified": False,
}
(OUT / "native_study_result.json").write_text(
    json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
)
print("NATIVE_ETF_STUDY", json.dumps(result, sort_keys=True))
