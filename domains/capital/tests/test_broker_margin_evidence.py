"""Risk evidence consumers: IBKR-style segments + exact declared fills.

Synthetic amounts are mathematical counterexamples, NOT live margin quotes,
broker rules, risk budgets, preferred allocations, or default percentages.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ordivon_capital.risk.portfolio_risk import (
    PortfolioRiskError,
    assess_provider_margin_segments,
    replay_declared_long_liquidation,
)

NOW = datetime(2026, 11, 7, 11, tzinfo=UTC)


def segment(**updates):
    row = {
        "segmentId": "SECURITIES",
        "equityBasis": "EQUITY_WITH_LOAN_VALUE",
        "marginEquityUsd": "1000",
        "initialMarginUsd": "800",
        "maintenanceMarginUsd": "1200",
    }
    row.update(updates)
    return row


def liquidation(**updates):
    sample = dict(
        observed_at=NOW,
        positions=[
            {"instrumentId": "SPY", "quantity": "10", "markPriceUsd": "100"}
        ],
        fills=[
            {"instrumentId": "SPY", "sellQuantity": "3",
             "fillPriceUsd": "90", "feeUsd": "3"}
        ],
        cash_before_usd="10",
        loan_before_usd="600",
        loan_repayment_usd="200",
        provider_maintenance_before_usd="500",
        provider_maintenance_after_usd="350",
    )
    sample.update(updates)
    return sample


def test_broker_segments_must_not_net_a_breach_away():
    securities = segment()
    commodities = segment(
        segmentId="COMMODITIES", equityBasis="NET_LIQUIDATION_VALUE",
        marginEquityUsd="10000", initialMarginUsd="2000",
        maintenanceMarginUsd="1000",
    )
    result = assess_provider_margin_segments(
        observed_at=NOW, provider="IBKR", segments=[securities, commodities]
    )
    assert result["anySegmentMaintenanceBreached"] is True
    a, b = result["segments"]
    assert a["excessLiquidityUsd"] == "-200.000000"
    assert a["maintenanceBreached"] is True
    assert b["excessLiquidityUsd"] == "9000.000000"
    assert b["maintenanceBreached"] is False
    assert result["effectStanding"] == "READ_ONLY_NO_ORDERS_NO_PAPER_LEDGER"


def test_reported_negative_provider_equity_remains_observable():
    out = assess_provider_margin_segments(
        observed_at=NOW, provider="IBKR",
        segments=[segment(marginEquityUsd="-25.1", maintenanceMarginUsd="0")],
    )
    assert out["segments"][0]["excessLiquidityUsd"] == "-25.100000"
    assert out["anySegmentMaintenanceBreached"]


@pytest.mark.parametrize("bad", [
    segment(marginEquityUsd="nan"),
    segment(initialMarginUsd="-1"),
    segment(maintenanceMarginUsd="-1"),
    segment(marginEquityUsd=True),
    {"segmentId":"SECURITIES"},
    segment(equityBasis=""),
])
def test_broker_margin_facts_require_explicit_finite_contract(bad):
    with pytest.raises(PortfolioRiskError):
        assess_provider_margin_segments(
            observed_at=NOW, provider="IBKR", segments=[bad]
        )


def test_unattested_broker_timestamp_and_duplicate_segments_rejected():
    with pytest.raises(PortfolioRiskError, match="timezone"):
        assess_provider_margin_segments(
            observed_at=datetime(2026, 11, 7),
            provider="IBKR", segments=[segment()],
        )
    with pytest.raises(PortfolioRiskError, match="unique"):
        assess_provider_margin_segments(
            observed_at=NOW, provider="IBKR",
            segments=[segment(),segment()],
        )


def test_declared_liquidation_does_not_create_wealth_or_erase_debt():
    out = replay_declared_long_liquidation(**liquidation())
    assert out["beforeEquityUsd"] == "410.000000"
    assert out["afterEquityUsd"] == "377.000000"
    assert out["equityChangeUsd"] == "-33.000000"
    assert out["realizedExecutionPriceDifferenceUsd"] == "-30.000000"
    assert out["feesUsd"] == "3.000000"
    assert out["cashAfterUsd"] == "77.000000"
    assert out["loanAfterUsd"] == "400.000000"
    assert out["remainingQuantities"] == {"SPY":"7.000000"}
    assert out["beforeMaintenanceGapUsd"] == "-90.000000"
    assert out["afterMaintenanceGapUsd"] == "27.000000"
    assert out["beforeMaintenanceBreached"] is True
    assert out["afterMaintenanceBreached"] is False
    assert out["selfFinancingResidualUsd"] == "0"
    assert out["effectStanding"] == "READ_ONLY_NO_ORDERS_NO_PAPER_LEDGER"


def test_lender_paydown_at_same_mark_does_not_increase_equity():
    no_loan_paydown = liquidation(
        fills=[{
            "instrumentId":"SPY","sellQuantity":"3",
            "fillPriceUsd":"100","feeUsd":"0",
        }],
        loan_repayment_usd="0",
    )
    with_paydown = {**no_loan_paydown, "loan_repayment_usd":"250"}
    a = replay_declared_long_liquidation(**no_loan_paydown)
    b = replay_declared_long_liquidation(**with_paydown)
    assert a["beforeEquityUsd"] == b["beforeEquityUsd"]
    assert a["afterEquityUsd"] == b["afterEquityUsd"] == "410.000000"
    assert a["equityChangeUsd"] == "0.000000"
    assert b["loanAfterUsd"] == "350.000000"
    assert b["cashAfterUsd"] == "60.000000"


def test_liquidation_may_still_breach_and_leave_unpaid_negative_equity():
    out = replay_declared_long_liquidation(**liquidation(
        positions=[
            {"instrumentId":"IWM","quantity":"2","markPriceUsd":"100"}
        ],
        fills=[
            {"instrumentId":"IWM","sellQuantity":"2",
             "fillPriceUsd":"80","feeUsd":"5"}
        ],
        cash_before_usd="0",
        loan_before_usd="500",
        loan_repayment_usd="155",
        provider_maintenance_before_usd="100",
        provider_maintenance_after_usd="0",
    ))
    assert out["beforeEquityUsd"] == "-300.000000"
    assert out["afterEquityUsd"] == "-345.000000"
    assert out["remainingQuantities"]["IWM"] == "0.000000"
    assert out["loanAfterUsd"] == "345.000000"
    assert out["remainingUncoveredNetLiabilityUsd"] == "345.000000"
    assert out["afterMaintenanceBreached"] is True
    assert out["selfFinancingResidualUsd"] == "0"


def test_two_assets_multiple_fills_fee_and_slippage_are_exact():
    out = replay_declared_long_liquidation(**liquidation(
        positions=[
            {"instrumentId":"IWM","quantity":"2.5","markPriceUsd":"30"},
            {"instrumentId":"QQQ","quantity":"3.75","markPriceUsd":"20"},
        ],
        fills=[
            {"instrumentId":"IWM","sellQuantity":"1.25",
             "fillPriceUsd":"28","feeUsd":"0.4"},
            {"instrumentId":"QQQ","sellQuantity":"0.75",
             "fillPriceUsd":"19","feeUsd":"0.2"},
        ],
        cash_before_usd="10",
        loan_before_usd="40",
        loan_repayment_usd="20",
        provider_maintenance_before_usd="25",
        provider_maintenance_after_usd="22",
    ))
    assert out["beforeEquityUsd"] == "120.000000"
    assert out["equityChangeUsd"] == "-3.850000"
    assert out["afterEquityUsd"] == "116.150000"
    assert out["remainingQuantities"]["IWM"] == "1.250000"
    assert out["remainingQuantities"]["QQQ"] == "3.000000"
    assert out["selfFinancingResidualUsd"] == "0"


@pytest.mark.parametrize("changes", [
    {"loan_repayment_usd":"700"},
    {"loan_repayment_usd":"280"},
    {"cash_before_usd":"-1"},
    {"provider_maintenance_after_usd":"-1"},
    {"fills":[{"instrumentId":"SPY","sellQuantity":"11",
               "fillPriceUsd":"90","feeUsd":"0"}]},
    {"fills":[{"instrumentId":"MISSING","sellQuantity":"1",
               "fillPriceUsd":"90","feeUsd":"0"}]},
    {"fills":[{"instrumentId":"SPY","sellQuantity":"3",
               "fillPriceUsd":"0","feeUsd":"0"}]},
    {"fills":[{"instrumentId":"SPY","sellQuantity":"3",
               "fillPriceUsd":"90","feeUsd":"-0.1"}]},
    {"fills":[{"instrumentId":"SPY","sellQuantity":"2",
               "fillPriceUsd":"90","feeUsd":"0"},
              {"instrumentId":"SPY","sellQuantity":"9",
               "fillPriceUsd":"90","feeUsd":"0"}]},
])
def test_invalid_or_future_funded_liquidations_cannot_make_money(changes):
    with pytest.raises(PortfolioRiskError):
        replay_declared_long_liquidation(**liquidation(**changes))
