import math

import pytest

from ordivon_capital.research.model_monitoring import (
    assess_paired_return_data_quality,
    build_tail_risk_report,
    measure_dependence_drift,
    monitor_dependence_outcomes,
)
from ordivon_capital.risk.portfolio_risk import PortfolioRiskError


def _series(beta: float, start: int, count: int, *, phase: float = 0.0):
    proxy = {}
    base = {}
    for i in range(count):
        t = start + i
        x = 0.01 * math.sin((i + phase) / 4)
        proxy[t] = x
        base[t] = 0.001 + beta * x
    return base, proxy


def test_data_quality_reports_overlap_and_interval_without_status_label():
    base = {1000: 0.01, 2000: 0.02, 3000: -0.01}
    proxy = {1000: 0.02, 3000: -0.02, 4000: 0.01}
    out = assess_paired_return_data_quality(
        base_returns=base,
        proxy_returns=proxy,
        as_of_ms=5000,
        expected_interval_ms=1000,
    )
    assert out["overlapObservationCount"] == 2
    assert out["overlapToUnionRatio"] == "0.500000"
    assert out["latestOverlapAgeMs"] == 2000
    assert "standing" not in out
    assert "severity" not in out


def test_outcomes_monitoring_requires_strictly_later_realized_sample():
    ref_base, ref_proxy = _series(1.5, 1, 40)
    realized_base, realized_proxy = _series(1.5, 100, 12)
    out = monitor_dependence_outcomes(
        base_instrument_id="A",
        proxy_instrument_id="B",
        reference_base_returns=ref_base,
        reference_proxy_returns=ref_proxy,
        realized_base_returns=realized_base,
        realized_proxy_returns=realized_proxy,
    )
    assert float(out["primary"]["realizedVarianceReductionVsUnhedged"]) > 0.99
    assert out["referenceEndObservedAtMs"] < out["realizedStartObservedAtMs"]

    with pytest.raises(PortfolioRiskError):
        monitor_dependence_outcomes(
            base_instrument_id="A",
            proxy_instrument_id="B",
            reference_base_returns=ref_base,
            reference_proxy_returns=ref_proxy,
            realized_base_returns={35 + i: v for i, v in enumerate(realized_base.values())},
            realized_proxy_returns={35 + i: v for i, v in enumerate(realized_proxy.values())},
        )


def test_drift_measurement_reports_continuous_statistics_without_classifier():
    ref_base, ref_proxy = _series(1.0, 1, 40)
    cur_base, cur_proxy = _series(2.0, 100, 20, phase=3)
    out = measure_dependence_drift(
        base_instrument_id="A",
        proxy_instrument_id="B",
        reference_base_returns=ref_base,
        reference_proxy_returns=ref_proxy,
        current_base_returns=cur_base,
        current_proxy_returns=cur_proxy,
    )
    assert float(out["parameterDrift"]["betaDelta"]) > 0.9
    assert "standing" not in out
    assert "severity" not in out
    assert "threshold" not in out


def test_tail_risk_report_preserves_sample_and_horizon_metadata():
    returns = [0.01] * 39 + [-0.20]
    out = build_tail_risk_report(
        [{
            "seriesId": "A",
            "returns": returns,
            "returnHorizon": "1D_LOG_RETURN",
            "sampleLabel": "TEST_SAMPLE",
            "liquidityHorizonDays": 10,
        }],
        confidence=0.975,
    )
    row = out["series"][0]
    assert row["returnHorizon"] == "1D_LOG_RETURN"
    assert row["liquidityHorizonDays"] == 10
    assert out["liquidityHorizonScalingApplied"] is False
    assert float(row["calculation"]["expectedShortfallLossFraction"]) >= float(
        row["calculation"]["valueAtRiskLossFraction"]
    )
