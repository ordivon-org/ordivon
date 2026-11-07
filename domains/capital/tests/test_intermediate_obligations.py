"""Tests the timing of actual monthly obligations without inventing policy caps."""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ordivon_capital.portfolio.algebraic_policy import AlgebraicPolicyError
from ordivon_capital.portfolio.multistage_policy import (
    InformationNode,
    MultistageProblem,
    solve_multistage,
)


def states():
    return (
        InformationNode(
            "root", None, 0, 1, initial_margin=(.5,), turnover_cost=(0,),
        ),
        InformationNode(
            "next", "root", 1, 1, (.8,), 1.02, 1.04, (.3,),
            (.5,), (0,),
        ),
        InformationNode(
            "end", "next", 2, 1, (.8,), 1.03, 1.04, (.3,),
            terminal=True,
        ),
    )


def test_monthly_dated_payments_are_real_account_cashflows():
    result = solve_multistage(MultistageProblem(
        gamma=1, nodes=states(),
        node_outflow_after_contribution_r={"root":.2, "next":.3},
    ))
    assert result.root_cash_r == pytest.approx(.8,abs=1e-6)
    assert result.root_debt_r == pytest.approx(0,abs=1e-6)
    assert result.node_decisions_r["root"]["contributionR"] == 1
    assert result.node_decisions_r["next"]["outflowAfterContributionR"] == .3
    assert result.node_decisions_r["next"]["postTradeEquityR"] == pytest.approx(
        .8*1.02+1-.3,abs=1e-6
    )
    assert result.expected_terminal_r == pytest.approx(
        (.8*1.02+1-.3)*1.03,abs=1e-6
    )
    assert result.concavity_global_utility_gap_upper < 1e-5


def test_missing_obligations_match_zero_outflows_and_previous_model():
    nodes=states()
    a=solve_multistage(MultistageProblem(gamma=2,nodes=nodes))
    b=solve_multistage(MultistageProblem(
        gamma=2,nodes=nodes,
        node_outflow_after_contribution_r={"root":0.0,"next":0.0},
    ))
    assert a.expected_terminal_r == pytest.approx(b.expected_terminal_r,abs=1e-6)
    assert a.certainty_equivalent_terminal_r == pytest.approx(
        b.certainty_equivalent_terminal_r,abs=1e-6
    )


def test_unfunded_obligation_is_infeasible_and_unknown_dates_are_rejected():
    with pytest.raises(AlgebraicPolicyError,match="intermediate obligations"):
        solve_multistage(MultistageProblem(
            gamma=1,nodes=states(),
            node_outflow_after_contribution_r={"root":1.3,"next":0.0},
        ))
    for invalid in (
        {"root":.2},
        {"root":.2,"next":-1},
        {"root":.2,"next":math.nan},
        {"root":.2,"next":False},
        {"root":.2,"next":0.0,"future":0.0},
    ):
        with pytest.raises(AlgebraicPolicyError):
            solve_multistage(MultistageProblem(
                gamma=1,nodes=states(),
                node_outflow_after_contribution_r=invalid,
            ))


def test_native_multistage_json_readback_reports_cashflow_timing():
    payload={
        "gamma":1,
        "nodes":[
            {"id":"root","parent":None,"t":0,"conditional_probability":1,
             "initial_margin":[.5],"turnover_cost":[0]},
            {"id":"next","parent":"root","t":1,"conditional_probability":1,
             "risky_gross":[.8],"cash_gross":1.02,"debt_gross":1.04,
             "maintenance":[.3],"initial_margin":[.5],"turnover_cost":[0]},
            {"id":"end","parent":"next","t":2,"conditional_probability":1,
             "risky_gross":[.8],"cash_gross":1.03,"debt_gross":1.04,
             "maintenance":[.3],"terminal":True},
        ],
        "node_outflow_after_contribution_r":{"root":.2,"next":.3},
    }
    res=subprocess.run(
        [sys.executable,"-m","ordivon_capital.portfolio.multistage_policy",
         "--input","-"],
        input=json.dumps(payload),capture_output=True,text=True,check=True,
        env={**os.environ,"PYTHONPATH":str(Path(__file__).resolve().parents[1]/"src")},
    )
    out=json.loads(res.stdout)
    assert out["effectStanding"]=="READ_ONLY_NO_BROKER_NO_PAPER_LEDGER"
    assert out["solution"]["node_decisions_r"]["root"]["outflowAfterContributionR"]==.2
    assert out["solution"]["expected_terminal_r"]==pytest.approx(
        (.8*1.02+1-.3)*1.03,abs=1e-6
    )


def test_spent_all_cash_can_receive_future_1r() -> None:
    # A non-borrowing account can validly be zero before the next deposit.
    result = solve_multistage(MultistageProblem(
        gamma=1, nodes=states(),
        node_outflow_after_contribution_r={"root":1.0, "next":0.0},
    ))
    assert result.root_risky_r[0] == pytest.approx(0.0, abs=1e-6)
    assert result.root_cash_r == pytest.approx(0.0, abs=1e-6)
    assert result.root_debt_r == pytest.approx(0.0, abs=1e-6)
    assert result.node_decisions_r["next"]["postTradeEquityR"] == pytest.approx(
        1.0, abs=1e-6
    )
    assert result.expected_terminal_r == pytest.approx(1.03, abs=1e-6)
    assert result.concavity_global_utility_gap_upper < 1e-5
