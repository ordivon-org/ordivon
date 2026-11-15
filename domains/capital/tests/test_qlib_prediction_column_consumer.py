"""A model-score consumer must not rank assets using observed future outcomes."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SOURCE = (
    Path(__file__).resolve().parents[1] / "adoption/r3_native/tests/probe_qlib_paper_horizon.py"
)


def consumer():
    spec = importlib.util.spec_from_file_location("actual_finance_portfolio_score_consumer", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_actual_portfolio_consumer_rejects_label_column_even_with_matching_score(
    tmp_path, monkeypatch
):
    module = consumer()
    monkeypatch.setattr(module, "OUT", tmp_path)
    path = tmp_path / "qlib_test_predictions.csv"
    path.write_text(
        "datetime,instrument,actual_return,predicted_next_open_to_close_fractional_return\n"
        "2026-10-01,SPY,0.99,0.01\n"
        "2026-10-01,IWM,0.01,0.05\n"
    )
    with pytest.raises(ValueError, match="Qlib prediction column schema"):
        module._native_prediction_scores("close")


def test_actual_portfolio_consumer_selects_declared_score_not_label(tmp_path, monkeypatch):
    module = consumer()
    monkeypatch.setattr(module, "OUT", tmp_path)
    path = tmp_path / "qlib_test_predictions.csv"
    path.write_text(
        "datetime,instrument,predicted_next_open_to_next_open_fractional_return\n"
        "2026-10-01,SPY,0.01\n"
        "2026-10-01,IWM,0.05\n"
    )
    scores = module._native_prediction_scores("next_open")
    assert scores.loc[("2026-10-01", "IWM")] > scores.loc[("2026-10-01", "SPY")]
    with pytest.raises(ValueError, match="Qlib prediction column schema"):
        module._native_prediction_scores("close")
