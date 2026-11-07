"""A read-only, cash-flow-matched passive benchmark replay.

This computes on caller-supplied period returns; it does not assert
market-data accuracy, tax compliance, investability, or execution rights.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal, Inexact, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

_ROW_FIELDS = frozenset({
    "periodEndAt", "depositAtStart", "strategyGrossReturn",
    "benchmarkGrossReturn", "strategyExpenseFractionAtStart",
    "benchmarkExpenseFractionAtStart", "strategyFixedFeeAtStart",
    "benchmarkFixedFeeAtStart",
})


class PassiveBenchmarkError(ValueError):
    """Invalid observation, asset flow or replay convention."""


def _amount(value: Any, label: str) -> Decimal:
    if type(value) is not str:
        raise PassiveBenchmarkError(f"{label}: expected decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise PassiveBenchmarkError(f"{label}: invalid decimal") from exc
    if not number.is_finite():
        raise PassiveBenchmarkError(f"{label}: non-finite decimal")
    return number


def _timestamp(value: Any) -> datetime:
    if type(value) is not str:
        raise PassiveBenchmarkError("periodEndAt: expected timestamp string")
    try:
        instant = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PassiveBenchmarkError("periodEndAt: invalid timestamp") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise PassiveBenchmarkError("periodEndAt: timezone required")
    return instant.astimezone(UTC)


def _add_cash_exact(left: Decimal, right: Decimal, path: str) -> Decimal:
    """Reject a representationally lost deposit; retain existing return precision.

    Decimal market returns remain intentionally context-rounded. External cash
    ledger additions instead must be representable in that same context.
    """
    with localcontext() as context:
        context.traps[Inexact] = True
        try:
            return left + right
        except Inexact as exc:
            raise PassiveBenchmarkError(
                f"{path}: cash flow would be silently rounded at current precision"
            ) from exc


def _next_value(
    *,
    capital: Decimal,
    deposit: Decimal,
    gross_return: Decimal,
    expense: Decimal,
    fixed_fee: Decimal,
    path: str,
) -> Decimal:
    if gross_return < -1:
        raise PassiveBenchmarkError(f"{path}: gross simple return below -100%")
    if not 0 <= expense <= 1:
        raise PassiveBenchmarkError(f"{path}: expense fraction outside [0,1]")
    if fixed_fee < 0:
        raise PassiveBenchmarkError(f"{path}: negative fixed fee")
    start = _add_cash_exact(capital, deposit, path)
    after_fees = start * (1 - expense) - fixed_fee
    if after_fees < 0:
        raise PassiveBenchmarkError(f"{path}: fees exceed available capital")
    return after_fees * (1 + gross_return)


def replay_passive_benchmark(
    *,
    opening_balance: str,
    currency: str,
    periods: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Replay two investment paths with exactly matched start-of-period deposits.

    All returns and costs are caller-provided; the comparison contains no
    extrapolation, live account state, trade intent or broker connectivity.
    """
    if type(currency) is not str or len(currency) != 3 or not currency.isascii() or not currency.isupper() or not currency.isalpha():
        raise PassiveBenchmarkError("currency must be ISO-style three-letter uppercase")
    opening = _amount(opening_balance, "opening_balance")
    if opening < 0:
        raise PassiveBenchmarkError("opening_balance must be nonnegative")
    if type(periods) not in (list, tuple) or not periods:
        raise PassiveBenchmarkError("periods must be a nonempty ordered sequence")
    strategy = benchmark = opening
    contributed = opening
    last_end: datetime | None = None
    for i, raw in enumerate(periods):
        if type(raw) is not dict or set(raw) != _ROW_FIELDS:
            raise PassiveBenchmarkError(f"periods[{i}]: invalid field set")
        end = _timestamp(raw["periodEndAt"])
        if last_end is not None and end <= last_end:
            raise PassiveBenchmarkError("periods must be strictly ordered and unique")
        last_end = end
        deposit = _amount(raw["depositAtStart"], "depositAtStart")
        if deposit < 0:
            raise PassiveBenchmarkError("deposits cannot be negative")
        strategy_return = _amount(raw["strategyGrossReturn"], "strategyGrossReturn")
        benchmark_return = _amount(raw["benchmarkGrossReturn"], "benchmarkGrossReturn")
        strategy_expense = _amount(
            raw["strategyExpenseFractionAtStart"], "strategyExpenseFractionAtStart"
        )
        benchmark_expense = _amount(
            raw["benchmarkExpenseFractionAtStart"], "benchmarkExpenseFractionAtStart"
        )
        strategy_fee = _amount(raw["strategyFixedFeeAtStart"], "strategyFixedFeeAtStart")
        benchmark_fee = _amount(raw["benchmarkFixedFeeAtStart"], "benchmarkFixedFeeAtStart")
        strategy = _next_value(
            capital=strategy, deposit=deposit, gross_return=strategy_return,
            expense=strategy_expense, fixed_fee=strategy_fee, path="strategy",
        )
        benchmark = _next_value(
            capital=benchmark, deposit=deposit, gross_return=benchmark_return,
            expense=benchmark_expense, fixed_fee=benchmark_fee, path="benchmark",
        )
        contributed = _add_cash_exact(contributed, deposit, "contributed")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.finance.cashflow-matched-passive-benchmark",
        "standing": "DESCRIPTIVE_REPLAY_NO_MARKET_VALIDATION",
        "capitalAuthority": "NONE",
        "currency": currency,
        "periodCount": len(periods),
        "contributedCapital": format(contributed, "f"),
        "strategyTerminalWealth": format(strategy, "f"),
        "benchmarkTerminalWealth": format(benchmark, "f"),
        "strategyNetGainVsContributions": format(strategy - contributed, "f"),
        "benchmarkNetGainVsContributions": format(benchmark - contributed, "f"),
        "terminalWealthDifference": format(strategy - benchmark, "f"),
        "cashFlowConvention": "MATCHED_DEPOSIT_AT_PERIOD_START",
        "feeConvention": "FRACTION_AND_FIXED_COST_AT_START_BEFORE_RETURN",
        "notEvaluated": [
            "Market-data provenance, total-return reconstruction and investability",
            "Realized tax/transaction execution, inflation and foreign-exchange conversion",
            "Time-weighted or money-weighted return and drawdown",
            "Independent strategy verification and capital authorization",
        ],
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise PassiveBenchmarkError("duplicate JSON key")
        output[key] = value
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Finance passive benchmark replay")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        if type(data) is not dict or set(data) != {
            "schemaVersion", "kind", "openingBalance", "currency", "periods",
        }:
            raise PassiveBenchmarkError("input: invalid root fields")
        if type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1:
            raise PassiveBenchmarkError("input: invalid schemaVersion")
        if data["kind"] != "ordivon.capital.finance.passive-benchmark-input":
            raise PassiveBenchmarkError("input: unsupported kind")
        out = replay_passive_benchmark(
            opening_balance=data["openingBalance"],
            currency=data["currency"],
            periods=data["periods"],
        )
    except (PassiveBenchmarkError, ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({
            "standing": "REJECTED", "capitalAuthority": "NONE",
            "reason": str(exc) if isinstance(exc, (PassiveBenchmarkError, ValueError)) else "input unreadable",
        }, sort_keys=True))
        return 2
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
