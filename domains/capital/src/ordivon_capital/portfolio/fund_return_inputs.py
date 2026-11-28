"""Normalize explicitly declared fund-NAV returns to the existing cashflow model.

This is a semantic adapter, not a data provider, total-return constructor,
trade simulator, or second wealth engine.
"""

from __future__ import annotations

from datetime import date
from typing import Any

NAV_BASIS = "FUND_NAV_TOTAL_RETURN_NET_OF_FUND_EXPENSES"
_ROOT_FIELDS = {"schemaVersion", "kind", "openingBalance", "currency", "periods"}
_PERIOD_FIELDS = {
    "depositAtStart", "strategy", "benchmark",
    "strategyExternalExpenseFractionAtStart", "benchmarkExternalExpenseFractionAtStart",
    "strategyExternalFixedFeeAtStart", "benchmarkExternalFixedFeeAtStart",
}
_OBSERVATION_FIELDS = {
    "instrument", "currency", "returnBasis", "periodStartDate", "periodEndDate",
    "totalReturn", "sourceRef",
}


def _date(value: Any) -> date:
    if type(value) is not str:
        raise ValueError("fund return date must be YYYY-MM-DD")
    result = date.fromisoformat(value)
    if result.isoformat() != value:
        raise ValueError("fund return date must be canonical YYYY-MM-DD")
    return result


def _observation(raw: Any) -> tuple[date, date, str]:
    if type(raw) is not dict or set(raw) != _OBSERVATION_FIELDS:
        raise ValueError("invalid fund return observation fields")
    if raw["currency"] != "USD" or raw["returnBasis"] != NAV_BASIS:
        raise ValueError("both legs require USD fund NAV total return net of fund expenses")
    for field in ("instrument", "sourceRef"):
        if type(raw[field]) is not str or not raw[field].strip():
            raise ValueError(f"fund return requires nonblank {field}")
    start = _date(raw["periodStartDate"])
    end = _date(raw["periodEndDate"])
    if start >= end:
        raise ValueError("fund return period must have positive duration")
    return start, end, raw["instrument"]


def normalize_fund_return_request(
    request: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Ensure both legs describe identical contiguous periods and return basis.

    Only explicitly named external investor costs may enter the existing
    transition model. Caller claims about origin/semantics remain unattested.
    """
    if type(request) is not dict or set(request) != _ROOT_FIELDS:
        raise ValueError("invalid fund-return request fields")
    if type(request["schemaVersion"]) is not int or request["schemaVersion"] != 2:
        raise ValueError("fund return schemaVersion must be 2")
    if request["kind"] != "ordivon.capital.finance.passive-benchmark-input":
        raise ValueError("unexpected fund-return request kind")
    if request["currency"] != "USD":
        raise ValueError("fund return comparison currently supports USD only")
    periods = request["periods"]
    if type(periods) is not list or not periods:
        raise ValueError("fund return comparison requires ordered periods")
    normalized = []
    evidence = []
    previous_end = None
    previous_instruments = None
    for row in periods:
        if type(row) is not dict or set(row) != _PERIOD_FIELDS:
            raise ValueError("invalid fund-return period fields; only external costs allowed")
        strategy, benchmark = row["strategy"], row["benchmark"]
        s_start, s_end, s_id = _observation(strategy)
        b_start, b_end, b_id = _observation(benchmark)
        if (s_start, s_end) != (b_start, b_end):
            raise ValueError("fund return legs must cover the same period")
        if previous_end is not None and s_start != previous_end:
            raise ValueError("fund return periods must be contiguous without gaps or overlap")
        if previous_instruments is not None and (s_id, b_id) != previous_instruments:
            raise ValueError("fund identities must not change within a comparison")
        previous_end = s_end
        previous_instruments = (s_id, b_id)
        normalized.append({
            # This instant is an internal ordering key, NOT publication time.
            "periodEndAt": s_end.isoformat() + "T00:00:00+00:00",
            "depositAtStart": row["depositAtStart"],
            "strategyGrossReturn": strategy["totalReturn"],
            "benchmarkGrossReturn": benchmark["totalReturn"],
            "strategyExpenseFractionAtStart": row["strategyExternalExpenseFractionAtStart"],
            "benchmarkExpenseFractionAtStart": row["benchmarkExternalExpenseFractionAtStart"],
            "strategyFixedFeeAtStart": row["strategyExternalFixedFeeAtStart"],
            "benchmarkFixedFeeAtStart": row["benchmarkExternalFixedFeeAtStart"],
        })
        evidence.append({"strategy": dict(strategy), "benchmark": dict(benchmark)})
    return normalized, evidence
