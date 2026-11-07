"""Pure 1r model: static boundary, causality, ledger identity, fail-closed data."""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path

import pytest

from ordivon_capital.research.unit_r_dca import (
    Assumptions,
    Bar,
    UnitRModelError,
    exposure_from_stress,
    load_adjusted_bars,
    observed_max_drawdown,
    replay_unit_r,
    stress_estimate,
)


def series(values: list[float]) -> list[Bar]:
    return [Bar(date(2020, 1, 1) + timedelta(days=i), p, p) for i, p in enumerate(values)]


def test_exact_static_margin_bound_and_cash_allocation() -> None:
    for m in (.25, .30, .40, .50):
        for d in (.20, .40, .60, .90):
            cap = 1 / (m + (1 - m) * d)
            w = exposure_from_stress(
                shock=d, maintenance=m, initial_margin=.50, headroom_use=1
            )
            assert w == pytest.approx(min(2, cap))
            assert 1 - w * (m + (1 - m) * d) >= -1e-12
    low = exposure_from_stress(
        shock=.60, maintenance=.40, initial_margin=.5,
        headroom_use=.8, risk_budget=.25,
    )
    assert low == pytest.approx(.25 / .60)
    assert low < 1  # keep residual in cash instead of borrowing


def test_stress_uses_only_previous_days() -> None:
    history = series([1 + i * .001 for i in range(801)])
    changed = history.copy()
    changed[756] = Bar(history[756].session, .01, .01)
    assert stress_estimate(history, 756, Assumptions()) == stress_estimate(
        changed, 756, Assumptions()
    )
    assert observed_max_drawdown([100, 120, 80]) == pytest.approx(1 / 3)
    with pytest.raises(UnitRModelError, match="strictly previous"):
        stress_estimate(history, 755, Assumptions())


def test_monthly_one_r_flat_prices_have_zero_investment_return() -> None:
    rows = series([1.0] * 850)
    result = replay_unit_r(
        rows, start=rows[756].session, policy="unlevered",
        assumptions=Assumptions(turnover_cost=0, borrow_annual=0),
    )
    assert result["status"] == "COMPLETED"
    assert result["months"] >= 3
    assert result["paidInR"] == result["terminalR"]
    assert result["netGainR"] == pytest.approx(0)
    assert result["flowAdjustedUnitMaxDrawdownPct"] == pytest.approx(0)
    assert result["xirrAnnualPct"] == pytest.approx(0)


def test_intraday_margin_breach_precedes_future_contribution() -> None:
    prices = [1.0] * 758
    prices[757] = .2
    rows = series(prices)
    result = replay_unit_r(
        rows, start=rows[756].session, policy="margin_cap",
        assumptions=Assumptions(turnover_cost=0),
    )
    assert result["status"] == "MARGIN_BREACH"
    assert result["paidInR"] == 1
    assert result["terminalR"] is None


def test_frozen_csv_hash_rejects_tampering(tmp_path: Path) -> None:
    p = tmp_path / "daily.csv"
    data = "date,close,low,adj_close\n"
    data += "".join(
        f"{(date(2020, 1, 1) + timedelta(days=i)).isoformat()},100,90,100\n"
        for i in range(805)
    )
    p.write_text(data)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    assert len(load_adjusted_bars(p, digest)) == 805
    p.write_text(data.replace(",100,90,100\n", ",101,90,101\n", 1))
    with pytest.raises(UnitRModelError, match="sha256 mismatch"):
        load_adjusted_bars(p, digest)


def test_invalid_math_fail_closed() -> None:
    with pytest.raises(UnitRModelError):
        Assumptions(stress_maintenance=1.1)
    with pytest.raises(UnitRModelError):
        exposure_from_stress(
            shock=float("nan"), maintenance=.4,
            initial_margin=.5, headroom_use=.8
        )
    with pytest.raises(UnitRModelError):
        observed_max_drawdown([1.0, 0.0, 2.0])

def test_crisis_memory_retains_old_tail_loss_without_future_data() -> None:
    # A crash outside the last 756 bars must still constrain lifetime-memory
    # risk sizing. The ETF's *past* is known even when another ETF did not
    # exist at the date of that crash.
    prices = [1.0] * 1600
    prices[100] = 0.15
    rows = series(prices)
    cut = rows[1500].session
    assumptions = Assumptions(turnover_cost=0, borrow_annual=0)
    rolling = replay_unit_r(
        rows, start=cut, policy="risk_budget", assumptions=assumptions,
        account_drawdown_budget=.4,
    )
    memory = replay_unit_r(
        rows, start=cut, policy="crisis_memory", assumptions=assumptions,
        account_drawdown_budget=.4,
    )
    assert rolling["status"] == memory["status"] == "COMPLETED"
    assert memory["averageExposure"] < rolling["averageExposure"]
    assert memory["largestPriorKnownStressPct"] >= 90.0
    assert memory["maximumExposure"] < 0.50
