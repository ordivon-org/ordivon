"""Native Qlib economics cannot silently reuse a CLOSE study as NEXT_OPEN.

Imports the actual existing Portfolio economic consumer, not a cloned parser.
Test-only synthetic bytes are intentionally not a Qlib trained model; no
PIT, price adjustment, source licence, orders or real profit are certified.
"""
from __future__ import annotations

import importlib.util
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

from ordivon_capital.markets.equity_ohlcv_shape import require_ohlcv_shape_for_hilo
from ordivon_capital.markets.equity_session_calendar import require_xnys_session_grid

SOURCE = Path(__file__).resolve().parents[1] / (
    "adoption/r3_native/tests/probe_qlib_paper_horizon.py"
)


def consumer():
    spec = importlib.util.spec_from_file_location(
        "finance_native_qlib_study_identity_under_test", SOURCE
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path, monkeypatch):
    module = consumer()
    monkeypatch.setattr(module, "OUT", tmp_path)

    rows = [
        ("2026-10-01", "SPY", 0.01),
        ("2026-10-01", "QQQ", 0.02),
        ("2026-10-01", "IWM", 0.03),
    ]
    prediction = tmp_path / "qlib_test_predictions.csv"
    prediction.write_text(
        "datetime,instrument,prediction\n"
        + "".join(f"{d},{s},{v}\n" for d, s, v in rows)
    )
    index = pd.MultiIndex.from_tuples(
        [(pd.Timestamp(d), s) for d, s, _ in rows],
        names=["datetime", "instrument"],
    )
    dataset = tmp_path / "qlib_static_dataset.parquet"
    columns = pd.MultiIndex.from_tuples([("label", "LABEL0")])
    pd.DataFrame([[0.015]] * len(rows), index=index, columns=columns).to_parquet(dataset)

    receipts = []
    for ticker in ("IWM", "QQQ", "SPY"):
        source = tmp_path / f"openbb_cboe_{ticker}_normalized.csv"
        source.write_text(
            "session_date,open,high,low,close,volume\n"
            "2026-10-01,100,102,98,100,10000\n"
            "2026-10-02,101,103,99,102,10100\n"
        )
        source_frame = pd.read_csv(source)
        receipts.append({
            "symbol": ticker,
            "provider": "cboe",
            "normalized_sha256": sha256(source.read_bytes()).hexdigest(),
            "session_grid_qualification": require_xnys_session_grid(
                source_frame["session_date"], symbol=ticker,
                requested_start="2026-10-01", requested_end="2026-10-02",
            ),
            "hilo_source_shape_qualification": require_ohlcv_shape_for_hilo(
                source_frame.set_index("session_date"), symbol=ticker,
            ),
        })

    report = {
        "kind": "ordivon.finance.r3.native-etf-research-only",
        "qlib_prediction_sha256": sha256(prediction.read_bytes()).hexdigest(),
        "qlib_dataset_sha256": sha256(dataset.read_bytes()).hexdigest(),
        "provider_receipts": receipts,
        "signal_quality": {"holding_sessions": 20, "exit_price_kind": "close"},
        "forecast": {
            "holding_sessions": 20,
            "exit_price_kind": "close",
            "target_horizon": "next_session_open_to_T_plus_20_close",
        },
    }
    return module, report


def test_native_study_reads_only_exact_consumed_prediction_label_and_source_bytes(
    tmp_path, monkeypatch,
):
    module, report = fixture(tmp_path, monkeypatch)
    predicted, labels, bars = module._native_study_inputs(report)
    assert len(predicted) == len(labels) == 3
    assert set(bars) == {"IWM", "QQQ", "SPY"}
    assert module._study_identity(report)["exitPriceKind"] == "close"


@pytest.mark.parametrize("role", ["predictions", "labels", "market_spy"])
def test_changed_single_study_artifact_fails_before_portfolio_economics(
    tmp_path, monkeypatch, role,
):
    module, report = fixture(tmp_path, monkeypatch)
    path = {
        "predictions": tmp_path / "qlib_test_predictions.csv",
        "labels": tmp_path / "qlib_static_dataset.parquet",
        "market_spy": tmp_path / "openbb_cboe_SPY_normalized.csv",
    }[role]
    path.write_bytes(path.read_bytes() + b"\nmutated bytes\n")
    with pytest.raises(ValueError, match="study source differs"):
        module._native_study_inputs(report)


def test_closed_h20_old_selected_iwm_cannot_be_misrepresented_as_new_next_open(
    tmp_path, monkeypatch,
):
    module, report = fixture(tmp_path, monkeypatch)
    report["signal_quality"]["exit_price_kind"] = "next_open"
    with pytest.raises(ValueError, match="exit/holding/horizon mismatches"):
        module._study_identity(report)


def test_cross_horizon_model_prediction_identity_must_not_be_inferred_from_hold_only(
    tmp_path, monkeypatch,
):
    module, report = fixture(tmp_path, monkeypatch)
    report["forecast"]["exit_price_kind"] = "next_open"
    report["forecast"]["target_horizon"] = "next_session_open_to_T_plus_21_open"
    with pytest.raises(ValueError, match="exit/holding/horizon mismatches"):
        module._study_identity(report)
    report["signal_quality"]["exit_price_kind"] = "next_open"
    assert module._study_identity(report)["forecastTargetHorizon"] == (
        "next_session_open_to_T_plus_21_open"
    )


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "provider"])
def test_every_etf_source_receipt_still_matters(tmp_path, monkeypatch, mutation):
    module, report = fixture(tmp_path, monkeypatch)
    if mutation == "missing":
        report["provider_receipts"].pop()
    elif mutation == "duplicate":
        report["provider_receipts"][-1]["symbol"] = "QQQ"
    else:
        report["provider_receipts"][0]["provider"] = "unknown"
    with pytest.raises(ValueError, match="receipts|provider"):
        module._native_study_inputs(report)


def test_missing_or_malformed_prediction_digest_fails_closed(tmp_path, monkeypatch):
    module, report = fixture(tmp_path, monkeypatch)
    report["qlib_prediction_sha256"] = "UNKNOWN"
    with pytest.raises(ValueError, match="missing exact study"):
        module._native_study_inputs(report)


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        ("invented_holiday", "XNYS_SESSION_GRID_MISMATCH"),
        ("impossible_high", "OHLC_BOUNDS_INVALID_FOR_HILO"),
    ],
)
def test_portfolio_qualifies_same_bytes_market_shape_and_session_even_with_matching_sha(
    tmp_path, monkeypatch, failure, expected,
):
    """A newly recomputed source hash alone must not authorize economic use."""
    module, report = fixture(tmp_path, monkeypatch)
    source = tmp_path / "openbb_cboe_SPY_normalized.csv"
    raw = source.read_text()
    if failure == "invented_holiday":
        changed = raw.replace("2026-10-02,101,103,99,102", "2026-10-03,101,103,99,102")
    else:
        changed = raw.replace("2026-10-01,100,102,98,100", "2026-10-01,100,99,98,100")
    assert changed != raw
    source.write_text(changed)
    report["provider_receipts"][2]["normalized_sha256"] = sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match=expected):
        module._native_study_inputs(report)


def test_portfolio_requires_original_market_qualification_claims(tmp_path, monkeypatch):
    module, report = fixture(tmp_path, monkeypatch)
    report["provider_receipts"][2].pop("session_grid_qualification", None)
    with pytest.raises(ValueError, match="source session qualification"):
        module._native_study_inputs(report)
