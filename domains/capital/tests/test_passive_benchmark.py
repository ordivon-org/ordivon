"""Test exact cash-flow comparison, not simulated investment alpha."""

import json
import subprocess
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from random import Random

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


def test_unrepresentable_deposit_is_rejected_not_silently_lost():
    """A 1-unit cashflow may not disappear beside a 29-digit balance."""
    row = sample_row()
    row.update(
        depositAtStart="1",
        strategyGrossReturn="0",
        benchmarkGrossReturn="0",
    )
    with pytest.raises(PassiveBenchmarkError, match="cash contribution exceeds valuation rounding budget"):
        evaluate([row], opening="10000000000000000000000000000")


def _independent_context_oracle(opening: str, rows: list[dict[str, str]]) -> dict[str, Decimal]:
    """Operational reference using explicit Python Decimal Context methods.

    This is a differential *implementation witness*, not a symbolic proof.
    It deliberately reproduces bounded 28-digit market-return rounding while
    keeping the full external deposit ledger visible to the caller.
    """
    context = Context(prec=28, rounding=ROUND_HALF_EVEN)
    opening_value = Decimal(opening)
    balances = [opening_value, opening_value]
    contributed = opening_value
    for row in rows:
        deposit = Decimal(row["depositAtStart"])
        contributed = context.add(contributed, deposit)
        for index, prefix in enumerate(("strategy", "benchmark")):
            gross = Decimal(row[f"{prefix}GrossReturn"])
            expense = Decimal(row[f"{prefix}ExpenseFractionAtStart"])
            fee = Decimal(row[f"{prefix}FixedFeeAtStart"])
            start = context.add(balances[index], deposit)
            after_expense = context.multiply(start, context.subtract(Decimal(1), expense))
            after_fee = context.subtract(after_expense, fee)
            balances[index] = context.multiply(after_fee, context.add(Decimal(1), gross))
    return {
        "contributedCapital": contributed,
        "strategyTerminalWealth": balances[0],
        "benchmarkTerminalWealth": balances[1],
        "strategyNetGainVsContributions": context.subtract(balances[0], contributed),
        "benchmarkNetGainVsContributions": context.subtract(balances[1], contributed),
        "terminalWealthDifference": context.subtract(balances[0], balances[1]),
    }


def test_arbitrary_finite_period_lengths_match_independent_decimal_context_oracle():
    """Real bounded operational refinement evidence for 1..120 periods.

    Deterministic differential corpus includes losses, gains, zero deposits,
    fractional expenses and fixed fees on both independent paths. The Lean
    proof covers arbitrary finite lengths of the *exact Rational* model;
    these observations bind the actual Python semantics to a second oracle.
    """
    random = Random(20261107)
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
        for count in (1, 2, 3, 7, 31, 120):
            for _case in range(16):
                opening = str(random.randrange(10000, 20001))
                rows = []
                for i in range(count):
                    day = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=i)
                    rows.append({
                        "periodEndAt": day.isoformat(),
                        "depositAtStart": str(Decimal(random.randrange(0, 3000)) / 100),
                        "strategyGrossReturn": str(Decimal(random.randrange(-70, 91)) / 1000),
                        "benchmarkGrossReturn": str(Decimal(random.randrange(-60, 81)) / 1000),
                        "strategyExpenseFractionAtStart": str(Decimal(random.randrange(0, 11)) / 10000),
                        "benchmarkExpenseFractionAtStart": str(Decimal(random.randrange(0, 11)) / 10000),
                        "strategyFixedFeeAtStart": str(Decimal(random.randrange(0, 20)) / 100),
                        "benchmarkFixedFeeAtStart": str(Decimal(random.randrange(0, 20)) / 100),
                    })
                observed = evaluate(rows, opening=opening)
                reference = _independent_context_oracle(opening, rows)
                for key, expected in reference.items():
                    assert Decimal(observed[key]) == expected, (count, key)
                assert observed["periodCount"] == count
                assert observed["standing"] == "DESCRIPTIVE_REPLAY_NO_MARKET_VALIDATION"
                assert observed["capitalAuthority"] == "NONE"


def test_arbitrarily_long_zero_return_paths_preserve_exact_external_cash():
    """Zero fees and zero returns cannot reclassify deposits as profit."""
    rows = []
    for day in range(250):
        row = sample_row()
        row.update({
            "periodEndAt": (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day)).isoformat(),
            "depositAtStart": "0.01" if day % 3 else "100.25",
            "strategyGrossReturn": "0",
            "benchmarkGrossReturn": "0",
        })
        rows.append(row)
    observed = evaluate(rows, opening="12345.67")
    assert Decimal(observed["contributedCapital"]) == Decimal("12345.67") + sum(
        (Decimal(row["depositAtStart"]) for row in rows), Decimal(0)
    )
    assert Decimal(observed["strategyTerminalWealth"]) == Decimal(observed["contributedCapital"])
    assert Decimal(observed["benchmarkTerminalWealth"]) == Decimal(observed["contributedCapital"])
    assert Decimal(observed["strategyNetGainVsContributions"]) == 0
    assert Decimal(observed["benchmarkNetGainVsContributions"]) == 0
    assert Decimal(observed["terminalWealthDifference"]) == 0


def test_extreme_finite_decimal_return_fails_closed_with_typed_rejection(tmp_path):
    """A syntactically finite 1e999999 return must not leak Decimal.Overflow."""
    row = sample_row()
    row.update(strategyGrossReturn="1e999999", depositAtStart="0")
    with pytest.raises(PassiveBenchmarkError, match="arithmetic outside supported Decimal context"):
        evaluate([row])
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.finance.passive-benchmark-input",
        "openingBalance": "100",
        "currency": "USD",
        "periods": [row],
    }
    path = tmp_path / "overflow-admission.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cli = subprocess.run(
        [str(Path(__file__).resolve().parents[1] / "scripts/run-capability-python"),
         "-m", "ordivon_capital.portfolio.passive_benchmark", "--input", str(path)],
        text=True, capture_output=True, check=False, timeout=90,
    )
    assert cli.returncode == 2
    assert json.loads(cli.stdout)["standing"] == "REJECTED"
    assert "Traceback" not in cli.stderr


def test_disabled_decimal_overflow_trap_cannot_create_nonfinite_public_valuation():
    """Caller-specific context controls cannot smuggle Infinity into receipts."""
    from decimal import Overflow

    row = sample_row()
    row.update(strategyGrossReturn="1e999999", depositAtStart="0")
    context = Context(prec=28, rounding=ROUND_HALF_EVEN)
    context.traps[Overflow] = False
    with localcontext(context), pytest.raises(PassiveBenchmarkError, match="non-finite"):
        evaluate([row])
