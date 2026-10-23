"""Actual protected-main factor consumers, with no synthetic trading authority."""

from __future__ import annotations

import math

import pytest

from ordivon_capital.portfolio.portfolio_counterfactuals import (
    build_action_counterfactual,
)
from ordivon_capital.risk.portfolio_risk import (
    PortfolioRiskError,
    build_exposure_ledger,
    build_factor_observatory,
    build_portfolio_risk_report,
)


def _returns(scale: float) -> dict[int, float]:
    return {i: scale * math.sin(i / 5) for i in range(1, 90)}


def test_factor_proxy_to_portfolio_risk_is_descriptive_and_nonlive() -> None:
    """Factor/proxy observation → explicit exposure → risk report, no order."""
    factor = build_factor_observatory(
        base_instrument_id="ASSET-A",
        base_returns=_returns(0.001),
        factor_proxies=[
            {"factor": "sector", "instrumentId": "PROXY-B", "returns": _returns(0.0008)}
        ],
    )
    assert factor["componentId"] == "factor-proxy-aggregation"
    assert factor["factorCount"] == 1
    assert factor["factors"][0]["proxies"][0]["proxyInstrumentId"] == "PROXY-B"
    assert "targetPortfolio" not in factor
    assert "tradeSignal" not in factor

    ledger = build_exposure_ledger(
        equity_usd="100",
        available_equity_usd="40",
        positions=[
            {"instrumentId": "ASSET-A", "signedNotionalUsd": "120",
             "factorLoadings": {"sector": "0.5"}}
        ],
    )
    exposure = {item["factor"]: item for item in ledger["factorExposure"]}
    assert exposure["sector"]["signedExposureUsd"] == "60.000000"
    report = build_portfolio_risk_report(exposure_ledger=ledger)
    assert report["nodes"]["riskBudgetRegistration"]["standing"] == "UNSET"
    assert report["nodes"]["riskLimitEvaluation"]["standing"] == "INCOMPLETE"
    assert "order" not in report
    assert "allocationProduced" not in report


def test_factor_labels_do_not_override_counterfactual_authority() -> None:
    ledger = build_exposure_ledger(
        equity_usd="100",
        available_equity_usd="30",
        positions=[
            {"instrumentId": "ASSET-A", "signedNotionalUsd": "80",
             "factorLoadings": {"sector": "1.0"}}
        ],
    )
    out = build_action_counterfactual(
        exposure_ledger=ledger,
        scenario={
            "scenarioId": "explicit-caller-delta",
            "action": "DE_RISK",
            "instrumentId": "ASSET-A",
            "reductionFraction": "0.25",
        },
    )
    assert "rankingProduced" not in out
    assert "winnerSelected" not in out
    assert "executionApproved" not in out


def test_same_factor_proxy_cannot_be_double_counted() -> None:
    row = {"factor": "sector", "instrumentId": "PROXY-B", "returns": _returns(0.0008)}
    with pytest.raises(PortfolioRiskError, match="duplicate factor proxy"):
        build_factor_observatory(
            base_instrument_id="ASSET-A",
            base_returns=_returns(0.001),
            factor_proxies=[row, dict(row)],
        )
