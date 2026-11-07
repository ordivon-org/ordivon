"""Research-only 1r monthly ETF exposure and drawdown-bound experiments.

Uses Capital Risk's canonical historical expected-shortfall operator. This is
an immutable historical replay, NOT a broker, execution, or Paper ledger owner.
Prices are adjusted synthetic total-return units, not executable fill quotes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from ordivon_capital.risk.tail_risk import historical_expected_shortfall


class UnitRModelError(ValueError):
    """The historical experiment has insufficient or invalid evidence."""


@dataclass(frozen=True)
class Bar:
    session: date
    adjusted_close: float
    adjusted_low: float


@dataclass(frozen=True)
class Assumptions:
    borrow_annual: float = 0.07
    turnover_cost: float = 0.001
    maintenance: float = 0.40
    stress_maintenance: float = 0.45
    max_initial_leverage: float = 2.0
    initial_margin: float = 0.50
    past_sessions: int = 756
    shock_floor: float = 0.35
    drawdown_buffer: float = 0.10
    tail_es_multiplier: float = 1.25
    margin_headroom_use: float = 0.80

    def __post_init__(self) -> None:
        if not (
            0 <= self.borrow_annual <= 1
            and 0 <= self.turnover_cost < 0.05
            and 0 < self.maintenance < 1
            and 0 < self.stress_maintenance < 1
            and 1 <= self.max_initial_leverage <= 1 / self.initial_margin
            and 0 < self.initial_margin < 1
            and self.past_sessions >= 100
            and 0 < self.shock_floor < 1
            and 0 <= self.drawdown_buffer < 1
            and 1 <= self.tail_es_multiplier <= 10
            and 0 < self.margin_headroom_use <= 1
        ):
            raise UnitRModelError("invalid margin, loss, or financing assumptions")


def observed_max_drawdown(values: list[float]) -> float:
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise UnitRModelError("positive finite historical prices required")
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        worst = max(worst, 1 - value / peak)
    return worst


def exposure_from_stress(
    *,
    shock: float,
    maintenance: float,
    initial_margin: float,
    headroom_use: float,
    risk_budget: float | None = None,
    cushion: float | None = None,
) -> float:
    """Exact static margin boundary, with separate peak-cushion constraint."""
    if not (
        0 < shock < 1
        and 0 < maintenance < 1
        and 0 < initial_margin <= 1
        and 0 < headroom_use <= 1
    ):
        raise UnitRModelError("invalid risk boundary")
    margin_cap = 1 / (maintenance + (1 - maintenance) * shock)
    target = min(1 / initial_margin, 1 + headroom_use * (margin_cap - 1))
    if risk_budget is not None:
        if not 0 <= risk_budget <= 1:
            raise UnitRModelError("risk budget outside [0,1]")
        target = min(target, risk_budget / shock)
    if cushion is not None:
        if not 0 <= cushion <= 1:
            raise UnitRModelError("invalid remaining drawdown cushion")
        target = min(target, cushion / shock)
    return max(0.0, target)


def stress_estimate(
    bars: list[Bar], decision_index: int, assumptions: Assumptions
) -> dict[str, float]:
    """No-lookahead 3y peak drawdown and 21-session CVaR from prior closes."""
    previous = bars[max(0, decision_index - assumptions.past_sessions):decision_index]
    if len(previous) < assumptions.past_sessions:
        raise UnitRModelError("insufficient strictly previous training bars")
    values = [row.adjusted_close for row in previous]
    prior_drawdown = observed_max_drawdown(values)
    # 21-session overlapping returns are descriptive historical scenarios; ES
    # is NOT a confidence bound for a future 21-day loss.
    returns_21 = [values[i] / values[i - 21] - 1 for i in range(21, len(values))]
    es = historical_expected_shortfall(returns_21, confidence=0.975)
    es_21 = max(0.0, float(es["expectedShortfallLossFraction"]))
    shock = min(
        0.95,
        max(
            assumptions.shock_floor,
            prior_drawdown + assumptions.drawdown_buffer,
            assumptions.tail_es_multiplier * es_21,
        ),
    )
    return {
        "historicalDrawdown": prior_drawdown,
        "expectedShortfall21": es_21,
        "scenarioShock": shock,
    }


def load_adjusted_bars(csv_path: Path, expected_sha256: str) -> list[Bar]:
    raw = csv_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise UnitRModelError("frozen daily CSV sha256 mismatch")
    rows: list[Bar] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not {"date", "close", "low", "adj_close"}.issubset(reader.fieldnames or []):
            raise UnitRModelError("required daily OHLCV fields absent")
        for rec in reader:
            d = date.fromisoformat(rec["date"])
            raw_close = float(rec["close"])
            low = float(rec["low"])
            adjusted_close = float(rec["adj_close"])
            if not all(math.isfinite(v) and v > 0 for v in
                       (raw_close, low, adjusted_close)):
                raise UnitRModelError("nonfinite or nonpositive daily price")
            if low > raw_close * (1 + 1e-6):
                raise UnitRModelError("daily low exceeds close")
            if rows and not d > rows[-1].session:
                raise UnitRModelError("nonmonotonic/duplicate trading sessions")
            rows.append(Bar(d, adjusted_close, low * adjusted_close / raw_close))
    if len(rows) < 800:
        raise UnitRModelError("missing sufficient daily price history")
    return rows


def _xirr(deposits: list[date], terminal: float, end: date) -> float | None:
    """The unique cashflow-matched annual rate for deposits and final equity."""
    if terminal <= 0 or not deposits or end < deposits[-1]:
        return None
    from scipy.optimize import brentq

    first = deposits[0]
    years = [(d - first).days / 365.25 for d in deposits]
    remaining = (end - first).days / 365.25
    if remaining <= 0:
        return None

    def npv(rate: float) -> float:
        base = 1 + rate
        return terminal / base ** remaining - math.fsum(
            1 / base ** duration for duration in years
        )

    lo, hi = -0.95, 50.0
    if npv(lo) * npv(hi) > 0:
        return None
    return float(brentq(npv, lo, hi, xtol=1e-12))


def replay_unit_r(
    bars: list[Bar],
    *,
    start: date,
    policy: str,
    assumptions: Assumptions = Assumptions(),
    account_drawdown_budget: float = 0.40,
) -> dict[str, Any]:
    """One 1r/month historical experiment, with cash/debt and breach semantics.

    Rebalance decision uses ONLY prices strictly before the trade session.
    The same session's close is a simplifying execution assumption, never a
    claim that an actual market-on-close order would be filled at that price.
    """
    if policy not in ("unlevered", "margin_cap", "risk_budget", "peak_cushion"):
        raise UnitRModelError("unknown research-only policy")
    if not 0 <= account_drawdown_budget <= 1:
        raise UnitRModelError("invalid account risk budget")
    if not bars or any(bars[i].session >= bars[i + 1].session
                       for i in range(len(bars) - 1)):
        raise UnitRModelError("invalid bars")
    ix = next((i for i, b in enumerate(bars) if b.session >= start), None)
    if ix is None or ix < assumptions.past_sessions:
        raise UnitRModelError("evaluation start requires previous 756 daily bars")
    shares = 0.0
    cash = 0.0
    debt = 0.0
    before_cashflow_equity = 0.0
    last_post_equity: float | None = None
    last_date: date | None = None
    unit_nav = 1.0
    peak_nav = 1.0
    worst_dd = 0.0
    first_months: set[tuple[int, int]] = set()
    deposit_dates: list[date] = []
    avg_exposures: list[float] = []
    largest_shock = 0.0
    min_margin = 1.0
    under_floor_count = 0
    fee_sum = 0.0
    financing_sum = 0.0
    cppi_floor = lambda u, peak: (1 - account_drawdown_budget) * peak

    for i in range(ix, len(bars)):
        b = bars[i]
        days = (b.session - last_date).days if last_date else 0
        if debt:
            interest = debt * ((1 + assumptions.borrow_annual) ** (days / 365.25) - 1)
            debt += interest
            financing_sum += interest

        # The low occurs BEFORE the monthly close contribution or rebalance.
        if debt > 1e-10:
            gross_at_low = shares * b.adjusted_low
            ratio = (gross_at_low + cash - debt) / gross_at_low
            min_margin = min(min_margin, ratio)
            if ratio < assumptions.maintenance - 1e-12:
                return {
                    "status": "MARGIN_BREACH",
                    "session": b.session.isoformat(),
                    "maintenance": assumptions.maintenance,
                    "observedMarginAtDailyLow": round(ratio, 5),
                    "paidInR": len(deposit_dates),
                    "terminalR": None,
                    "modelLimit": "Synthetic adjusted-low proxy; actual broker liquidation not established.",
                }

        # Signals for today's closing auction must be fixed using information
        # observable by yesterday's close. Today's return is applied below
        # only for marking the existing position, NOT for sizing new risk.
        signal_unit_nav, signal_peak_nav = unit_nav, peak_nav
        current_equity = shares * b.adjusted_close + cash - debt
        if shares and current_equity <= 0:
            return {
                "status": "INSOLVENT", "session": b.session.isoformat(),
                "paidInR": len(deposit_dates), "terminalR": None,
            }
        if last_post_equity is not None:
            if last_post_equity <= 0:
                raise UnitRModelError("previous equity invalid")
            unit_nav *= current_equity / last_post_equity
            peak_nav = max(peak_nav, unit_nav)
            worst_dd = max(worst_dd, 1 - unit_nav / peak_nav)

        if unit_nav < cppi_floor(unit_nav, peak_nav) - 1e-12:
            under_floor_count += 1

        period_key = (b.session.year, b.session.month)
        if period_key not in first_months:
            first_months.add(period_key)
            deposit_dates.append(b.session)
            shock = stress_estimate(bars, i, assumptions)
            largest_shock = max(largest_shock, shock["scenarioShock"])
            if policy == "unlevered":
                target = 1.0
            else:
                # The regulator and house margin scenario can differ.
                basic = exposure_from_stress(
                    shock=shock["scenarioShock"],
                    maintenance=assumptions.stress_maintenance,
                    initial_margin=assumptions.initial_margin,
                    headroom_use=assumptions.margin_headroom_use,
                )
                if policy == "margin_cap":
                    target = min(1.5, basic)
                else:
                    cushion = None
                    if policy == "peak_cushion":
                        cushion = max(
                            0.0,
                            1 - cppi_floor(signal_unit_nav, signal_peak_nav)
                            / signal_unit_nav,
                        )
                    target = exposure_from_stress(
                        shock=shock["scenarioShock"],
                        maintenance=assumptions.stress_maintenance,
                        initial_margin=assumptions.initial_margin,
                        headroom_use=assumptions.margin_headroom_use,
                        risk_budget=account_drawdown_budget,
                        cushion=cushion,
                    )

            before_cashflow_equity = current_equity + 1.0
            prior_exposure = shares * b.adjusted_close
            f = assumptions.turnover_cost
            # Solve gross=target*(equity_before_trade - f*|gross-old_gross|)
            if target * before_cashflow_equity >= prior_exposure:
                exposure = target * (before_cashflow_equity + f * prior_exposure) / (
                    1 + target * f
                )
            else:
                exposure = target * (before_cashflow_equity - f * prior_exposure) / (
                    1 - target * f
                )
            paid = f * abs(exposure - prior_exposure)
            fee_sum += paid
            post_equity = before_cashflow_equity - paid
            if post_equity <= 0:
                raise UnitRModelError("trade fees exceed account equity")
            shares = exposure / b.adjusted_close
            if exposure > post_equity:
                debt, cash = exposure - post_equity, 0.0
            else:
                debt, cash = 0.0, post_equity - exposure
            if exposure and post_equity / exposure < assumptions.initial_margin - 1e-9:
                raise UnitRModelError("initial margin violated")
            if not math.isclose(
                shares * b.adjusted_close + cash - debt,
                post_equity, rel_tol=1e-10, abs_tol=1e-10,
            ):
                raise UnitRModelError("cash/debt/position conservation violated")
            avg_exposures.append(exposure / post_equity)
            # Trading costs are real investment losses, not external outflows.
            unit_nav *= post_equity / before_cashflow_equity
            peak_nav = max(peak_nav, unit_nav)
            worst_dd = max(worst_dd, 1 - unit_nav / peak_nav)
        else:
            post_equity = current_equity

        last_post_equity = post_equity
        last_date = b.session

    last = bars[-1]
    liquidation_fee = assumptions.turnover_cost * shares * last.adjusted_close
    fee_sum += liquidation_fee
    terminal = shares * last.adjusted_close + cash - debt - liquidation_fee
    total_paid = len(deposit_dates)
    irr = _xirr(deposit_dates, terminal, last.session)
    return {
        "status": "COMPLETED",
        "start": deposit_dates[0].isoformat(),
        "end": last.session.isoformat(),
        "months": total_paid,
        "paidInR": total_paid,
        "terminalR": round(terminal, 4),
        "netGainR": round(terminal - total_paid, 4),
        "xirrAnnualPct": round(irr * 100, 3) if irr is not None else None,
        "flowAdjustedUnitMaxDrawdownPct": round(worst_dd * 100, 3),
        "averageExposure": round(math.fsum(avg_exposures) / len(avg_exposures), 3),
        "minimumExposure": round(min(avg_exposures), 3),
        "maximumExposure": round(max(avg_exposures), 3),
        "largestPriorKnownStressPct": round(largest_shock * 100, 2),
        "minimumObservedMarginPct": round(min_margin * 100, 2),
        "closeBelowCushionFloorDays": under_floor_count,
        "borrowInterestR": round(financing_sum, 4),
        "totalTradingFeesR": round(fee_sum, 4),
    }


def run_study(
    data_dir: Path, *,
    starts: dict[str, date],
    assumptions: Assumptions = Assumptions(),
) -> dict[str, Any]:
    """No provider calls, no writes; verifies frozen CSV SHA before consumption."""
    manifest = json.loads((data_dir / "source_manifest.json").read_text())
    if manifest.get("dataStanding") != "SECONDARY_VENDOR_NOT_INDEPENDENTLY_ATTESTED":
        raise UnitRModelError("unexpected source standing")
    histories = {
        ticker: load_adjusted_bars(
            data_dir / "daily" / (ticker + ".csv"),
            manifest["symbols"][ticker]["csvSha256"],
        )
        for ticker in ("IWM", "SPY", "QQQ", "SMH", "DIA", "RSP")
    }
    # Compare all instruments on the intersection of actual trading sessions,
    # not filling absent daily observations with invented prices.
    intersection = set.intersection(*(set(bar.session for bar in history)
                                     for history in histories.values()))
    dates = sorted(intersection)
    aligned = {
        ticker: [bar for bar in history if bar.session in intersection]
        for ticker, history in histories.items()
    }
    for ticker in aligned:
        if len(aligned[ticker]) != len(dates):
            raise UnitRModelError("misaligned benchmark dates")
    result: dict[str, Any] = {
        "standing": "HISTORICAL_REPLAY_ONLY",
        "unit": "1r each calendar month, USD-numeraire-equivalent, no FX",
        "firstComparableBar": dates[0].isoformat(),
        "lastComparableBar": dates[-1].isoformat(),
        "comparableTradingDays": len(dates),
        "source": "Yahoo Finance secondary daily adjusted OHLCV",
        "modelAssumptions": vars(assumptions),
        "runs": {},
        "regimes": {},
    }
    for name, beginning in starts.items():
        variants: dict[str, Any] = {}
        for ticker, bars in aligned.items():
            variants[ticker] = {
                "unlevered": replay_unit_r(
                    bars, start=beginning, policy="unlevered", assumptions=assumptions
                ),
                "margin_cap": replay_unit_r(
                    bars, start=beginning, policy="margin_cap", assumptions=assumptions
                ),
                "risk_30pct": replay_unit_r(
                    bars, start=beginning, policy="risk_budget", assumptions=assumptions,
                    account_drawdown_budget=.30,
                ),
                "risk_40pct": replay_unit_r(
                    bars, start=beginning, policy="risk_budget", assumptions=assumptions,
                    account_drawdown_budget=.40,
                ),
                "peak_cushion_40pct": replay_unit_r(
                    bars, start=beginning, policy="peak_cushion", assumptions=assumptions,
                    account_drawdown_budget=.40,
                ),
            }
        result["runs"][name] = variants

    for name, lo, hi in (
        ("GFC_2007_2009", date(2007, 1, 1), date(2009, 12, 31)),
        ("COVID_2020", date(2020, 1, 1), date(2020, 12, 31)),
        ("TIGHTENING_2022", date(2022, 1, 1), date(2022, 12, 31)),
    ):
        by_ticker = {}
        for ticker, history in aligned.items():
            selected = [x.adjusted_close for x in history if lo <= x.session <= hi]
            by_ticker[ticker] = {
                "adjustedCloseMaxDrawdownPct": round(
                    observed_max_drawdown(selected) * 100, 2
                ),
                "bars": len(selected),
            }
        result["regimes"][name] = by_ticker
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="1r per-month long-range replay; read-only")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--borrow-annual", type=float, default=.07)
    parser.add_argument("--maintenance", type=float, default=.40)
    ns = parser.parse_args()
    result = run_study(
        ns.source_dir,
        starts={
            "2006-06": date(2006, 6, 1),
            "2007-10": date(2007, 10, 1),
            "2017-12": date(2017, 12, 1),
            "2021-11": date(2021, 11, 1),
        },
        assumptions=Assumptions(
            borrow_annual=ns.borrow_annual,
            maintenance=ns.maintenance,
        ),
    )
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "standing": result["standing"],
        "resultPath": str(ns.output),
        "commonDays": result["comparableTradingDays"],
        "start": result["firstComparableBar"],
        "end": result["lastComparableBar"],
        "variants": sum(len(v) for v in result["runs"].values()) * 5,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
