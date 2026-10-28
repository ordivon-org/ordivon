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
    evaluate_risk_budget,
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


@pytest.mark.parametrize(
    "loadings",
    [
        {"sector": "0.2", " sector ": "0.3"},
        {" sector ": "0.2", "sector": "0.3"},
        {"sector": "0.2", "sector ": "0.3"},
        {1: "0.2", "1": "0.3"},
    ],
)
def test_normalized_factor_alias_must_not_silently_change_risk(
    loadings: dict[object, str],
) -> None:
    """One canonical factor must denote exactly one raw loading at source ingress."""
    with pytest.raises(PortfolioRiskError, match="factor"):
        build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="40",
            positions=[
                {
                    "instrumentId": "ASSET-A",
                    "signedNotionalUsd": "100",
                    "factorLoadings": loadings,
                }
            ],
        )


@pytest.mark.parametrize("invalid_loadings", [[], "", False, 0, (), set()])
def test_wrong_type_factor_loadings_must_not_mean_empty_exposure(
    invalid_loadings: object,
) -> None:
    with pytest.raises(PortfolioRiskError, match="factorLoadings"):
        build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="40",
            positions=[
                {
                    "instrumentId": "ASSET-A",
                    "signedNotionalUsd": "100",
                    "factorLoadings": invalid_loadings,
                }
            ],
        )


def test_risk_budget_must_breach_at_exact_decimal_boundary() -> None:
    """Rounded 1/3 passes a 0.333333 limit; true 1/3 must breach, read-only."""
    ledger = build_exposure_ledger(
        equity_usd="3",
        available_equity_usd="2",
        positions=[{
            "instrumentId": "ASSET-A",
            "signedNotionalUsd": "1",
            "factorLoadings": {"micro": "0.0000001"},
        }],
    )
    budget = {
        "maxGrossToEquity": "0.333333",
        "maxLargestPositionGrossShare": "1",
        "minAvailableEquityRatio": "0.1",
        "shockMagnitudePct": "10",
        "maxEquityLossPctAtShock": "100",
    }
    accepted = evaluate_risk_budget(exposure_ledger=ledger, budget=budget)
    assert accepted["standing"] == "BREACHED"
    assert accepted["breachedChecks"] == ["MAX_GROSS_TO_EQUITY"]

    lossy_ledger = dict(ledger, grossToEquity="0.333333")
    incorrect = evaluate_risk_budget(exposure_ledger=lossy_ledger, budget=budget)
    assert incorrect["standing"] == "SATISFIED"
    assert incorrect["breachedChecks"] == []


def test_micro_factor_and_risk_ratios_remain_exact_machine_evidence() -> None:
    """Even if six places are enough for a display, they cannot erase risk."""
    from decimal import Decimal

    ledger = build_exposure_ledger(
        equity_usd="3",
        available_equity_usd="1",
        positions=[{
            "instrumentId": "ASSET-A",
            "signedNotionalUsd": "1",
            "factorLoadings": {"micro": "0.0000001"},
        }],
    )
    assert Decimal(ledger["factorExposure"][0]["signedExposureUsd"]) == Decimal("0.0000001")
    assert Decimal(ledger["factorExposure"][0]["absoluteExposureToGross"]) == Decimal("0.0000001")
    assert Decimal(ledger["grossToEquity"]) == Decimal("1") / Decimal("3")
    assert Decimal(ledger["availableEquityRatio"]) == Decimal("1") / Decimal("3")


@pytest.mark.parametrize(
    ("signed_notional", "loading", "equity"),
    [
        ("10000000", "0.0000001", "10000000"),
        ("100", "0.1234567", "1000"),
        ("100.0000007", "0.5", "1000.0000007"),
        ("-200.0000007", "-0.0000001", "1000"),
        ("100.000001", "0.123456", "1000"),
    ],
)
def test_source_and_derived_ledger_values_do_not_lose_precision(
    signed_notional: str, loading: str, equity: str,
) -> None:
    """Source raw decimals survive exactly; 6dp is a display, not a machine cut."""
    from decimal import Decimal

    ledger = build_exposure_ledger(
        equity_usd=equity,
        available_equity_usd="40.0000007",
        positions=[{
            "instrumentId": "ASSET-A",
            "signedNotionalUsd": signed_notional,
            "factorLoadings": {"sector": loading},
        }],
    )
    normalized = ledger["positions"][0]
    assert Decimal(normalized["signedNotionalUsd"]) == Decimal(signed_notional)
    assert Decimal(normalized["factorLoadings"]["sector"]) == Decimal(loading)
    assert Decimal(ledger["equityUsd"]) == Decimal(equity)
    assert Decimal(ledger["availableEquityUsd"]) == Decimal("40.0000007")
    # This producer-owned check is about exact source and derived values.
    # Downstream scenario display values are verified in their own consumer.
    expected = Decimal(signed_notional) * Decimal(loading)
    assert Decimal(ledger["factorExposure"][0]["signedExposureUsd"]) == expected
    assert Decimal(ledger["grossToEquity"]) == abs(Decimal(signed_notional)) / Decimal(equity)


@pytest.mark.parametrize("signed_notional", ["-100", "0", "75", "125"])
@pytest.mark.parametrize("loading", ["-0.5", "0", "0.5", "1"])
def test_canonical_exposure_equals_counterfactual_consumer_baseline(
    signed_notional: str, loading: str,
) -> None:
    """Finite composition contract: canonical exposure must reach downstream unchanged."""
    from decimal import Decimal

    ledger = build_exposure_ledger(
        equity_usd="100",
        available_equity_usd="40",
        positions=[{
            "instrumentId": "ASSET-A",
            "signedNotionalUsd": signed_notional,
            "factorLoadings": {" sector ": loading},
        }],
    )
    counterfactual = build_action_counterfactual(
        exposure_ledger=ledger,
        scenario={
            "scenarioId": "explicit-de-risk",
            "action": "DE_RISK",
            "instrumentId": "ASSET-A",
            "reductionFraction": "0.25",
        },
    )
    row = ledger["factorExposure"][0]
    before = counterfactual["deltas"]["factorExposure"][0]
    assert row["factor"] == "sector" == before["factor"]
    assert Decimal(row["signedExposureUsd"]) == Decimal(before["beforeUsd"])
    assert Decimal(before["deltaUsd"]) == -Decimal(signed_notional) * Decimal(loading) / 4


def test_same_factor_proxy_cannot_be_double_counted() -> None:
    row = {"factor": "sector", "instrumentId": "PROXY-B", "returns": _returns(0.0008)}
    with pytest.raises(PortfolioRiskError, match="duplicate factor proxy"):
        build_factor_observatory(
            base_instrument_id="ASSET-A",
            base_returns=_returns(0.001),
            factor_proxies=[row, dict(row)],
        )
