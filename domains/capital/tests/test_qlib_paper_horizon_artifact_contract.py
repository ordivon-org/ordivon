"""Real R3 hypothetical Qlib consumer: model SHA, forecast time and exit semantics.

Synthetic private parquet/CSV; no external provider, broker, Paper PG or capital grant.
"""
from __future__ import annotations

import hashlib
import importlib.util
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from ordivon_capital.markets.equity_ohlcv_shape import require_ohlcv_shape_for_hilo
from ordivon_capital.markets.equity_session_calendar import require_xnys_session_grid

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "adoption/r3_native/tests/probe_qlib_paper_horizon.py"
)
SYMBOLS = ("IWM", "QQQ", "SPY")


def _script_module():
    spec = importlib.util.spec_from_file_location("finance_r3_hypothetical_consumer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_bundle(tmp_path, monkeypatch, *, hold=5, exit_kind="next_open"):
    module = _script_module()
    monkeypatch.setattr(module, "OUT", tmp_path)
    sessions = []
    cursor = date(2025, 10, 1)
    while len(sessions) < hold + 4:
        if cursor.weekday() < 5:
            sessions.append(cursor.isoformat())
        cursor += timedelta(days=1)
    entry_ix = 1
    exit_ix = hold + (exit_kind == "next_open")
    decision = sessions[0]
    result_rows = []
    label_rows = []
    receipts = []
    for symbol, offset, score in (("IWM", 1, "0.03"), ("QQQ", 2, "0.02"),
                                  ("SPY", 3, "0.01")):
        opening = [100 + offset * j for j in range(len(sessions))]
        closes = [p + offset for p in opening]
        source = tmp_path / f"openbb_cboe_{symbol}_normalized.csv"
        with source.open("w") as fp:
            fp.write("session_date,open,high,low,close,volume\n")
            for day, op, close in zip(sessions, opening, closes, strict=True):
                fp.write(f"{day},{op},{close + 1},{op - 1},{close},1000\n")
        normalized = source.read_bytes()
        original = pd.read_csv(source)
        receipts.append({
            "symbol": symbol,
            "provider": "cboe",
            "normalized_sha256": hashlib.sha256(normalized).hexdigest(),
            "session_grid_qualification": require_xnys_session_grid(
                original["session_date"], symbol=symbol,
                requested_start=sessions[0], requested_end=sessions[-1],
            ),
            "hilo_source_shape_qualification": require_ohlcv_shape_for_hilo(
                original.set_index("session_date"), symbol=symbol,
            ),
        })
        label = (
            (opening[exit_ix] if exit_kind == "next_open" else closes[exit_ix])
            / opening[entry_ix] - 1
        )
        label_rows.append(label)
        result_rows.append((decision, symbol, score))
    column = (
        "predicted_next_open_to_next_open_fractional_return" if exit_kind == "next_open"
        else "predicted_next_open_to_close_fractional_return"
    )
    csv_content = (
        f"datetime,instrument,{column}\n"
        + "".join(f"{day},{s},{v}\n" for day, s, v in result_rows)
    ).encode()
    (tmp_path / "qlib_test_predictions.csv").write_bytes(csv_content)
    index = pd.MultiIndex.from_tuples(
        [(decision, s) for s in SYMBOLS], names=["datetime", "instrument"],
    )
    pd.DataFrame({
        ("label", "LABEL0"): label_rows,
        ("feature", "RET1"): [0.0] * len(label_rows),
    }, index=index).to_parquet(tmp_path / "qlib_static_dataset.parquet")
    label_step = hold + (exit_kind == "next_open")
    report = {
        "qlib_prediction_sha256": hashlib.sha256(csv_content).hexdigest(),
        "qlib_dataset_sha256": hashlib.sha256(
            (tmp_path / "qlib_static_dataset.parquet").read_bytes()
        ).hexdigest(),
        "provider_receipts": receipts,
        "portfolio_target": None,
        "signal_quality": {
            "standing": "RETROSPECTIVE_BACKFILL_TEST_ONLY",
            "holding_sessions": hold,
            "purged_overlapping_train_validation_labels": True,
            "multi_session_holding_state_representable": True,
            "exit_price_kind": exit_kind,
            "label_forward_sessions": label_step,
            "horizon": (
                f"decision_after_T_close_entry_T_plus_1_open_exit_T_plus_{label_step}_"
                f"{'open' if exit_kind == 'next_open' else 'close'}"
            ),
            "matches_native_fixed_holding_exit_event": exit_kind == "next_open",
            "sample_rows": 3, "sample_sessions": 1,
        },
        "forecast": {
            "kind": "uncalibrated_multisession_holding_return",
            "holding_sessions": hold,
            "exit_price_kind": exit_kind,
            "target_horizon": (
                f"next_session_open_to_T_plus_{label_step}_"
                f"{'open' if exit_kind == 'next_open' else 'close'}"
            ),
            "native_strategy_exit_event_matches_target": exit_kind == "next_open",
            "point_in_time_eligible": False,
        },
    }
    return module, report


@pytest.mark.parametrize("exit_kind", ["next_open", "close"])
def test_real_hypothetical_qlib_model_matches_declared_label_and_portfolio_replay(
    tmp_path, monkeypatch, exit_kind,
):
    module, study = _source_bundle(tmp_path, monkeypatch, exit_kind=exit_kind)
    result = module.run_multisession(study, 5)
    assert result["exit_price_kind"] == exit_kind
    assert result["holding_sessions"] == 5
    assert result["chosen_assets"] == {"IWM": 1}
    assert result["source_historical_PIT"] is False
    assert result["PortfolioIntent_admitted"] is False
    assert result["PG_or_broker_effects"] == "NONE"
    assert (tmp_path / "qlib_disjoint_holding_economic_result.json").is_file()


@pytest.mark.parametrize("field, key, corrupt", [
    ("signal_quality", "horizon", "wrong-time-event"),
    ("signal_quality", "label_forward_sessions", 5),
    ("forecast", "holding_sessions", 20),
    ("forecast", "exit_price_kind", "close"),
    ("forecast", "target_horizon", "next_session_open_to_T_plus_5_close"),
    ("forecast", "native_strategy_exit_event_matches_target", False),
])
def test_hypothetical_economic_comparison_rejects_wrong_study_target_before_reading_prices(
    tmp_path, monkeypatch, field, key, corrupt,
):
    module, report = _source_bundle(tmp_path, monkeypatch)
    invalid = deepcopy(report)
    invalid[field][key] = corrupt
    with pytest.raises((ValueError, AssertionError), match="horizon|forecast|label|target|exit"):
        module.run_multisession(invalid, 5)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


def test_hypothetical_consumer_rejects_changed_score_csv_even_if_column_named(
    tmp_path, monkeypatch,
):
    module, report = _source_bundle(tmp_path, monkeypatch)
    csv_file = tmp_path / "qlib_test_predictions.csv"
    csv_file.write_bytes(csv_file.read_bytes().replace(b"0.03", b"0.93"))
    with pytest.raises((ValueError, AssertionError), match="digest|sha|snapshot|prediction"):
        module.run_multisession(report, 5)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


def test_hypothetical_consumer_cannot_replay_modified_provider_rows_with_old_receipt(
    tmp_path, monkeypatch,
):
    module, report = _source_bundle(tmp_path, monkeypatch)
    prices = tmp_path / "openbb_cboe_IWM_normalized.csv"
    # A blank trailing row does not change the parsed market price series.
    prices.write_bytes(prices.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="source snapshot digest"):
        module.run_multisession(report, 5)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


def test_hypothetical_consumer_rejects_changed_qlib_dataset_unrelated_feature(
    tmp_path, monkeypatch,
):
    module, report = _source_bundle(tmp_path, monkeypatch)
    path = tmp_path / "qlib_static_dataset.parquet"
    dataset = pd.read_parquet(path)
    dataset[("feature", "RET1")] = [1.0, 2.0, 3.0]
    dataset.to_parquet(path)
    with pytest.raises(ValueError, match="dataset snapshot digest"):
        module.run_multisession(report, 5)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


@pytest.mark.parametrize("wrong_target", [False, True])
def test_h1_hypothetical_preflight_matches_producer_without_replaying_future(
    tmp_path, monkeypatch, wrong_target,
):
    import json

    module = _script_module()
    monkeypatch.setattr(module, "OUT", tmp_path)
    report = {
        "portfolio_target": None,
        "signal_quality": {
            "standing": "RETROSPECTIVE_BACKFILL_TEST_ONLY",
            "horizon": "decision_after_T_close_entry_at_T_plus_1_open_exit_at_T_plus_1_close",
            "holding_sessions": 1,
            "exit_price_kind": "close",
            "label_forward_sessions": 1,
            "outperforms_both_unconditional_baselines": False,
        },
        "forecast": {
            "kind": "uncalibrated_next_session_open_to_close_fractional_regression",
            "holding_sessions": 1,
            "exit_price_kind": "close",
            "target_horizon": "new_entry_next_session_open_to_close",
            "native_strategy_exit_event_matches_target": False,
            "point_in_time_eligible": False,
            "paper_buy_and_hold_consumer_horizon_compatible": False,
        },
        "qlib_prediction_sha256": "a" * 64,
    }
    if wrong_target:
        report["forecast"]["target_horizon"] = "next_session_close_to_close"
    (tmp_path / "native_study_result.json").write_text(json.dumps(report))

    class ReachedSourceReader(Exception):
        pass

    def reader(exit_kind, digest):
        assert exit_kind == "close" and digest == "a" * 64
        raise ReachedSourceReader

    monkeypatch.setattr(module, "_native_prediction_scores", reader)
    if wrong_target:
        with pytest.raises(ValueError, match="forecast target/label"):
            module.run()
    else:
        # A qualified H1 forecast reaches the actual byte-bound reader;
        # this deliberately does not claim the full 816-row experiment ran.
        with pytest.raises(ReachedSourceReader):
            module.run()


@pytest.mark.parametrize(
    ("poison", "message"),
    (
        ("impossible_high", "OHLC_BOUNDS_INVALID_FOR_HILO"),
        ("invented_weekend", "XNYS_SESSION_GRID_MISMATCH"),
        ("missing_shape_receipt", "source OHLCV qualification"),
        ("missing_calendar_receipt", "source session qualification"),
    ),
)
def test_native_portfolio_refuses_digest_bound_unqualified_market_bars(
    tmp_path, monkeypatch, poison, message,
):
    """The actual Portfolio consumer must independently recheck Markets qualifiers."""
    module, report = _source_bundle(tmp_path, monkeypatch)
    receipt = next(r for r in report["provider_receipts"] if r["symbol"] == "SPY")
    path = tmp_path / "openbb_cboe_SPY_normalized.csv"
    if poison == "missing_shape_receipt":
        receipt.pop("hilo_source_shape_qualification")
    elif poison == "missing_calendar_receipt":
        receipt.pop("session_grid_qualification")
    else:
        frame = pd.read_csv(path)
        if poison == "impossible_high":
            frame.loc[0, "high"] = frame.loc[0, "close"] - 1
        else:
            # Preserve monotonic order so the test specifically challenges XNYS.
            frame.loc[2, "session_date"] = "2025-10-04"
        frame.to_csv(path, index=False)
        receipt["normalized_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match=message):
        module._native_pinned_bars("SPY", report)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


def test_successful_consumer_emits_exact_study_identity(tmp_path, monkeypatch):
    module, report = _source_bundle(tmp_path, monkeypatch)
    result = module.run_multisession(report, 5)
    identity = result["native_study_identity"]
    assert identity["exitPriceKind"] == "next_open"
    assert identity["holdingSessions"] == 5
    assert identity["forecastTargetHorizon"] == report["forecast"]["target_horizon"]
    assert identity["qlibPredictionSha256"] == report["qlib_prediction_sha256"]
    assert identity["qlibDatasetSha256"] == report["qlib_dataset_sha256"]
    assert identity["sourceReceipts"] == {
        row["symbol"]: row["normalized_sha256"] for row in report["provider_receipts"]
    }
    assert identity["sourceStanding"] == "LOCAL_STUDY_BYTES_BOUND_NOT_PROVIDER_OR_PIT_ATTESTED"


@pytest.mark.parametrize("mutation", ["extra", "missing", "duplicate", "wrong_provider"])
def test_native_economics_requires_exact_source_universe(tmp_path, monkeypatch, mutation):
    module, report = _source_bundle(tmp_path, monkeypatch)
    rows = report["provider_receipts"]
    if mutation == "extra":
        rows.append({**rows[0], "symbol": "OTHER"})
    elif mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1]["symbol"] = rows[0]["symbol"]
    else:
        rows[0]["provider"] = "unknown"
    with pytest.raises(ValueError, match="source receipt|source snapshot identity"):
        module.run_multisession(report, 5)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


@pytest.mark.parametrize("mutation", ["duplicate_prediction", "extra_instrument", "duplicate_label",
                                      "missing_label"])
def test_hash_matched_malformed_keys_do_not_reach_economics(tmp_path, monkeypatch, mutation):
    module, report = _source_bundle(tmp_path, monkeypatch)
    if mutation in {"duplicate_prediction", "extra_instrument"}:
        path = tmp_path / "qlib_test_predictions.csv"
        frame = pd.read_csv(path)
        if mutation == "duplicate_prediction":
            frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        else:
            frame.loc[0, "instrument"] = "OTHER"
        frame.to_csv(path, index=False)
        report["qlib_prediction_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        path = tmp_path / "qlib_static_dataset.parquet"
        frame = pd.read_parquet(path)
        frame = (
            pd.concat([frame, frame.iloc[[0]]])
            if mutation == "duplicate_label" else frame.iloc[1:]
        )
        frame.to_parquet(path)
        report["qlib_dataset_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="duplicate|corresponding|exact ETF"):
        module.run_multisession(report, 5)
    assert not (tmp_path / "qlib_disjoint_holding_economic_result.json").exists()


def test_cross_study_close_prediction_cannot_be_relabelled_next_open(tmp_path, monkeypatch):
    module, report = _source_bundle(tmp_path, monkeypatch, exit_kind="close")
    skill = report["signal_quality"]
    forecast = report["forecast"]
    skill.update(
        exit_price_kind="next_open", label_forward_sessions=6,
        horizon="decision_after_T_close_entry_T_plus_1_open_exit_T_plus_6_open",
        matches_native_fixed_holding_exit_event=True,
    )
    forecast.update(
        exit_price_kind="next_open", target_horizon="next_session_open_to_T_plus_6_open",
        native_strategy_exit_event_matches_target=True,
    )
    # Even after all metadata is changed, the old CLOSE prediction column
    # is still from a different model and may not be consumed.
    with pytest.raises(ValueError, match="prediction column schema"):
        module.run_multisession(report, 5)
