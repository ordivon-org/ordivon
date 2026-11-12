"""Existing Finance passive-benchmark consumer over the real Qlib OOS test sessions.

Test-only economic thought experiment. Legacy H1 forecasts next open->close;
new opt-in H5/H20 can forecast entry next OPEN->exit later OPEN, matching
the fixed native holding exit event, NOT its actual orders or fill prices.
Legacy intraday switching is NOT executable by the current Paper state
machine. No order authority, actual orders, or PG write is created here.
Historical Cboe prices were captured AFTER these test dates: NOT PIT.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

# Economic evaluation uses assert-heavy experimental invariants.
# Never claim a successful test when optimized Python strips them.
if sys.flags.optimize:
    raise RuntimeError("Finance R3 research acceptance requires non-optimized Python")

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / "src"))
from ordivon_capital.portfolio.passive_benchmark import replay_passive_benchmark
from ordivon_capital.portfolio.strategic_contribution import plan_strategic_contribution

OUT = Path(os.environ.get("ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR", str(ROOT / "output"))).resolve()
SYMBOLS = ("IWM", "QQQ", "SPY")
ZERO = "0"
OPENING = "1000"  # investment sleeve only; $9,000 remains protected cash



def run_multisession(report: dict, hold: int) -> dict:
    """Compare pre-fixed, disjoint H-session holdings using existing Portfolio.

    These are hypothetical fractional-share market-price proxies, not orders,
    authenticated historical execution, licensed source PIT, or validated alpha.
    """
    assert hold in (5, 20)
    skill = report["signal_quality"]
    assert skill["holding_sessions"] == hold
    assert skill["purged_overlapping_train_validation_labels"] is True
    assert skill["multi_session_holding_state_representable"] is True
    exit_price = skill.get("exit_price_kind", "close")
    assert exit_price in ("close", "next_open")
    if exit_price == "next_open":
        assert skill["label_forward_sessions"] == hold + 1
        assert skill["matches_native_fixed_holding_exit_event"] is True
    assert report["forecast"]["point_in_time_eligible"] is False
    assert report["portfolio_target"] is None

    allocation = plan_strategic_contribution({
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": "USD",
        "cashMinor": 1_000_000,
        "protectedReserveMinor": 900_000,
        "contributionMinor": 100_000,
        "holdingsMinor": {symbol: 0 for symbol in SYMBOLS},
        "targetWeightsBps": {"IWM": 0, "QQQ": 0, "SPY": 10_000},
    })
    assert allocation["allocationsMinor"]["SPY"] == 100_000
    assert allocation["executionAuthorized"] is False

    predictions = pd.read_csv(OUT / "qlib_test_predictions.csv").set_index(
        ["datetime", "instrument"]
    ).iloc[:, 0]
    labels = pd.read_parquet(OUT / "qlib_static_dataset.parquet")["label"]["LABEL0"]
    assert len(predictions) == skill["sample_rows"]
    bars = {
        sym: pd.read_csv(OUT / f"openbb_cboe_{sym}_normalized.csv")
        .set_index("session_date").sort_index()
        for sym in SYMBOLS
    }
    sessions = list(bars["SPY"].index)
    assert all(list(bars[sym].index) == sessions for sym in SYMBOLS)
    index_of = {day: i for i, day in enumerate(sessions)}
    all_decisions = sorted(set(predictions.index.get_level_values("datetime")))
    assert len(all_decisions) == skill["sample_sessions"]
    # The cadence is fixed solely by the declared holding horizon, never
    # selected by comparing observed model or baseline returns on this test.
    decisions = all_decisions[::hold]
    chosen = Counter()
    periods = []
    previous_exit = None
    for decision in decisions:
        idx = index_of[decision]
        entry = sessions[idx + 1]
        # Reuse the same Portfolio benchmark for the exit event that the
        # native strategy ACTUALLY trades. Consecutive OPEN windows may
        # share the boundary open; they never overlap in exposure time.
        exit_day = sessions[idx + hold + (exit_price == "next_open")]
        assert previous_exit is None or previous_exit <= entry
        previous_exit = exit_day
        predicted = {sym: float(predictions.loc[(decision, sym)]) for sym in SYMBOLS}
        assert all(math.isfinite(x) for x in predicted.values())
        # Score ranking, not realized returns, selects the next exposure.
        winner = min(SYMBOLS, key=lambda sym: (-predicted[sym], sym))
        chosen[winner] += 1
        observed = {}
        for sym in SYMBOLS:
            start_px = Decimal(str(bars[sym].loc[entry, "open"]))
            end_px = Decimal(str(bars[sym].loc[exit_day, "open" if exit_price == "next_open" else "close"]))
            ret = end_px / start_px - 1
            assert abs(float(ret) - float(labels.loc[(decision, sym)])) < 1e-10
            observed[sym] = ret
        periods.append({
            "decision": decision, "entry": entry, "exit": exit_day,
            "winner": winner, "model": observed[winner],
            "spy": observed["SPY"],
            "qqq": observed["QQQ"],
            "iwm": observed["IWM"],
            "equal": sum(observed.values(), Decimal(0)) / len(SYMBOLS),
        })

    def compare(reference: str, *, model_cost: str = "0",
                reference_cost: str = "0") -> dict:
        cashflows = [{
            "periodEndAt": row["exit"] + "T23:59:00+00:00",
            "depositAtStart": ZERO,
            "strategyGrossReturn": str(row["model"]),
            "benchmarkGrossReturn": str(row[reference]),
            "strategyExpenseFractionAtStart": model_cost,
            "benchmarkExpenseFractionAtStart": reference_cost,
            "strategyFixedFeeAtStart": ZERO,
            "benchmarkFixedFeeAtStart": ZERO,
        } for row in periods]
        ans = replay_passive_benchmark(
            opening_balance=OPENING, currency="USD", periods=cashflows
        )
        assert ans["capitalAuthority"] == "NONE"
        assert ans["periodCount"] == len(periods)
        return ans

    result = {
        "kind": "ordivon.finance.r3.qlib-disjoint-holding-economic-counterexample",
        "standing": "RETROSPECTIVE_NON_EXECUTABLE_HYPOTHETICAL_ONLY",
        "source_forecast_skill": skill,
        "holding_sessions": hold,
        "exit_price_kind": exit_price,
        "native_fixed_holding_economic_event_matched": exit_price == "next_open",
        "precommitted_selection_cadence": f"every_{hold}_test_decision_sessions",
        "disjoint_exposure_periods": len(periods),
        "nonoverlap_dates": [{
            "decision": p["decision"], "entry": p["entry"],
            "exit": p["exit"], "selected": p["winner"]
        } for p in periods],
        "chosen_assets": dict(sorted(chosen.items())),
        "distinct_assets_selected": len(chosen),
        "conditional_asset_rotation_observed": len(chosen) > 1,
        "benchmark_exposure": (
            "same_nonoverlapping_entry_open_exit_next_open_windows"
            if exit_price == "next_open"
            else "same_nonoverlapping_entry_open_exit_close_windows_flat_between_windows"
        ),
        "investment_sleeve_minor": 100_000,
        "protected_cash_minor": 900_000,
        "fractional_shares_assumed": True,
        "source_historical_PIT": False,
        "fully_executable_strategy_proven": False,
        "PortfolioIntent_admitted": False,
        "PG_or_broker_effects": "NONE",
        "actual_ohlcv_adjustments_and_fees_qualified": False,
        "model_vs_fixed_spy_zero_cost": compare("spy"),
        "model_vs_fixed_qqq_zero_cost": compare("qqq"),
        "model_vs_fixed_iwm_zero_cost": compare("iwm"),
        "model_vs_fixed_equal_zero_cost": compare("equal"),
        # Alternatives share the same declared entry/exit events, so the
        # identical illustrative cost convention is applied to BOTH.
        # Not continuous SPY buy-and-hold or measured transaction fees.
        "model_vs_spy_symmetric_10bps_per_period": compare(
            "spy", model_cost="0.001", reference_cost="0.001"
        ),
    }
    (OUT / "qlib_disjoint_holding_economic_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("R3_QLIB_DISJOINT_HOLDING_ECONOMIC_CONSUMER_PASS",
          json.dumps({
              "h": hold, "periods": len(periods),
              "selected": result["chosen_assets"],
              "model_minus_fixed_SPY": result["model_vs_fixed_spy_zero_cost"]["terminalWealthDifference"],
              "model_minus_equal": result["model_vs_fixed_equal_zero_cost"]["terminalWealthDifference"],
              "model_minus_fixed_IWM": result["model_vs_fixed_iwm_zero_cost"]["terminalWealthDifference"],
              "model_minus_fixed_QQQ": result["model_vs_fixed_qqq_zero_cost"]["terminalWealthDifference"],
              "distinct_assets_selected": result["distinct_assets_selected"],
              "symmetric_10bps_cost_minus_same_window_SPY": result[
                  "model_vs_spy_symmetric_10bps_per_period"
              ]["terminalWealthDifference"],
              "capital_authorized": False,
          }, sort_keys=True))
    return result

def run() -> dict:
    report = json.loads((OUT / "native_study_result.json").read_text(encoding="utf-8"))
    skill = report["signal_quality"]
    if skill.get("holding_sessions", 1) in (5, 20):
        return run_multisession(report, skill["holding_sessions"])
    assert skill["standing"] == "RETROSPECTIVE_BACKFILL_TEST_ONLY"
    assert skill["horizon"] == (
        "decision_after_T_close_entry_at_T_plus_1_open_exit_at_T_plus_1_close"
    )
    assert skill["outperforms_both_unconditional_baselines"] is False
    assert report["forecast"]["point_in_time_eligible"] is False
    assert report["forecast"]["paper_buy_and_hold_consumer_horizon_compatible"] is False
    assert report["portfolio_target"] is None

    # Existing Portfolio LEGO defines the capital envelope. The simulated
    # daily ETF-selection thought experiment does not acquire its authority.
    allocation = plan_strategic_contribution({
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": "USD",
        "cashMinor": 1_000_000,
        "protectedReserveMinor": 900_000,
        "contributionMinor": 100_000,
        "holdingsMinor": {sym: 0 for sym in SYMBOLS},
        "targetWeightsBps": {"IWM": 0, "QQQ": 0, "SPY": 10_000},
    })
    assert allocation["allocationsMinor"]["SPY"] == 100_000
    assert allocation["protectedReserveMinor"] == 900_000
    assert allocation["executionAuthorized"] is False
    predictions = pd.read_csv(OUT / "qlib_test_predictions.csv").set_index(
        ["datetime", "instrument"]
    ).iloc[:, 0]
    dataset = pd.read_parquet(OUT / "qlib_static_dataset.parquet")
    labels = dataset["label"]["LABEL0"]
    assert predictions.index.is_unique and labels.index.is_unique
    assert predictions.index.isin(labels.index).all()
    assert len(predictions) == skill["sample_rows"] == 816
    assert len(set(predictions.index.get_level_values("datetime"))) == 272

    bars = {}
    for sym in SYMBOLS:
        data = pd.read_csv(OUT / f"openbb_cboe_{sym}_normalized.csv")
        assert data["session_date"].is_unique
        bars[sym] = data.set_index("session_date").sort_index()
    sessions = list(bars["SPY"].index)
    assert all(list(bars[s].index) == sessions for s in SYMBOLS)
    next_date = dict(zip(sessions[:-1],sessions[1:]))

    expected = {}
    chosen = Counter()
    equal_rows = []
    spy_rows = []
    shifted_mismatch = 0
    daily_dates = sorted(set(predictions.index.get_level_values("datetime")))
    for day in daily_dates:
        next_day = next_date.get(day)
        assert next_day is not None
        forecasts = {s: float(predictions.loc[(day, s)]) for s in SYMBOLS}
        assert all(math.isfinite(v) for v in forecasts.values())
        winner = min(SYMBOLS,key=lambda sym: (-forecasts[sym],sym))
        chosen[winner] += 1
        realized = {}
        for sym in SYMBOLS:
            open_next = Decimal(str(bars[sym].loc[next_day, "open"]))
            close_next = Decimal(str(bars[sym].loc[next_day, "close"]))
            ret = close_next / open_next - 1
            actual_label = float(labels.loc[(day, sym)])
            assert abs(float(ret) - actual_label) < 1e-10, (
                day, sym, "Qlib target differs from NEXT-session open/close"
            )
            realized[sym] = ret
        same_day = Decimal(str(bars["SPY"].loc[day, "close"])) / Decimal(
            str(bars["SPY"].loc[day, "open"])
        ) - 1
        shifted_mismatch += abs(float(same_day - realized["SPY"])) > 1e-6
        expected[day] = (winner, realized, next_day)
        equal_rows.append(sum(realized.values(), Decimal(0)) / 3)
        spy_rows.append(realized["SPY"])
    assert shifted_mismatch > 220, "same-day/next-session shift indistinguishable"

    def benchmark(strategy, reference, fee: str) -> dict:
        assert len(strategy) == len(reference) == len(daily_dates)
        rows = []
        for day, gross, baseline in zip(daily_dates, strategy, reference):
            rows.append({
                "periodEndAt": expected[day][2] + "T23:59:00+00:00",
                "depositAtStart": ZERO,
                "strategyGrossReturn": str(gross),
                "benchmarkGrossReturn": str(baseline),
                "strategyExpenseFractionAtStart": fee,
                "benchmarkExpenseFractionAtStart": fee,
                "strategyFixedFeeAtStart": ZERO,
                "benchmarkFixedFeeAtStart": ZERO,
            })
        result = replay_passive_benchmark(
            opening_balance=OPENING, currency="USD", periods=rows
        )
        assert result["capitalAuthority"] == "NONE"
        assert result["periodCount"] == 272
        return result

    model_returns = [expected[d][1][expected[d][0]] for d in daily_dates]
    # Intraday "daily re-entry" scenario: flat overnight, zero/illustrative
    # symmetric daily roundtrip cost, model choice from prior day's forecast.
    against_spy = benchmark(model_returns,spy_rows,ZERO)
    against_equal = benchmark(model_returns,equal_rows,ZERO)
    fee_scenario = benchmark(model_returns,spy_rows,"0.001")

    # Consumer horizon counterexample: open once then hold through all closes.
    # This is independent of Qlib scores and a different economic strategy.
    first_trade = expected[daily_dates[0]][2]
    last_trade = expected[daily_dates[-1]][2]
    assert date.fromisoformat(first_trade) < date.fromisoformat(last_trade)
    def hold_path(sym: str) -> list[Decimal]:
        ret = []
        previous_close = None
        for day in sessions[sessions.index(first_trade):sessions.index(last_trade)+1]:
            close = Decimal(str(bars[sym].loc[day, "close"]))
            base = (
                Decimal(str(bars[sym].loc[day, "open"]))
                if previous_close is None else previous_close
            )
            ret.append(close / base - 1)
            previous_close = close
        return ret

    hold_spy = hold_path("SPY")
    hold_qqq = hold_path("QQQ")
    assert len(hold_spy) == len(daily_dates)
    # The repeated passive benchmark consumer works for fixed SPY/QQQ holds.
    hold = benchmark(hold_qqq,hold_spy,ZERO)

    # Do not assume predictive skill solely from MSE or retrospective gains.
    # The proven gap is a logical horizon mismatch, not a trading P&L claim.
    result = {
        "kind":"ordivon.finance.r3.qlib-economic-consumer-counterexample",
        "standing":"RETROSPECTIVE_NON_EXECUTABLE_HYPOTHETICAL_ONLY",
        "source_model_skill":skill,
        "capital_budget_lego":"ordivon_capital.portfolio.strategic_contribution",
        "total_initial_cash_minor":1_000_000,
        "protected_cash_minor":900_000,
        "economic_comparison_investment_sleeve_minor":100_000,
        "fractional_ETF_shares_assumed":True,
        "whole_share_Paper_execution_equivalence_proven":False,
        "source_historical_pit_eligible":False,
        "source_corporate_actions_verified":False,
        "source_dividends_reinvested":False,
        "real_execution_costs_qualified":False,
        "decision_policy_admitted":False,
        "real_orders_or_accounting_effects":"NONE",
        "model_daily_prediction_horizon":"T+1 open->T+1 close",
        "actual_capital_paper_horizon":"T+1 open entry and carry across sessions",
        "model_daily_strategy_executable_by_current_paper":False,
        "candidate_sessions":len(daily_dates),
        "test_feature_dates":[daily_dates[0],daily_dates[-1]],
        "economic_trade_dates":[first_trade,last_trade],
        "model_daily_selected_assets":dict(sorted(chosen.items())),
        "wrong_same_day_label_sessions":int(shifted_mismatch),
        "model_vs_spy_intraday_zero_cost":against_spy,
        "model_vs_equal_weight_intraday_zero_cost":against_equal,
        "model_vs_spy_intraday_symmetric_10bps_cost_scenario":fee_scenario,
        "fixed_qqq_hold_vs_fixed_spy_hold_zero_cost":hold,
        "note":"No native strategy was executed here. All assets fixed retrospectively; no price basis adjustment or independent PIT.",
    }
    (OUT / "qlib_paper_horizon_economic_result.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print("R3_QLIB_PAPER_HORIZON_ECONOMIC_CONSUMER_PASS",json.dumps({
        "model_selected_assets":dict(chosen),
        "model_vs_spy_intraday_terminal_difference":against_spy["terminalWealthDifference"],
        "initial_account_cash":"10000",
        "protected_cash":"9000",
        "invested_sleeve":"1000",
        "model_vs_equal_intraday_terminal_difference":against_equal["terminalWealthDifference"],
        "model_vs_spy_intraday_fee_scenario_difference":fee_scenario["terminalWealthDifference"],
        "fixed_QQQ_vs_SPY_holding_terminal_difference":hold["terminalWealthDifference"],
        "model_Paper_consumer_eligible":False,
        "PIT":False,
    },sort_keys=True))
    return result


if __name__ == "__main__":
    run()
