"""Test exact cash-flow comparison, not simulated investment alpha."""

import json
import subprocess
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from ordivon_capital.portfolio.passive_benchmark import (
    PassiveBenchmarkError,
    replay_passive_benchmark,
)


def sample_row():
    return {
        "periodEndAt": "2026-11-02T00:00:00+00:00",
        "depositAtStart": "50",
        "strategyGrossReturn": "0.10",
        "benchmarkGrossReturn": "0",
        "strategyExpenseFractionAtStart": "0",
        "benchmarkExpenseFractionAtStart": "0",
        "strategyFixedFeeAtStart": "0",
        "benchmarkFixedFeeAtStart": "0",
    }


def evaluate(rows=None, opening="100", currency="USD"):
    return replay_passive_benchmark(
        opening_balance=opening,
        currency=currency,
        periods=[sample_row()] if rows is None else rows,
    )


def d(out, name):
    return Decimal(out[name])


def test_two_period_equal_deposits_are_matched_but_not_counted_as_alpha():
    first = sample_row()
    second = sample_row()
    second["periodEndAt"] = "2026-11-03T00:00:00+00:00"
    result = evaluate([first, second])
    assert result == evaluate([first, second])
    assert result["capitalAuthority"] == "NONE"
    assert result["standing"] == "DESCRIPTIVE_REPLAY_NO_MARKET_VALIDATION"
    assert result["periodCount"] == 2
    assert d(result, "contributedCapital") == 200
    assert d(result, "strategyTerminalWealth") == Decimal("236.5")
    assert d(result, "benchmarkTerminalWealth") == Decimal("200")
    assert d(result, "terminalWealthDifference") == Decimal("36.5")
    assert d(result, "strategyNetGainVsContributions") == Decimal("36.5")


def test_identical_paths_have_zero_relative_terminal_wealth():
    first = sample_row()
    first.update({
        "strategyGrossReturn": "0.08",
        "benchmarkGrossReturn": "0.08",
        "strategyExpenseFractionAtStart": "0.005",
        "benchmarkExpenseFractionAtStart": "0.005",
        "strategyFixedFeeAtStart": "1",
        "benchmarkFixedFeeAtStart": "1",
    })
    result = evaluate([first])
    assert d(result, "terminalWealthDifference") == 0


def test_costs_are_charged_before_return_not_after():
    row = sample_row()
    row.update({
        "depositAtStart": "0",
        "strategyExpenseFractionAtStart": "0.01",
        "strategyFixedFeeAtStart": "1",
        "benchmarkGrossReturn": "0.10",
    })
    out = evaluate([row])
    assert d(out, "strategyTerminalWealth") == Decimal("107.8")
    assert d(out, "benchmarkTerminalWealth") == Decimal("110")
    assert d(out, "terminalWealthDifference") == Decimal("-2.2")


def test_100_percent_loss_and_subsequent_contribution():
    first = sample_row()
    first.update({"strategyGrossReturn": "-1", "benchmarkGrossReturn": "-1"})
    second = sample_row()
    second["periodEndAt"] = "2026-11-03T00:00:00+00:00"
    second["strategyGrossReturn"] = "0"
    out = evaluate([first, second])
    assert d(out, "strategyTerminalWealth") == 50
    assert d(out, "benchmarkTerminalWealth") == 50
    assert d(out, "contributedCapital") == 200


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("depositAtStart", "-0.01"),
        ("depositAtStart", "NaN"),
        ("depositAtStart", 50),
        ("strategyGrossReturn", "-1.01"),
        ("strategyGrossReturn", float("inf")),
        ("benchmarkGrossReturn", "-1.1"),
        ("strategyExpenseFractionAtStart", "1.01"),
        ("strategyExpenseFractionAtStart", "-0.01"),
        ("strategyFixedFeeAtStart", "-1"),
        ("strategyFixedFeeAtStart", "1000"),
        ("benchmarkFixedFeeAtStart", "1000"),
        ("periodEndAt", "2026-11-02T00:00:00"),
        ("periodEndAt", "not-a-time"),
        ("unexpectedPermission", "allow"),
    ],
)
def test_bad_period_never_produces_a_comparison(field, value):
    row = sample_row()
    row[field] = value
    with pytest.raises(PassiveBenchmarkError):
        evaluate([row])


def test_invalid_sequence_order_and_missing_period_are_rejected():
    row = sample_row()
    row2 = deepcopy(row)
    for rows in ([row, row2], [], {}, [row2, row]):
        with pytest.raises(PassiveBenchmarkError):
            evaluate(rows)


@pytest.mark.parametrize("opening", ["-1", "NaN", 10, "Infinity"])
def test_invalid_initial_capital(opening):
    with pytest.raises(PassiveBenchmarkError):
        evaluate(opening=opening)


@pytest.mark.parametrize("currency", ["usd", "USDT", "U$D", "", 42])
def test_invalid_currency(currency):
    with pytest.raises(PassiveBenchmarkError):
        evaluate(currency=currency)


def test_partial_wealth_comparison_does_not_report_annualized_or_drawdown():
    out = evaluate()
    assert "maxDrawdown" not in out
    assert any("drawdown" in x for x in out["notEvaluated"])
    assert "annualizedReturn" not in out
    assert out["capitalAuthority"] == "NONE"


def test_native_cli_observes_matched_contributions_and_net_gain_identity(tmp_path):
    """One real module/JSON consumer witness; not an arbitrary-period proof."""
    first = sample_row()
    first.update(
        strategyExpenseFractionAtStart="0.01",
        strategyFixedFeeAtStart="1",
        benchmarkGrossReturn="0.02",
    )
    second = sample_row()
    second.update(
        periodEndAt="2026-11-03T00:00:00+00:00",
        depositAtStart="25",
        strategyGrossReturn="-0.03",
        benchmarkGrossReturn="-0.02",
        benchmarkFixedFeeAtStart="2",
    )
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.finance.passive-benchmark-input",
        "openingBalance": "100",
        "currency": "USD",
        "periods": [first, second],
    }
    source = tmp_path / "benchmark-consumer.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        [str(Path(__file__).resolve().parents[1] / "scripts/run-capability-python"),
         "-m", "ordivon_capital.portfolio.passive_benchmark",
         "--input", str(source)],
        text=True, capture_output=True, check=False, timeout=90,
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed["capitalAuthority"] == "NONE"
    assert observed["standing"] == "DESCRIPTIVE_REPLAY_NO_MARKET_VALIDATION"
    assert observed["contributedCapital"] == "175"
    assert Decimal(observed["terminalWealthDifference"]) == (
        Decimal(observed["strategyNetGainVsContributions"])
        - Decimal(observed["benchmarkNetGainVsContributions"])
    )
    assert observed == replay_passive_benchmark(
        opening_balance="100", currency="USD", periods=[first, second]
    )
