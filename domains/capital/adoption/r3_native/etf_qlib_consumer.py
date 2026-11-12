"""Read-only native OpenBB V5 -> Qlib DatasetH/Recorder -> PyPortfolioOpt ETF study.

No broker order, PG posting, or point-in-time historical availability claim.
Data is captured NOW; a retrospective backfill does not prove what was known THEN.
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path

# Set MLflow authority BEFORE importing Qlib/its MLflow integration. Otherwise
# even a read-only experiment can create a default ./mlruns under caller CWD.
ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get("ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR", str(ROOT / "output"))).resolve()
OUT.mkdir(exist_ok=True)
os.chdir(ROOT)
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"  # isolated reproducibility proof only; production uses existing PG tracking authority
os.environ["MLFLOW_TRACKING_URI"] = (OUT / "mlruns").resolve().as_uri()

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
from qlib.workflow.record_temp import SignalRecord, SigAnaRecord
from qlib.workflow.task.utils import TimeAdjuster
from qlib.workflow.task.gen import trunc_segments

SYMBOLS = ("SPY", "QQQ", "IWM")
# The legacy one-session output is the default; longer horizons are
# read-only retrospective research experiments, NEVER order authority.
HOLD_SESSIONS = int(os.environ.get("ORDIVON_FINANCE_R3_RESEARCH_HOLD_SESSIONS", "1"))
if HOLD_SESSIONS not in (1, 5, 20):
    raise ValueError("Research holding-horizon options are 1, 5 or 20 sessions")
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
        requested = datetime.now(UTC).isoformat()
        response = obb.cboe.equity.historical(
            symbol=symbol, start_date=START, end_date=END, provider="cboe"
        )
        received = datetime.now(UTC).isoformat()
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
    # Decision after T close, enter T+1 OPEN, exit T+H CLOSE.
    # Match the cross-session Paper holding period before testing skill;
    # no point-in-time execution or source rights are implied by a label.
    next_open = x["open"].astype(float).shift(-1)
    label = pd.DataFrame({
        "LABEL0": (close.shift(-HOLD_SESSIONS) / next_open - 1.0).to_numpy()
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
segments = {
    "train": ("2023-02-01", "2024-12-30"),
    "valid": ("2025-01-01", "2025-09-29"),
    "test": ("2025-10-01", "2026-10-29"),
}
if HOLD_SESSIONS > 1:
    # Reuse Qlib TimeAdjuster/trunc_segments with this OFFLINE capture's
    # actual exchange-session calendar (D.calendar is not installed for the
    # isolated StaticDataLoader). This is not a new calendar engine.
    exchange_sessions = data.index.get_level_values("datetime").unique().sort_values()
    native_calendar = TimeAdjuster.__new__(TimeAdjuster)
    native_calendar._future = False
    native_calendar.cals = list(exchange_sessions)
    segments = native_calendar.align_seg(segments)
    trunc_segments(native_calendar, segments, HOLD_SESSIONS + 1, test_key="test")
    train_valid = {"train": segments["train"], "valid": segments["valid"]}
    trunc_segments(native_calendar, train_valid, HOLD_SESSIONS + 1, test_key="valid")
    segments["train"] = train_valid["train"]
    index_by_session = {day: pos for pos, day in enumerate(exchange_sessions)}
    for older, newer in (("train", "valid"), ("valid", "test")):
        if index_by_session[segments[older][1]] + HOLD_SESSIONS >= index_by_session[segments[newer][0]]:
            raise ValueError(f"Research target leaks future labels across {older}/{newer}")
dataset = DatasetH(handler=handler, segments=segments)
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
    # Qlib's mature signal-evaluation recorder computes test-segment daily
    # cross-sectional IC/RankIC. With only three ETFs it has high sampling
    # noise; never equate that number with an executable strategy or alpha.
    SigAnaRecord(recorder=recorder, ana_long_short=False).generate()
    native_signal_metrics = recorder.list_metrics()
    predictions = model.predict(dataset, segment="test")
    recorder_id = getattr(recorder, "id", None)
    if recorder_id is None and hasattr(recorder, "info"):
        recorder_id = getattr(recorder.info, "id", None)

if isinstance(predictions, pd.DataFrame):
    predictions = predictions.iloc[:, 0]
# Evaluate the ACTUAL out-of-sample open-to-close target, not the in-sample
# fit loss or a hypothetical same-close/next-close execution shortcut.
# The zero predictor and a TRAIN-only unconditional mean are conservative
# nontrading baselines. This measures retrospective predictive skill only.
actual_test = dataset.prepare("test", col_set="label").iloc[:, 0].astype(float)
predicted_test = predictions.astype(float)
if actual_test.index.has_duplicates or predicted_test.index.has_duplicates:
    raise ValueError("Duplicate test sample index prevents OOS evaluation")
if not actual_test.index.equals(predicted_test.index):
    # Both representations must refer to exactly the same sessions/assets:
    # missing or reordered predictions may silently inflate scores.
    if len(actual_test) != len(predicted_test) or set(actual_test.index) != set(predicted_test.index):
        raise ValueError("Qlib predictions and realized labels have different test samples")
    predicted_test = predicted_test.reindex(actual_test.index)
realized = actual_test.to_numpy(dtype=float)
forecast_values = predicted_test.to_numpy(dtype=float)
historical_train = train["label"].iloc[:, 0].to_numpy(dtype=float)
if (
    len(realized) < 50
    or not np.isfinite(realized).all()
    or not np.isfinite(forecast_values).all()
    or not np.isfinite(historical_train).all()
):
    raise ValueError("Test-signal measurement requires finite nonempty OOS rows")
train_mean = float(historical_train.mean())
# Each ETF's own prior-only unconditional mean is an additional inexpensive
# baseline. A model beating a zero vector alone is not predictive alpha.
per_instrument_train_mean = train["label"].iloc[:, 0].groupby(level="instrument").mean()
instrument_train_baseline = np.array([
    per_instrument_train_mean[instrument]
    for instrument in actual_test.index.get_level_values("instrument")
], dtype=float)
per_instrument_train_mse = float(np.mean((realized - instrument_train_baseline) ** 2))
model_mse = float(np.mean((realized - forecast_values) ** 2))
zero_mse = float(np.mean(realized**2))
train_mean_mse = float(np.mean((realized - train_mean) ** 2))
if min(zero_mse, train_mean_mse) <= 0:
    raise ValueError("Degenerate realized labels cannot establish forecast skill")
skill = {
    "standing": "RETROSPECTIVE_BACKFILL_TEST_ONLY",
    "horizon": (
        "decision_after_T_close_entry_at_T_plus_1_open_exit_at_T_plus_1_close"
        if HOLD_SESSIONS == 1
        else f"decision_after_T_close_entry_T_plus_1_open_exit_T_plus_{HOLD_SESSIONS}_close"
    ),
    "holding_sessions": HOLD_SESSIONS,
    "purged_overlapping_train_validation_labels": HOLD_SESSIONS > 1,
    "approx_nonoverlapping_test_blocks": int(np.ceil(
        len(actual_test.index.get_level_values("datetime").unique()) / HOLD_SESSIONS
    )),
    "sample_rows": int(len(realized)),
    "sample_sessions": int(len(actual_test.index.get_level_values("datetime").unique())),
    "asset_universe": list(SYMBOLS),
    "model_mse": model_mse,
    "zero_return_baseline_mse": zero_mse,
    "train_only_mean_baseline_mse": train_mean_mse,
    "train_only_each_instrument_mean_mse": per_instrument_train_mse,
    "model_mse_reduction_vs_each_instrument_mean": float(
        1.0 - model_mse / per_instrument_train_mse
    ),
    "model_mse_reduction_vs_zero": float(1.0 - model_mse / zero_mse),
    "model_mse_reduction_vs_train_only_mean": float(1.0 - model_mse / train_mean_mse),
    # A purely empirical OOS dominance check, NOT trading authorization.
    "outperforms_both_unconditional_baselines": bool(
        model_mse < zero_mse and model_mse < train_mean_mse
    ),
    "qlib_native_signal_analysis_metrics": {
        key: float(value) for key, value in native_signal_metrics.items()
        if key in ("IC", "ICIR", "Rank IC", "Rank ICIR")
    },
    "prices_from_historical_backfill": True,
    "transaction_costs_and_market_impact_modeled": False,
    # An actual Research-derived SELL order is still missing from this
    # consumer, even when the multi-session Paper state can represent it.
    "paper_buy_and_hold_consumer_horizon_compatible": False,
    # A multi-session holding is representable as successive PaperSessions
    # with a later sell, but no real research-driven exit order exists yet.
    "multi_session_holding_state_representable": HOLD_SESSIONS > 1,
    "profitable_executable_strategy_demonstrated": False,
}
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
    "captured_at": datetime.now(UTC).isoformat(),
    "data_input_mode": "hash_verified_local_replay" if capture_dir is not None else "OpenBB_native_provider_capture",
    "replay_is_historical_pit": False,
    "provider_receipts": provider_receipts,
    "qlib_version": qlib.__version__,
    "session_index_unit": "datetime64[ns] canonical date label",
    "qlib_dataset_sha256": dataset_digest,
    "qlib_split_rows": {"train": len(train), "valid": len(valid), "test": len(test)},
    "qlib_recorder_id": str(recorder_id),
    "qlib_prediction_rows": len(predictions),
    "signal_quality": skill,
    "optim_date": str(decision_at.date()),
    "native_math_only_min_variance_weights": {k: float(v) for k, v in weights.items()},
    "optimizer_input_kind": "trailing_120_session_sample_covariance",
    "optimizer_policy_eligible": False,
    "forecast": {
        "kind": (
            "uncalibrated_next_session_open_to_close_fractional_regression"
            if HOLD_SESSIONS == 1 else "uncalibrated_multisession_holding_return"
        ),
        **{(
            "predicted_next_open_to_close_fractional_returns"
            if HOLD_SESSIONS == 1 else "predicted_next_open_to_holding_exit_fractional_returns"
        ): {k: float(v) for k, v in expected_daily.items()}},
        "target_horizon": (
            "new_entry_next_session_open_to_close"
            if HOLD_SESSIONS == 1 else f"next_session_open_to_T_plus_{HOLD_SESSIONS}_close"
        ),
        "holding_sessions": HOLD_SESSIONS,
        "paper_buy_and_hold_consumer_horizon_compatible": False,
        "multi_session_holding_state_representable": HOLD_SESSIONS > 1,
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
