"""Economic consumers for normalized monthly 1r nonanticipative scenario trees.

All test input numbers are synthetic finite mathematical fixtures, NOT
investment risk budgets, historical forecasts, or brokerage facts.
"""
from __future__ import annotations

import pytest

from ordivon_capital.portfolio.algebraic_policy import (
    AlgebraicPolicyError,
    OnePeriodProblem,
    Scenario,
    solve_one_period,
)
from ordivon_capital.portfolio.multistage_policy import (
    InformationNode,
    MultistageProblem,
    solve_multistage,
)


def root(*, margin: float = .4, cost: float = 0) -> InformationNode:
    return InformationNode(
        id="root", parent=None, t=0, conditional_probability=1,
        initial_margin=(margin,), turnover_cost=(cost,),
    )


def terminal(
    id: str, parent: str, t: int, probability: float, gross: float,
    *, cash: float = 1, debt: float = 1.01,
    maintenance: float = .3, label: str = "",
) -> InformationNode:
    return InformationNode(
        id=id, parent=parent, t=t, conditional_probability=probability,
        risky_gross=(gross,), cash_gross=cash, debt_gross=debt,
        maintenance=(maintenance,), terminal=True, observed_label=label,
    )


def test_one_period_is_a_special_case_of_multistage_convex_program() -> None:
    econ = OnePeriodProblem(
        gamma=1, initial_margin=(.4,), turnover_cost=(0,),
        old_weights=(0,),
        scenarios=(
            Scenario(.4, (1.8,), 1.0, 1.01, (.2,)),
            Scenario(.6, (2.0,), 1.0, 1.01, (.2,)),
        ),
    )
    original = solve_one_period(econ)
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("down", "root", 1, .4, 1.8, maintenance=.2),
            terminal("up", "root", 1, .6, 2.0, maintenance=.2),
        ),
    )
    multi = solve_multistage(tree)
    assert multi.contributions_r_per_path == 1
    assert multi.root_risky_r[0] == pytest.approx(
        original.risky_weights[0], abs=1e-5
    )
    assert multi.expected_terminal_r == pytest.approx(
        original.expected_equity, abs=1e-5
    )
    assert multi.certainty_equivalent_terminal_r == pytest.approx(
        original.certainty_equivalent, abs=1e-5
    )
    assert multi.equality_residual < 1e-7
    assert multi.inequality_residual < 1e-7
    assert multi.concavity_global_utility_gap_upper < 1e-5


def test_two_months_each_inject_exactly_one_r_not_investment_return() -> None:
    tree = MultistageProblem(
        gamma=2,
        nodes=(
            root(),
            InformationNode(
                id="month2", parent="root", t=1,
                conditional_probability=1,
                risky_gross=(.80,), cash_gross=1.05, debt_gross=1.06,
                maintenance=(.3,), initial_margin=(.4,), turnover_cost=(0,),
            ),
            terminal("end", "month2", 2, 1, .8,
                     cash=1.03, debt=1.04),
        ),
    )
    result = solve_multistage(tree)
    assert result.contributions_r_per_path == 2
    assert result.root_risky_r[0] == pytest.approx(0, abs=1e-7)
    assert result.node_decisions_r["month2"]["assetExposuresR"][0] == pytest.approx(
        0, abs=1e-7
    )
    # First 1r grows across both months; second 1r grows only one month.
    assert result.expected_terminal_r == pytest.approx(
        1.05 * 1.03 + 1.03, abs=1e-6
    )
    assert result.concavity_global_utility_gap_upper < 1e-5


def test_different_observations_allow_distinct_future_actions_not_foresight() -> None:
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(margin=.5),
            InformationNode(
                "bad", "root", 1, .5, (.95,), 1, 1.01, (.35,),
                (.5,), (0,),
            ),
            InformationNode(
                "good", "root", 1, .5, (1.05,), 1, 1.01, (.35,),
                (.5,), (0,),
            ),
            terminal("bad_low", "bad", 2, .5, .6),
            terminal("bad_high", "bad", 2, .5, .7),
            terminal("good_low", "good", 2, .5, 1.5),
            terminal("good_high", "good", 2, .5, 1.8),
        ),
    )
    result = solve_multistage(tree)
    assert result.contributions_r_per_path == 2
    assert set(result.node_decisions_r) == {"root", "bad", "good"}
    assert result.node_decisions_r["bad"]["assetExposuresR"][0] < 1e-5
    assert result.node_decisions_r["good"]["assetExposuresR"][0] > 0
    assert len(result.terminal_distribution) == 4
    assert sum(v["probability"] for v in result.terminal_distribution.values()) == pytest.approx(1)
    assert result.concavity_global_utility_gap_upper < 1e-5


def test_possible_total_loss_prevents_unsecured_positive_margin_borrowing() -> None:
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(margin=.4),
            terminal("wipeout", "root", 1, .4, 0.0,
                     cash=1.01, debt=1.05, maintenance=.6),
            terminal("rally", "root", 1, .6, 2.0,
                     cash=1.01, debt=1.05, maintenance=.3),
        ),
    )
    sol = solve_multistage(tree)
    assert sol.root_debt_r < 1e-6
    assert sol.terminal_distribution["wipeout"]["terminalR"] > 0
    assert sol.equality_residual < 1e-7


def test_probability_mass_and_hidden_information_are_economic_contracts() -> None:
    duplicated = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("hidden_A", "root", 1, .5, 1.5),
            terminal("hidden_B", "root", 1, .5, 1.5),
        ),
    )
    with pytest.raises(AlgebraicPolicyError, match="indistinguishable"):
        solve_multistage(duplicated)
    invalid_distribution = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("low", "root", 1, .25, 0.8),
            terminal("high", "root", 1, .5, 1.4),
        ),
    )
    with pytest.raises(AlgebraicPolicyError, match="sum to one"):
        solve_multistage(invalid_distribution)


def test_unequal_loan_and_deposit_rates_never_generate_free_arbitrage() -> None:
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("down", "root", 1, .5, .9, cash=1.04, debt=1.07),
            terminal("up", "root", 1, .5, 1.0, cash=1.04, debt=1.07),
        ),
    )
    result = solve_multistage(tree)
    assert result.root_cash_r == pytest.approx(1, abs=1e-6)
    assert result.root_debt_r == pytest.approx(0, abs=1e-6)
    assert result.root_risky_r[0] == pytest.approx(0, abs=1e-6)
    assert result.expected_terminal_r == pytest.approx(1.04, abs=1e-6)

def test_two_asset_joint_states_observe_only_current_branch_and_margin() -> None:
    root_node = InformationNode(
        "root", None, 0, 1, initial_margin=(.5, .5), turnover_cost=(.01, .01)
    )
    decisions = (
        InformationNode(
            "A", "root", 1, .45, (.9, 1.2), 1.01, 1.03,
            (.4, .4), (.5, .5), (.01, .01),
        ),
        InformationNode(
            "B", "root", 1, .55, (1.2, .9), 1.01, 1.03,
            (.4, .4), (.5, .5), (.01, .01),
        ),
    )
    leaves = (
        InformationNode(
            "A1", "A", 2, .3, (.95, 1.15), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
        InformationNode(
            "A2", "A", 2, .7, (1.2, 1.05), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
        InformationNode(
            "B1", "B", 2, .8, (1.05, .95), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
        InformationNode(
            "B2", "B", 2, .2, (1.3, 1.4), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
    )
    sol = solve_multistage(
        MultistageProblem(gamma=3, nodes=(root_node, *decisions, *leaves))
    )
    assert sol.contributions_r_per_path == 2
    assert len(sol.node_decisions_r) == 3
    assert len(sol.root_risky_r) == 2
    assert all(w >= 0 for w in sol.root_risky_r)
    assert sum(sol.root_risky_r) + sol.root_cash_r - sol.root_debt_r == pytest.approx(
        1 - sol.node_decisions_r["root"]["tradeCostR"], abs=1e-7
    )
    assert sum(x["probability"] for x in sol.terminal_distribution.values()) == pytest.approx(1)
    assert all(x["terminalR"] > 0 for x in sol.terminal_distribution.values())
    assert sol.equality_residual < 1e-7
    assert sol.inequality_residual < 1e-7
    assert sol.concavity_global_utility_gap_upper < 1e-5

def test_native_module_consumer_accepts_exact_json_and_no_execution_authority() -> None:
    import dataclasses
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    # Pytest adds src to sys.path via pythonpath config, but an independent
    # Runtime child process needs the same explicit native source binding.
    src = str(Path(__file__).resolve().parents[1] / "src")
    inherited = os.environ.get("PYTHONPATH")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = src + (
        os.pathsep + inherited if inherited else ""
    )
    payload = {
        "gamma": 2,
        "nodes": [
            dataclasses.asdict(root()),
            dataclasses.asdict(
                terminal(
                    "terminal", "root", 1, 1, .8,
                    cash=1.03, debt=1.04,
                )
            ),
        ],
    }
    command = [
        sys.executable,
        "-m",
        "ordivon_capital.portfolio.multistage_policy",
        "--input",
        "-",
    ]
    result = subprocess.run(
        command,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env=environment,
    )
    observed = json.loads(result.stdout)
    assert observed["inputStanding"] == "CALLER_SUPPLIED_NOT_MARKET_ATTESTED"
    assert observed["effectStanding"] == "READ_ONLY_NO_BROKER_NO_PAPER_LEDGER"
    assert observed["solution"]["contributions_r_per_path"] == 1
    assert observed["solution"]["expected_terminal_r"] == pytest.approx(
        1.03, abs=1e-6
    )
    assert observed["solution"]["root_debt_r"] < 1e-6
    missing = subprocess.run(
        command, input='{"nodes":[]}', text=True,
        capture_output=True, check=False, env=environment,
    )
    assert missing.returncode != 0
    assert "expected only gamma and nodes" in missing.stderr
